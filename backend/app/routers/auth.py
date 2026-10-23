"""NotebookLM Backend - Authentication Router

Endpoints:
  POST /api/auth/register  - Register with email + password
  POST /api/auth/login     - Login with email + password → JWT token
  POST /api/auth/google    - Login / Register via Google ID Token → JWT token
  GET  /api/auth/me        - Get current user info (requires token)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, GoogleAuthInput, UserResponse, TokenResponse
from app.services.auth_service import (
    get_user_by_email,
    get_user_by_id,
    create_local_user,
    verify_password,
    create_access_token,
    decode_access_token,
    verify_google_id_token,
    get_or_create_google_user,
)
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


# ── Dependency: get current authenticated user ─────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the Bearer JWT token.
    Also supports ?token=<jwt> query parameter as fallback (for file preview).
    Raises HTTP 401 if the token is missing, invalid, or expired.
    """
    # Prefer Bearer header, fallback to query param
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy token xác thực",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(db, payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị vô hiệu hóa",
        )

    return user


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new account with email and password."""
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được sử dụng. Vui lòng đăng nhập hoặc dùng email khác.",
        )

    user = await create_local_user(db, body.email, body.password, body.full_name or "")
    token = create_access_token(str(user.id), user.email)

    logger.info(f"New user registered: {user.email}")
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password. Returns a JWT access token."""
    user = await get_user_by_email(db, body.email)

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
        )

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa",
        )

    token = create_access_token(str(user.id), user.email)
    logger.info(f"User logged in: {user.email}")
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthInput, db: AsyncSession = Depends(get_db)):
    """Login or register via Google ID Token (from Google Sign-In frontend SDK)."""
    google_payload = await verify_google_id_token(body.id_token)

    if not google_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token không hợp lệ. Vui lòng thử lại.",
        )

    if not google_payload.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email Google chưa được xác minh.",
        )

    user = await get_or_create_google_user(db, google_payload)
    token = create_access_token(str(user.id), user.email)

    logger.info(f"Google auth successful: {user.email}")
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
