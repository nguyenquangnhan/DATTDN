"""NotebookLM Backend - User Pydantic Schemas"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


# ── Input Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Schema for registering with email + password."""
    email: EmailStr
    password: str
    full_name: Optional[str] = ""

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự")
        return v


class UserLogin(BaseModel):
    """Schema for logging in with email + password."""
    email: EmailStr
    password: str


class GoogleAuthInput(BaseModel):
    """Schema for logging in / registering via Google OAuth2 ID Token."""
    id_token: str  # Google ID Token từ phía frontend (Google Sign-In)


# ── Response Schemas ───────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public user information returned to the client."""
    id: uuid.UUID
    email: str
    full_name: Optional[str] = ""
    avatar_url: Optional[str] = None
    auth_provider: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response after successful authentication."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
