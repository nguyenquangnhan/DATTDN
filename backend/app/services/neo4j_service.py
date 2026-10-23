"""NotebookLM Backend - Neo4j GraphRAG Service

Handles storage of document chunks, vector embeddings, and Knowledge Graph
(entities & relationships) in Neo4j.
"""

import json
import logging
from neo4j import GraphDatabase
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_driver = None
_gemini_client = None


def get_neo4j_driver():
    """Lazy-load the Neo4j Python driver."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
    return _driver


def get_gemini_client():
    """Lazy-load the Google GenAI client."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


# ── Pydantic Schemas for Gemini Structured Output ───────────────────────────

class ExtractedEntity(BaseModel):
    name: str
    type: str  # e.g., "Person", "Organization", "Location", "Concept", "Date"
    description: str = ""


class ExtractedRelationship(BaseModel):
    source: str
    target: str
    type: str  # e.g., "WORKS_AT", "PART_OF", "RELATED_TO"
    description: str = ""


class ExtractedKnowledgeGraph(BaseModel):
    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]


# ── Database Initialization ──────────────────────────────────────────────────

def init_neo4j():
    """Create constraints and vector indexes in Neo4j."""
    logger.info("Initializing Neo4j database...")
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Create constraint for Unique Notebook ID
        session.run("CREATE CONSTRAINT UNIQUE_NOTEBOOK_ID IF NOT EXISTS FOR (n:Notebook) REQUIRE n.id IS UNIQUE")
        # Create constraint for Unique Source ID
        session.run("CREATE CONSTRAINT UNIQUE_SOURCE_ID IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE")
        # Create constraint for Unique Chunk ID
        session.run("CREATE CONSTRAINT UNIQUE_CHUNK_ID IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE")

        # Create Vector Index for Chunk Node using db.index.vector.createNodeIndex
        try:
            result = session.run("SHOW INDEXES YIELD name")
            indexes = [row["name"] for row in result]
            if "chunk_vector_index" not in indexes:
                session.run("CALL db.index.vector.createNodeIndex('chunk_vector_index', 'Chunk', 'embedding', 768, 'cosine')")
                logger.info("Neo4j vector index 'chunk_vector_index' created.")
            else:
                logger.info("Neo4j vector index 'chunk_vector_index' already exists.")
        except Exception as e:
            logger.error(f"Error creating vector index: {e}")


# ── Ingestion ────────────────────────────────────────────────────────────────

async def save_chunks_to_neo4j(
    notebook_id: str,
    source_id: str,
    source_name: str,
    chunks: list[str],
    embeddings: list[list[float]]
):
    """Save document chunks and their embeddings into Neo4j."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Clean existing source data (idempotency)
        logger.info(f"Clearing existing graph data for source {source_id}")
        session.run(
            """
            MATCH (s:Source {id: $source_id})
            OPTIONAL MATCH (s)<-[:PART_OF]-(c:Chunk)
            DETACH DELETE s, c
            """,
            {"source_id": str(source_id)}
        )

        # Create Notebook and Source nodes
        session.run(
            """
            MERGE (n:Notebook {id: $notebook_id})
            CREATE (s:Source {id: $source_id, name: $source_name})
            CREATE (s)-[:BELONGS_TO]->(n)
            """,
            {
                "notebook_id": str(notebook_id),
                "source_id": str(source_id),
                "source_name": source_name
            }
        )

        # Bulk create Chunk nodes and links to Source
        chunks_data = [
            {
                "id": f"{source_id}_{idx}",
                "content": content,
                "index": idx,
                "embedding": emb
            }
            for idx, (content, emb) in enumerate(zip(chunks, embeddings))
        ]

        session.run(
            """
            MATCH (s:Source {id: $source_id})
            UNWIND $chunks_data AS c_data
            CREATE (c:Chunk {
                id: c_data.id,
                content: c_data.content,
                index: c_data.index,
                embedding: c_data.embedding
            })
            CREATE (c)-[:PART_OF]->(s)
            """,
            {
                "source_id": str(source_id),
                "chunks_data": chunks_data
            }
        )
    logger.info(f"Stored {len(chunks)} chunks in Neo4j for source {source_id}")


async def extract_and_save_graph(
    source_id: str,
    chunks: list[str]
):
    """Parse entities and relationships using Gemini and save to Neo4j."""
    client = get_gemini_client()
    driver = get_neo4j_driver()

    logger.info(f"Extracting Knowledge Graph from {len(chunks)} chunks for source {source_id}...")

    for idx, chunk_text in enumerate(chunks):
        chunk_id = f"{source_id}_{idx}"
        try:
            response = await client.aio.models.generate_content(
                model=settings.CHAT_MODEL,
                contents=f"Extract knowledge graph from this text chunk:\n\n{chunk_text}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedKnowledgeGraph,
                    system_instruction=(
                        "You are an expert at extracting entities and relationships to build a Knowledge Graph. "
                        "Identify the key entities (Person, Organization, Location, Concept, Event, etc.) and "
                        "the relationships between them from the provided text. Keep entity names normalized (same entity should have the same name)."
                    )
                )
            )

            if not response.text:
                continue

            graph_data = json.loads(response.text)
            entities = graph_data.get("entities", [])
            relationships = graph_data.get("relationships", [])

            with driver.session() as session:
                # 1. Create entities and connect them to the specific Chunk node
                for entity in entities:
                    entity_type = entity.get("type", "Concept").strip().replace(" ", "_")
                    if not entity_type.isalnum():
                        entity_type = "Concept"

                    session.run(
                        f"""
                        MATCH (c:Chunk {{id: $chunk_id}})
                        MERGE (e:`{entity_type}` {{name: $name}})
                        ON CREATE SET e.description = $description, e.source_id = $source_id
                        MERGE (e)-[:MENTIONED_IN]->(c)
                        """,
                        {
                            "chunk_id": chunk_id,
                            "name": entity.get("name"),
                            "description": entity.get("description", ""),
                            "source_id": str(source_id)
                        }
                    )

                # 2. Create relationships between entities
                for rel in relationships:
                    rel_type = rel.get("type", "RELATED_TO").strip().upper().replace(" ", "_")
                    if not rel_type.replace("_", "").isalnum():
                        rel_type = "RELATED_TO"

                    session.run(
                        f"""
                        MATCH (source {{name: $source_name}})
                        MATCH (target {{name: $target_name}})
                        MERGE (source)-[r:`{rel_type}`]->(target)
                        ON CREATE SET r.description = $description, r.source_id = $source_id
                        """,
                        {
                            "source_name": rel.get("source"),
                            "target_name": rel.get("target"),
                            "description": rel.get("description", ""),
                            "source_id": str(source_id)
                        }
                    )
        except Exception as e:
            logger.error(f"Error extracting graph from chunk {chunk_id}: {e}")


def delete_source_from_neo4j(source_id: str):
    """Delete all chunks, entities, and relationships related to a source from Neo4j."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Delete source-specific relationships, chunks, and the source itself
        session.run(
            """
            MATCH (s:Source {id: $source_id})
            OPTIONAL MATCH (s)<-[:PART_OF]-(c:Chunk)
            DETACH DELETE s, c
            """,
            {"source_id": str(source_id)}
        )

        # Clean up orphan relationships and entities that only belong to this source_id
        session.run(
            """
            MATCH (e)
            WHERE e.source_id = $source_id
            OPTIONAL MATCH (e)-[r]-()
            WHERE r.source_id = $source_id
            DETACH DELETE e
            """,
            {"source_id": str(source_id)}
        )

        # General clean up of any relationships created for this source_id
        session.run(
            """
            MATCH ()-[r]->()
            WHERE r.source_id = $source_id
            DELETE r
            """,
            {"source_id": str(source_id)}
        )
    logger.info(f"Deleted graph data for source {source_id} in Neo4j")


