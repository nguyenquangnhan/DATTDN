"""NotebookLM Backend - Embedding Service

Uses Google Gemini Embeddings to embed text chunks and store them in Neo4j.
Also triggers Knowledge Graph extraction.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import get_settings
from app.models.notebook import Source, SourceStatus
from app.services.neo4j_service import save_chunks_to_neo4j, extract_and_save_graph

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy-load embeddings model
_embeddings_model = None


def _get_embeddings():
    """Lazy-load the Gemini embeddings model."""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            output_dimensionality=768,
        )
    return _embeddings_model


async def embed_and_store_chunks(
    db: AsyncSession,
    source_id: UUID,
    chunks: list[str],
) -> int:
    """Embed text chunks using Gemini and store them in Neo4j (along with Knowledge Graph).

    Args:
        db: Database session
        source_id: The source document ID
        chunks: List of text chunks to embed

    Returns:
        Number of chunks successfully embedded
    """
    if not chunks:
        logger.warning(f"No chunks to embed for source {source_id}")
        return 0

    try:
        # Retrieve source from postgres to get notebook_id and original_name
        source = await db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found in database")

        embeddings_model = _get_embeddings()

        # Batch embed all chunks
        logger.info(f"Embedding {len(chunks)} chunks for source {source_id}")
        vectors = await embeddings_model.aembed_documents(chunks)

        # Store chunks with embeddings in Neo4j
        await save_chunks_to_neo4j(
            notebook_id=str(source.notebook_id),
            source_id=str(source_id),
            source_name=source.original_name,
            chunks=chunks,
            embeddings=vectors,
        )

        # Extract entities and relationships and save to Neo4j
        await extract_and_save_graph(str(source_id), chunks)

        # Update source status in postgres to ready
        source.status = SourceStatus.READY
        source.content_preview = chunks[0][:200] if chunks else None
        await db.commit()

        logger.info(f"Successfully stored {len(chunks)} chunks and graph data for source {source_id}")
        return len(chunks)

    except Exception as e:
        logger.error(f"Error embedding chunks/graph for source {source_id}: {e}")
        # Update source status to error
        source = await db.get(Source, source_id)
        if source:
            source.status = SourceStatus.ERROR
            source.error_message = str(e)[:500]
            await db.commit()
        raise


async def embed_query(query: str) -> list[float]:
    """Embed a single query string for similarity search.

    Args:
        query: The search query

    Returns:
        Embedding vector
    """
    embeddings_model = _get_embeddings()
    return await embeddings_model.aembed_query(query)
