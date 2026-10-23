"""NotebookLM Backend - Authentication Service

Handles password hashing, JWT token creation/verification,
and Google OAuth2 ID Token verification.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt as _bcrypt

import httpx
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Password hashing ───────────────────────────────────────────────────────────


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    password_bytes = plain_password.encode("utf-8")
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        return _bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ── JWT Token ──────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


# ── Database helpers ───────────────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Fetch a user by their email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Fetch a user by their UUID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_local_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str = "",
) -> User:
    """Create and persist a new local (email/password) user."""
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        auth_provider="local",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ── Google OAuth2 ──────────────────────────────────────────────────────────────

async def verify_google_id_token(id_token: str) -> Optional[dict]:
    """
    Verify a Google ID Token by calling Google's tokeninfo endpoint.
    Returns the token payload (email, name, picture, sub) or None on failure.
    """
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Google tokeninfo rejected: {resp.text}")
                return None
            data = resp.json()

        # Verify audience matches our CLIENT_ID (if configured)
        if settings.GOOGLE_CLIENT_ID and data.get("aud") != settings.GOOGLE_CLIENT_ID:
            logger.warning("Google token audience mismatch")
            return None

        return data
    except Exception as e:
        logger.error(f"Error verifying Google token: {e}")
        return None


async def get_or_create_google_user(db: AsyncSession, google_payload: dict) -> User:
    """
    Find existing user by Google ID or email, otherwise create a new one.
    Returns the user object.
    """
    google_id = google_payload.get("sub")
    email = google_payload.get("email", "")
    full_name = google_payload.get("name", "")
    avatar_url = google_payload.get("picture")

    # 1. Try find by google_id
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user:
        return user

    # 2. Try find by email (user might have registered with email before)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Link google_id to existing account
        user.google_id = google_id
        user.avatar_url = avatar_url or user.avatar_url
        user.auth_provider = "google"
        await db.commit()
        await db.refresh(user)
        return user

    # 3. Create new user
    user = User(
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        auth_provider="google",
        google_id=google_id,
        hashed_password=None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
