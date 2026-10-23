"""NotebookLM Backend - User Model"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """A registered user of the application."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable cho Google OAuth
    full_name = Column(String(255), nullable=True, default="")
    avatar_url = Column(Text, nullable=True)
    auth_provider = Column(String(20), nullable=False, default="local")  # "local" | "google"
    google_id = Column(String(255), nullable=True, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
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
    notebooks = relationship(
        "Notebook", back_populates="owner", cascade="all, delete-orphan"
    )
