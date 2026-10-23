"""NotebookLM Backend - Pydantic Schemas"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ── Notebook Schemas ──────────────────────────────────────────────────────────


class NotebookCreate(BaseModel):
    title: str = Field(default="Untitled Notebook", max_length=255)
    description: str = Field(default="", max_length=2000)


class NotebookUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class SourceResponse(BaseModel):
    id: UUID
    notebook_id: UUID
    file_type: str
    original_name: str
    status: str
    page_count: int | None = None
    content_preview: str | None = None
    url: str | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotebookResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    source_count: int = 0
    sources: list[SourceResponse] = []

    model_config = {"from_attributes": True}


class NotebookListItem(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    source_count: int = 0

    model_config = {"from_attributes": True}


# ── Source Schemas ────────────────────────────────────────────────────────────


class SourceUploadResponse(BaseModel):
    id: UUID
    file_type: str
    original_name: str
    status: str
    message: str = "File uploaded and processing started"

    model_config = {"from_attributes": True}


class UrlAddRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)


# ── Chat Schemas ─────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources_used: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []
