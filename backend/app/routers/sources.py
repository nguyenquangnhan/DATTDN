"""NotebookLM Backend - Sources Router

Endpoints for uploading, managing, and deleting document sources.
"""

import os
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, async_session
from app.models.notebook import FileType, Source, SourceStatus
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.notebook import SourceResponse, SourceUploadResponse, UrlAddRequest
from app.services.notebook_service import (
    get_notebook,
    get_sources,
    get_source,
    delete_source,
    delete_all_sources,
    process_uploaded_file,
    process_url_source,
)

router = APIRouter(prefix="/api/notebooks/{notebook_id}/sources", tags=["sources"])
settings = get_settings()

# Supported file extensions
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
SUPPORTED_EXTENSIONS = SUPPORTED_PDF_EXTENSIONS | SUPPORTED_IMAGE_EXTENSIONS


def _get_file_type(filename: str) -> FileType:
    """Determine file type from extension."""
    ext = Path(filename).suffix.lower()
    if ext in SUPPORTED_PDF_EXTENSIONS:
        return FileType.PDF
    elif ext in SUPPORTED_IMAGE_EXTENSIONS:
        return FileType.IMAGE
    else:
        raise ValueError(f"Unsupported file type: {ext}")


async def _process_file_background(
    source_id: UUID,
    notebook_id: UUID,
    file_path: str,
    original_name: str,
    file_type: FileType,
):
    """Background task to process an uploaded file."""
    async with async_session() as db:
        await process_uploaded_file(db, notebook_id, file_path, original_name, file_type, source_id=source_id)


async def _process_url_background(
    source_id: UUID,
    notebook_id: UUID,
    url: str,
):
    """Background task to process a URL."""
    async with async_session() as db:
        await process_url_source(db, notebook_id, url, source_id=source_id)


@router.post("/upload", response_model=SourceUploadResponse, status_code=201)
async def upload_source(
    notebook_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file (PDF or image) as a source document."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập notebook này")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    file_type = _get_file_type(file.filename)

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4()}{ext}"
    file_path = upload_dir / stored_filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    source = Source(
        notebook_id=notebook_id,
        filename=stored_filename,
        file_type=file_type,
        original_name=file.filename,
        status=SourceStatus.PROCESSING,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    background_tasks.add_task(
        _process_file_background,
        source.id,
        notebook_id,
        str(file_path),
        file.filename,
        file_type,
    )

    return SourceUploadResponse(
        id=source.id,
        file_type=source.file_type.value,
        original_name=source.original_name,
        status=source.status.value,
        message=f"File '{file.filename}' uploaded successfully and processing in the background",
    )


@router.post("/url", response_model=SourceUploadResponse, status_code=201)
async def add_url_source(
    notebook_id: UUID,
    data: UrlAddRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a URL as a source document."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập notebook này")

    source = Source(
        notebook_id=notebook_id,
        file_type=FileType.URL,
        original_name=data.url,
        url=data.url,
        status=SourceStatus.PROCESSING,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    background_tasks.add_task(
        _process_url_background,
        source.id,
        notebook_id,
        data.url,
    )

    return SourceUploadResponse(
        id=source.id,
        file_type=source.file_type.value,
        original_name=source.original_name,
        status=source.status.value,
        message=f"URL '{data.url}' added successfully and processing in the background",
    )


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all sources for a notebook."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập notebook này")

    sources = await get_sources(db, notebook_id)
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source_endpoint(
    notebook_id: UUID,
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific source."""
    source = await get_source(db, source_id)
    if not source or source.notebook_id != notebook_id:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.model_validate(source)


@router.delete("/{source_id}")
async def delete_source_endpoint(
    notebook_id: UUID,
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific source."""
    source = await get_source(db, source_id)
    if not source or source.notebook_id != notebook_id:
        raise HTTPException(status_code=404, detail="Source not found")

    await delete_source(db, source_id)
    return {"message": "Source deleted successfully"}


@router.delete("")
async def delete_all_sources_endpoint(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all sources for a notebook."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa notebook này")

    count = await delete_all_sources(db, notebook_id)
    return {"message": f"Deleted {count} sources"}


# ── File content type mapping ─────────────────────────────────────────────────

CONTENT_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
}


@router.get("/{source_id}/file")
async def get_source_file(
    notebook_id: UUID,
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve the original uploaded file for preview/download.

    - For PDF/image sources: returns the file directly.
    - For URL sources: redirects to the original URL.
    """
    source = await get_source(db, source_id)
    if not source or source.notebook_id != notebook_id:
        raise HTTPException(status_code=404, detail="Source not found")

    # Check ownership
    notebook = await get_notebook(db, notebook_id)
    if notebook and notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập file này")

    # URL sources → redirect to original URL
    if source.file_type == FileType.URL:
        if not source.url:
            raise HTTPException(status_code=404, detail="URL not available")
        return RedirectResponse(url=source.url)

    # File sources → serve the file
    if not source.filename:
        raise HTTPException(status_code=404, detail="File not available")

    file_path = Path(settings.UPLOAD_DIR) / source.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    ext = file_path.suffix.lower()
    media_type = CONTENT_TYPE_MAP.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=source.original_name,
        headers={"Content-Disposition": f"inline; filename=\"{source.original_name}\""},
    )

