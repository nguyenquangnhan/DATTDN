"""NotebookLM Backend - SQLAlchemy Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
    ForeignKey,
    JSON,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


import enum


class FileType(str, enum.Enum):
    PDF = "pdf"
    IMAGE = "image"
    URL = "url"


class SourceStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Notebook(Base):
    """A notebook containing sources and chat history."""

    __tablename__ = "notebooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title = Column(String(255), nullable=False, default="Untitled Notebook")
    description = Column(Text, nullable=True, default="")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = relationship("User", back_populates="notebooks")
    sources = relationship(
        "Source", back_populates="notebook", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatMessage", back_populates="notebook", cascade="all, delete-orphan"
    )


class Source(Base):
    """A source document (PDF, image, URL) within a notebook."""

    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notebook_id = Column(
        UUID(as_uuid=True), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String(500), nullable=True)  # stored filename on disk
    file_type = Column(SAEnum(FileType), nullable=False)
    original_name = Column(String(500), nullable=False)  # original filename or URL
    status = Column(
        SAEnum(SourceStatus), nullable=False, default=SourceStatus.PROCESSING
    )
    page_count = Column(Integer, nullable=True)
    content_preview = Column(Text, nullable=True)  # first 200 chars of extracted text
    url = Column(Text, nullable=True)  # for URL sources
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    notebook = relationship("Notebook", back_populates="sources")


class ChatMessage(Base):
    """A chat message within a notebook conversation."""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notebook_id = Column(
        UUID(as_uuid=True), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources_used = Column(JSON, nullable=True, default=list)  # list of source_ids
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    notebook = relationship("Notebook", back_populates="chat_messages")
