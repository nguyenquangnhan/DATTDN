"""NotebookLM Backend - Notebook Service

Business logic for managing notebooks, sources, and processing pipeline.
"""

import logging
import os
import uuid
from pathlib import Path

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.notebook import (
    Notebook,
    Source,
    ChatMessage,
    FileType,
    SourceStatus,
)
from app.services.neo4j_service import delete_source_from_neo4j
from app.services.document_processor import (
    extract_text_from_pdf,
    extract_text_from_pdf_async,
    extract_text_from_image,
    extract_text_from_image_async,
    extract_text_from_url,
    chunk_text,
)
from anyio.to_thread import run_sync
from app.services.embedding_service import embed_and_store_chunks

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Notebook CRUD ─────────────────────────────────────────────────────────────


async def create_notebook(db: AsyncSession, title: str, description: str = "", user_id=None) -> Notebook:
    """Create a new notebook."""
    notebook = Notebook(title=title, description=description, user_id=user_id)
    db.add(notebook)
    await db.commit()
    await db.refresh(notebook)
    logger.info(f"Created notebook: {notebook.id} - {title}")
    return notebook


async def get_notebooks(db: AsyncSession, user_id=None) -> list[dict]:
    """Get all notebooks with source counts, filtered by user_id."""
    stmt = (
        select(
            Notebook,
            func.count(Source.id).label("source_count"),
        )
        .outerjoin(Source)
        .group_by(Notebook.id)
        .order_by(Notebook.updated_at.desc())
    )
    if user_id is not None:
        stmt = stmt.where(Notebook.user_id == user_id)
    result = await db.execute(stmt)

    notebooks = []
    for row in result.all():
        notebook = row[0]
        notebooks.append({
            "id": notebook.id,
            "title": notebook.title,
            "description": notebook.description,
            "created_at": notebook.created_at,
            "updated_at": notebook.updated_at,
            "source_count": row[1],
        })
    return notebooks


