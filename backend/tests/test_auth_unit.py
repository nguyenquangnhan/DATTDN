import pytest
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

def test_password_hashing():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    email = "test@example.com"
    
    token = create_access_token(user_id=user_id, email=email)
    assert isinstance(token, str)
    assert len(token) > 0

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("email") == email

def test_invalid_jwt_token():
    invalid_token = "invalid.jwt.token"
    payload = decode_access_token(invalid_token)
    assert payload is None
