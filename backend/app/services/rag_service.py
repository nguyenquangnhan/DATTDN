"""NotebookLM Backend - RAG Service

Retrieval-Augmented Generation service using Neo4j for semantic vector search
and Knowledge Graph context, and Google Gemini for chat completions.
"""

import json
import logging
from uuid import UUID
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.services.embedding_service import embed_query
from app.services.neo4j_service import get_neo4j_driver

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy-load chat model
_chat_model = None


def _get_chat_model():
    """Lazy-load the Gemini chat model."""
    global _chat_model
    if _chat_model is None:
        _chat_model = ChatGoogleGenerativeAI(
            model=settings.CHAT_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
            max_output_tokens=4096,
        )
    return _chat_model


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided source documents and knowledge graph.

Instructions:
- Answer ONLY based on the provided context (document chunks and knowledge graph).
- If the context doesn't contain enough information to answer, say so clearly.
- Cite the source by mentioning the document name when referencing information.
- Be concise but thorough in your answers.
- Use markdown formatting for better readability.
- If asked about something not in the sources, politely redirect to what's available.

Context from uploaded documents:
{context}

{graph_context}
"""


# ── Semantic Search & Graph Traversal ──────────────────────────────────────────

async def search_similar_chunks(
    db: AsyncSession,
    notebook_id: UUID,
    query: str,
    top_k: int = None,
) -> list[dict]:
    """Search for the most similar document chunks using Neo4j vector index.

    Args:
        db: Database session (unused but kept for API compatibility)
        notebook_id: Filter chunks by notebook
        query: The search query
        top_k: Number of results to return

    Returns:
        List of dicts with chunk content, source info, and similarity score
    """
    top_k = top_k or settings.RAG_TOP_K

    # Embed the query
    query_embedding = await embed_query(query)

    driver = get_neo4j_driver()
    chunks = []

    with driver.session() as session:
        # Cypher query querying the vector index and filtering by notebook_id
        result = session.run(
            """
            CALL db.index.vector.queryNodes('chunk_vector_index', $top_k, $query_vector)
            YIELD node, score
            MATCH (node)-[:PART_OF]->(s:Source)-[:BELONGS_TO]->(n:Notebook {id: $notebook_id})
            RETURN 
                node.id AS id,
                node.content AS content,
                node.index AS chunk_index,
                s.id AS source_id,
                s.name AS source_name,
                score AS similarity
            """,
            {
                "notebook_id": str(notebook_id),
                "query_vector": query_embedding,
                "top_k": top_k
            }
        )

        for row in result:
            chunks.append({
                "id": row["id"],
                "content": row["content"],
                "chunk_index": row["chunk_index"],
                "source_id": str(row["source_id"]),
                "source_name": row["source_name"],
                "source_type": "pdf",  # Default placeholder or parsed from filename extension
                "similarity": float(row["similarity"]),
            })

    logger.info(
        f"Found {len(chunks)} similar chunks in Neo4j for query in notebook {notebook_id}"
    )
    return chunks


def get_graph_context(chunk_ids: list[str]) -> str:
    """Retrieve entities and relations linked to the retrieved chunks for structural context."""
    if not chunk_ids:
        return ""

    driver = get_neo4j_driver()
    relations = []

    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Chunk) WHERE c.id IN $chunk_ids
            MATCH (e)-[:MENTIONED_IN]->(c)
            OPTIONAL MATCH (e)-[r]->(target)
            RETURN e.name AS entity_name, type(r) AS rel_type, target.name AS target_name
            LIMIT 25
            """,
            {"chunk_ids": chunk_ids}
        )

        for row in result:
            if row["rel_type"] and row["target_name"]:
                relations.append(f"- ({row['entity_name']}) -[{row['rel_type']}]-> ({row['target_name']})")
            else:
                relations.append(f"- Entity: {row['entity_name']}")

    if relations:
        return "Knowledge Graph Relationships:\n" + "\n".join(relations)
    return ""