async def get_notebook(db: AsyncSession, notebook_id: uuid.UUID) -> Notebook | None:
    """Get a notebook by ID with its sources."""
    stmt = (
        select(Notebook)
        .options(selectinload(Notebook.sources))
        .where(Notebook.id == notebook_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_notebook(
    db: AsyncSession, notebook_id: uuid.UUID, title: str | None = None, description: str | None = None
) -> Notebook | None:
    """Update a notebook's title and/or description."""
    notebook = await db.get(Notebook, notebook_id)
    if not notebook:
        return None

    if title is not None:
        notebook.title = title
    if description is not None:
        notebook.description = description

    await db.commit()
    await db.refresh(notebook)
    return notebook


async def delete_notebook(db: AsyncSession, notebook_id: uuid.UUID) -> bool:
    """Delete a notebook and all its sources/chunks/messages (cascade)."""
    notebook = await db.get(Notebook, notebook_id)
    if not notebook:
        return False

    # Clean up uploaded files
    sources = await get_sources(db, notebook_id)
    for source in sources:
        if source.filename:
            file_path = Path(settings.UPLOAD_DIR) / source.filename
            if file_path.exists():
                file_path.unlink()

    await db.delete(notebook)
    await db.commit()
    logger.info(f"Deleted notebook: {notebook_id}")
    return True


# ── Source Management ─────────────────────────────────────────────────────────


async def get_sources(db: AsyncSession, notebook_id: uuid.UUID) -> list[Source]:
    """Get all sources for a notebook."""
    stmt = (
        select(Source)
        .where(Source.notebook_id == notebook_id)
        .order_by(Source.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_source(db: AsyncSession, source_id: uuid.UUID) -> Source | None:
    """Get a single source by ID."""
    return await db.get(Source, source_id)


async def delete_source(db: AsyncSession, source_id: uuid.UUID) -> bool:
    """Delete a source and its chunks. Also remove the uploaded file."""
    source = await db.get(Source, source_id)
    if not source:
        return False

    # Remove file from disk
    if source.filename:
        file_path = Path(settings.UPLOAD_DIR) / source.filename
        if file_path.exists():
            file_path.unlink()

    # Remove from Neo4j
    delete_source_from_neo4j(str(source_id))

    await db.delete(source)
    await db.commit()
    logger.info(f"Deleted source: {source_id}")
    return True


async def delete_all_sources(db: AsyncSession, notebook_id: uuid.UUID) -> int:
    """Delete all sources for a notebook."""
    sources = await get_sources(db, notebook_id)
    count = len(sources)

    for source in sources:
        if source.filename:
            file_path = Path(settings.UPLOAD_DIR) / source.filename
            if file_path.exists():
                file_path.unlink()
        # Remove from Neo4j
        delete_source_from_neo4j(str(source.id))

    stmt = delete(Source).where(Source.notebook_id == notebook_id)
    await db.execute(stmt)
    await db.commit()
    logger.info(f"Deleted {count} sources from notebook {notebook_id}")
    return count


# ── Source Processing Pipeline ────────────────────────────────────────────────


async def process_uploaded_file(
    db: AsyncSession,
    notebook_id: uuid.UUID,
    file_path: str,
    original_name: str,
    file_type: FileType,
    source_id: uuid.UUID | None = None,
) -> Source:
    """Process an uploaded file: extract text → chunk → embed → store.

    Args:
        db: Database session
        notebook_id: The notebook to add the source to
        file_path: Path to the saved file
        original_name: Original filename
        file_type: Type of file (pdf, image)
        source_id: Optional existing source ID

    Returns:
        The created or updated Source object
    """
    # Create or retrieve source record
    if source_id:
        source = await db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
    else:
        stored_filename = Path(file_path).name
        source = Source(
            notebook_id=notebook_id,
            filename=stored_filename,
            file_type=file_type,
            original_name=original_name,
            status=SourceStatus.PROCESSING,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)

    try:
        # Extract text based on file type
        # Use async Gemini Vision (concurrent) with PaddleOCR fallback
        if file_type == FileType.PDF:
            result = await extract_text_from_pdf_async(file_path)
        elif file_type == FileType.IMAGE:
            result = await extract_text_from_image_async(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        text = result["text"]
        if not text.strip():
            source.status = SourceStatus.ERROR
            source.error_message = "No text could be extracted from this file"
            await db.commit()
            return source

        # Update source with page count
        source.page_count = result.get("page_count")

        # Chunk the text
        chunks = chunk_text(text)
        if not chunks:
            source.status = SourceStatus.ERROR
            source.error_message = "Text extraction succeeded but no chunks could be created"
            await db.commit()
            return source

        # Embed and store chunks
        await embed_and_store_chunks(db, source.id, chunks)
        await db.refresh(source)

        logger.info(
            f"Processed file '{original_name}': {len(chunks)} chunks created"
        )
        return source

    except Exception as e:
        logger.error(f"Error processing file '{original_name}': {e}")
        source.status = SourceStatus.ERROR
        source.error_message = str(e)[:500]
        await db.commit()
        return source


async def process_url_source(
    db: AsyncSession,
    notebook_id: uuid.UUID,
    url: str,
    source_id: uuid.UUID | None = None,
) -> Source:
    """Process a URL source: scrape → chunk → embed → store."""

    # Create or retrieve source record
    if source_id:
        source = await db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
    else:
        source = Source(
            notebook_id=notebook_id,
            file_type=FileType.URL,
            original_name=url,
            url=url,
            status=SourceStatus.PROCESSING,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)

    try:
        # Extract text from URL
        result = await extract_text_from_url(url)
        text = result["text"]

        if not text.strip():
            source.status = SourceStatus.ERROR
            source.error_message = "No text could be extracted from this URL"
            await db.commit()
            return source

        # Chunk the text
        chunks = chunk_text(text)
        if not chunks:
            source.status = SourceStatus.ERROR
            source.error_message = "Text extraction succeeded but no chunks could be created"
            await db.commit()
            return source

        # Embed and store chunks
        await embed_and_store_chunks(db, source.id, chunks)
        await db.refresh(source)

        logger.info(f"Processed URL '{url}': {len(chunks)} chunks created")
        return source

    except Exception as e:
        logger.error(f"Error processing URL '{url}': {e}")
        source.status = SourceStatus.ERROR
        source.error_message = str(e)[:500]
        await db.commit()
        return source


# ── Chat History ──────────────────────────────────────────────────────────────


async def get_chat_history(db: AsyncSession, notebook_id: uuid.UUID) -> list[ChatMessage]:
    """Get chat history for a notebook."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.notebook_id == notebook_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def save_chat_message(
    db: AsyncSession,
    notebook_id: uuid.UUID,
    role: str,
    content: str,
    sources_used: list | None = None,
) -> ChatMessage:
    """Save a chat message to history."""
    message = ChatMessage(
        notebook_id=notebook_id,
        role=role,
        content=content,
        sources_used=sources_used or [],
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def clear_chat_history(db: AsyncSession, notebook_id: uuid.UUID) -> int:
    """Clear all chat messages for a notebook."""
    stmt = delete(ChatMessage).where(ChatMessage.notebook_id == notebook_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
