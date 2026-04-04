"""Expose authentication endpoints for token issuance."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    create_access_token,
    get_jwt_expire_minutes,
    get_users_registry,
    pwd_context,
)
from src.api.schemas.auth import TokenRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def issue_access_token(payload: TokenRequest) -> TokenResponse:
    """Authenticate credentials and issue a bearer token.

    Args:
        payload: Username and password request payload.

    Returns:
        Signed JWT response with role and expiration metadata.

    Raises:
        HTTPException: If username or password is invalid.
    """

    users_registry = get_users_registry()
    user_entry = users_registry.get(payload.username)

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user_entry is None:
        raise invalid_credentials

    password_hash = user_entry.get("password_hash")
    if not isinstance(password_hash, str) or not pwd_context.verify(payload.password, password_hash):
        raise invalid_credentials

    role = user_entry["role"]
    token = create_access_token(username=payload.username, role=role)
    return TokenResponse(
        access_token=token,
        role=role,
        expires_in=get_jwt_expire_minutes() * 60,
    )
