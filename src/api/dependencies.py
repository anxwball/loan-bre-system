"""Provide shared FastAPI dependencies for DB access and JWT role guards."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, Generator

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt as pyjwt
from jwt import PyJWTError
from passlib.context import CryptContext
from sqlalchemy import Connection

from src.db.database import begin_connection, create_db_engine, dispose_engine

load_dotenv()

JWT_ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db() -> Generator[Connection, None, None]:
    """Yield one transactional SQL connection for the active request.

    Returns:
        Generator yielding a transactional SQLAlchemy Core connection.
    """

    engine = create_db_engine()
    try:
        with begin_connection(engine) as connection:
            yield connection
    finally:
        dispose_engine(engine)


def get_jwt_secret_key() -> str:
    """Return JWT signing key from environment configuration.

    Returns:
        HS256 signing secret.

    Raises:
        HTTPException: If JWT secret is not configured.
    """

    secret = os.getenv("JWT_SECRET_KEY")
    if secret is None or not secret.strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret key is not configured.",
        )

    return secret


def get_jwt_expire_minutes() -> int:
    """Resolve token expiration window in minutes.

    Returns:
        Positive token expiration in minutes, defaulting to 60.
    """

    raw_value = os.getenv("JWT_EXPIRE_MINUTES", "60")
    try:
        value = int(raw_value)
    except ValueError:
        return 60

    return value if value > 0 else 60


def get_users_registry() -> dict[str, dict[str, str]]:
    """Load and validate USERS registry from environment JSON.

    Returns:
        Dictionary keyed by username with password_hash and role entries.

    Raises:
        HTTPException: If USERS payload is missing or invalid.
    """

    raw_users = os.getenv("USERS", "{}")
    try:
        decoded = json.loads(raw_users)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="USERS environment variable is not valid JSON.",
        ) from exc

    if not isinstance(decoded, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="USERS environment variable must be a JSON object.",
        )

    registry: dict[str, dict[str, str]] = {}
    for username, entry in decoded.items():
        if not isinstance(username, str) or not isinstance(entry, dict):
            continue

        password_hash = entry.get("password_hash")
        role = entry.get("role")
        if not isinstance(password_hash, str) or role not in {"admin", "analyst"}:
            continue

        registry[username] = {
            "password_hash": password_hash,
            "role": role,
        }

    return registry


def create_access_token(username: str, role: str) -> str:
    """Create an HS256 JWT token for an authenticated user.

    Args:
        username: Subject username.
        role: Authorization role claim.

    Returns:
        Encoded JWT token string.
    """

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=get_jwt_expire_minutes())
    payload = {
        "sub": username,
        "role": role,
        "exp": expires_at,
    }

    return pyjwt.encode(payload, get_jwt_secret_key(), algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, str]:
    """Decode and validate bearer token for downstream role checks.

    Args:
        token: JWT token from OAuth2 Bearer Authorization header.

    Returns:
        Dictionary containing username and role for current request.

    Raises:
        HTTPException: If token is invalid or credentials are not authorized.
    """

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload: dict[str, Any] = pyjwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except PyJWTError as exc:
        raise unauthorized from exc

    exp_value = payload.get("exp")
    try:
        exp_timestamp = int(exp_value)
    except (TypeError, ValueError):
        raise unauthorized

    now_timestamp = int(datetime.now(timezone.utc).timestamp())
    if exp_timestamp <= now_timestamp:
        raise unauthorized

    username = payload.get("sub")
    role = payload.get("role")
    if not isinstance(username, str) or role not in {"admin", "analyst"}:
        raise unauthorized

    user_entry = get_users_registry().get(username)
    if user_entry is None or user_entry.get("role") != role:
        raise unauthorized

    return {"username": username, "role": role}


def require_admin(user: dict[str, str] = Depends(get_current_user)) -> dict[str, str]:
    """Allow only admin role.

    Args:
        user: Authenticated user payload from JWT dependency.

    Returns:
        The same user payload when authorized.

    Raises:
        HTTPException: If user role is not admin.
    """

    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role is required.",
        )

    return user


def require_analyst(user: dict[str, str] = Depends(get_current_user)) -> dict[str, str]:
    """Allow analyst and admin roles for analyst-level endpoints.

    Args:
        user: Authenticated user payload from JWT dependency.

    Returns:
        The same user payload when authorized.

    Raises:
        HTTPException: If role is outside analyst/admin set.
    """

    if user.get("role") not in {"analyst", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or admin role is required.",
        )

    return user