def get_notebook_graph(notebook_id: str) -> dict:
    """Retrieve entities and relationships for a notebook's Knowledge Graph visualization.

    Returns:
        dict with 'nodes' (list of entities) and 'edges' (list of relationships)
    """
    driver = get_neo4j_driver()
    nodes_map = {}  # name -> node dict
    edges = []

    with driver.session() as session:
        # Get all entities linked to chunks belonging to this notebook
        result = session.run(
            """
            MATCH (s:Source)-[:BELONGS_TO]->(n:Notebook {id: $notebook_id})
            MATCH (c:Chunk)-[:PART_OF]->(s)
            MATCH (e)-[:MENTIONED_IN]->(c)
            RETURN DISTINCT e.name AS name, labels(e) AS labels, e.description AS description
            """,
            {"notebook_id": str(notebook_id)}
        )

        for row in result:
            name = row["name"]
            if name and name not in nodes_map:
                # Filter out base labels like "Chunk", "Source", etc.
                entity_labels = [
                    l for l in row["labels"]
                    if l not in ("Chunk", "Source", "Notebook")
                ]
                entity_type = entity_labels[0] if entity_labels else "Concept"
                nodes_map[name] = {
                    "id": name,
                    "name": name,
                    "type": entity_type,
                    "description": row["description"] or "",
                }

        # Get relationships between entities
        result = session.run(
            """
            MATCH (s:Source)-[:BELONGS_TO]->(n:Notebook {id: $notebook_id})
            MATCH (c:Chunk)-[:PART_OF]->(s)
            MATCH (e1)-[:MENTIONED_IN]->(c)
            MATCH (e1)-[r]->(e2)
            WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'PART_OF' AND type(r) <> 'BELONGS_TO'
            RETURN DISTINCT e1.name AS source, type(r) AS rel_type, e2.name AS target, r.description AS description
            """,
            {"notebook_id": str(notebook_id)}
        )

        for row in result:
            source_name = row["source"]
            target_name = row["target"]
            if source_name and target_name:
                # Ensure both nodes exist in our map
                if target_name not in nodes_map:
                    nodes_map[target_name] = {
                        "id": target_name,
                        "name": target_name,
                        "type": "Concept",
                        "description": "",
                    }
                edges.append({
                    "source": source_name,
                    "target": target_name,
                    "type": row["rel_type"] or "RELATED_TO",
                    "description": row["description"] or "",
                })

    logger.info(
        f"Retrieved graph for notebook {notebook_id}: "
        f"{len(nodes_map)} nodes, {len(edges)} edges"
    )

    return {
        "nodes": list(nodes_map.values()),
        "edges": edges,
    }
