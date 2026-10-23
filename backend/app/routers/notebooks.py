"""NotebookLM Backend - Notebook Router

CRUD endpoints for managing notebooks.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.notebook import (
    NotebookCreate,
    NotebookUpdate,
    NotebookResponse,
    NotebookListItem,
    SourceResponse,
)
from app.services.notebook_service import (
    create_notebook,
    get_notebooks,
    get_notebook,
    update_notebook,
    delete_notebook,
)

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


@router.post("", response_model=NotebookResponse, status_code=201)
async def create_notebook_endpoint(
    data: NotebookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new notebook for the current user."""
    notebook = await create_notebook(
        db, title=data.title, description=data.description, user_id=current_user.id
    )
    return NotebookResponse(
        id=notebook.id,
        title=notebook.title,
        description=notebook.description,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at,
        source_count=0,
        sources=[],
    )


@router.get("", response_model=list[NotebookListItem])
async def list_notebooks_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all notebooks belonging to the current user."""
    notebooks = await get_notebooks(db, user_id=current_user.id)
    return [NotebookListItem(**n) for n in notebooks]


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook_endpoint(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a notebook by ID with its sources (must belong to current user)."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập notebook này")

    return NotebookResponse(
        id=notebook.id,
        title=notebook.title,
        description=notebook.description,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at,
        source_count=len(notebook.sources),
        sources=[SourceResponse.model_validate(s) for s in notebook.sources],
    )


@router.put("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook_endpoint(
    notebook_id: UUID,
    data: NotebookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a notebook's title or description (must belong to current user)."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa notebook này")

    notebook = await update_notebook(
        db, notebook_id, title=data.title, description=data.description
    )

    return NotebookResponse(
        id=notebook.id,
        title=notebook.title,
        description=notebook.description,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at,
        source_count=0,
        sources=[],
    )


@router.delete("/{notebook_id}")
async def delete_notebook_endpoint(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a notebook and all its data (must belong to current user)."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id and notebook.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa notebook này")

    success = await delete_notebook(db, notebook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return {"message": "Notebook deleted successfully"}
