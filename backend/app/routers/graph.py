"""NotebookLM Backend - Knowledge Graph Router

Endpoint for retrieving Knowledge Graph data for visualization.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.notebook_service import get_notebook
from app.services.neo4j_service import get_notebook_graph

router = APIRouter(prefix="/api/notebooks/{notebook_id}/graph", tags=["graph"])


@router.get("")
async def get_graph_endpoint(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Knowledge Graph data for a notebook.

    Returns nodes (entities) and edges (relationships) for visualization.
    """
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    graph_data = get_notebook_graph(str(notebook_id))
    return graph_data