# ── RAG Chat ──────────────────────────────────────────────────────────────────

async def generate_rag_response(
    db: AsyncSession,
    notebook_id: UUID,
    user_message: str,
    chat_history: list[dict] | None = None,
) -> dict:
    """Generate a RAG response: search → build context → call LLM.

    Args:
        db: Database session
        notebook_id: The notebook to search in
        user_message: The user's question
        chat_history: Optional previous chat messages

    Returns:
        dict with answer and sources
    """
    # 1. Search for relevant chunks
    relevant_chunks = await search_similar_chunks(db, notebook_id, user_message)

    if not relevant_chunks:
        return {
            "answer": "Tôi không tìm thấy thông tin liên quan trong các tài liệu đã upload. "
                      "Hãy thử upload thêm tài liệu hoặc đặt câu hỏi khác.",
            "sources": [],
        }

    # 2. Build context and graph context
    context_parts = []
    sources_used = []
    seen_sources = set()
    chunk_ids = []

    for chunk in relevant_chunks:
        chunk_ids.append(chunk["id"])
        source_label = f"[{chunk['source_name']}]"
        context_parts.append(f"{source_label}:\n{chunk['content']}")

        if chunk["source_id"] not in seen_sources:
            seen_sources.add(chunk["source_id"])
            sources_used.append({
                "source_id": chunk["source_id"],
                "source_name": chunk["source_name"],
                "source_type": chunk["source_type"],
                "similarity": chunk["similarity"],
            })

    context = "\n\n---\n\n".join(context_parts)
    graph_context = get_graph_context(chunk_ids)

    # 3. Build messages for LLM
    system_content = SYSTEM_PROMPT.format(context=context, graph_context=graph_context)
    messages = [("system", system_content)]

    # Add chat history if available (last 6 messages for context)
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append((msg["role"], msg["content"]))

    messages.append(("human", user_message))

    # 4. Call Gemini
    chat_model = _get_chat_model()
    response = await chat_model.ainvoke(messages)

    return {
        "answer": response.content,
        "sources": sources_used,
    }


async def generate_rag_response_stream(
    db: AsyncSession,
    notebook_id: UUID,
    user_message: str,
    chat_history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Generate a streaming RAG response using Server-Sent Events format.

    Yields SSE-formatted strings with either content chunks or source info.
    """
    # 1. Search for relevant chunks
    relevant_chunks = await search_similar_chunks(db, notebook_id, user_message)

    if not relevant_chunks:
        yield f"data: {json.dumps({'type': 'content', 'content': 'Tôi không tìm thấy thông tin liên quan trong các tài liệu đã upload. Hãy thử upload thêm tài liệu hoặc đặt câu hỏi khác.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # 2. Build context
    context_parts = []
    sources_used = []
    seen_sources = set()
    chunk_ids = []

    for chunk in relevant_chunks:
        chunk_ids.append(chunk["id"])
        source_label = f"[{chunk['source_name']}]"
        context_parts.append(f"{source_label}:\n{chunk['content']}")

        if chunk["source_id"] not in seen_sources:
            seen_sources.add(chunk["source_id"])
            sources_used.append({
                "source_id": chunk["source_id"],
                "source_name": chunk["source_name"],
                "source_type": chunk["source_type"],
                "similarity": chunk["similarity"],
            })

    context = "\n\n---\n\n".join(context_parts)
    graph_context = get_graph_context(chunk_ids)

    # 3. Build messages
    system_content = SYSTEM_PROMPT.format(context=context, graph_context=graph_context)
    messages = [("system", system_content)]

    if chat_history:
        for msg in chat_history[-6:]:
            messages.append((msg["role"], msg["content"]))

    messages.append(("human", user_message))

    # 4. Stream response
    chat_model = _get_chat_model()
    full_response = ""

    async for chunk in chat_model.astream(messages):
        if chunk.content:
            full_response += chunk.content
            yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"

    # 5. Send sources info
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources_used})}\n\n"
    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"
