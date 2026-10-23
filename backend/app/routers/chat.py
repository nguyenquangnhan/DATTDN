"""NotebookLM Backend - Chat Router

Chat endpoints with RAG-powered responses and streaming support.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.notebook import ChatRequest, ChatMessageResponse, ChatResponse
from app.services.notebook_service import (
    get_notebook,
    get_chat_history,
    save_chat_message,
    clear_chat_history,
)
from app.services.rag_service import generate_rag_response, generate_rag_response_stream

router = APIRouter(prefix="/api/notebooks/{notebook_id}/chat", tags=["chat"])


@router.post("")
async def chat_endpoint(
    notebook_id: UUID,
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get a streaming RAG response.

    Uses Server-Sent Events (SSE) for streaming.
    Each event contains JSON with:
    - type: "content" | "sources" | "done"
    - content: text chunk (for "content" type)
    - sources: list of source references (for "sources" type)
    """
    # Verify notebook exists
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Save user message
    await save_chat_message(db, notebook_id, "user", data.message)

    # Get chat history for context
    history = await get_chat_history(db, notebook_id)
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history[-10:]  # Last 10 messages for context
    ]

    # Generate streaming response
    async def event_stream():
        full_response = ""
        sources_used = []

        async for chunk in generate_rag_response_stream(
            db, notebook_id, data.message, chat_history
        ):
            yield chunk
            # Parse the chunk to collect full response
            try:
                # Remove "data: " prefix and parse JSON
                json_str = chunk.strip().replace("data: ", "")
                if json_str:
                    parsed = json.loads(json_str)
                    if parsed.get("type") == "done":
                        full_response = parsed.get("full_response", "")
                    elif parsed.get("type") == "sources":
                        sources_used = parsed.get("sources", [])
            except (json.JSONDecodeError, KeyError):
                pass

        # Save assistant response to chat history
        if full_response:
            await save_chat_message(
                db, notebook_id, "assistant", full_response, sources_used
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sync", response_model=ChatResponse)
async def chat_sync_endpoint(
    notebook_id: UUID,
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get a non-streaming RAG response.

    Alternative to the streaming endpoint for simpler clients.
    """
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Save user message
    await save_chat_message(db, notebook_id, "user", data.message)

    # Get chat history
    history = await get_chat_history(db, notebook_id)
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history[-10:]
    ]

    # Generate response
    result = await generate_rag_response(db, notebook_id, data.message, chat_history)

    # Save assistant response
    await save_chat_message(
        db, notebook_id, "assistant", result["answer"], result["sources"]
    )

    return ChatResponse(answer=result["answer"], sources=result["sources"])


@router.get("/history", response_model=list[ChatMessageResponse])
async def get_history_endpoint(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chat history for a notebook."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    messages = await get_chat_history(db, notebook_id)
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.delete("/history")
async def clear_history_endpoint(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear chat history for a notebook."""
    notebook = await get_notebook(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    count = await clear_chat_history(db, notebook_id)
    return {"message": f"Cleared {count} messages"}
