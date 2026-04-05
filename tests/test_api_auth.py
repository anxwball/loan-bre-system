"""Validate authentication behavior for the Phase 4c API layer."""

from __future__ import annotations

import json
from secrets import token_urlsafe

from fastapi.testclient import TestClient
from passlib.context import CryptContext

from src.api.main import create_app
from src.api.schemas.auth import TokenRequest


def _build_users_payload(admin_secret: str, analyst_secret: str) -> str:
    """Create USERS env JSON using runtime-generated test secrets."""

    context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return json.dumps(
        {
            "admin": {
                "password_hash": context.hash(admin_secret),
                "role": "admin",
            },
            "analyst": {
                "password_hash": context.hash(analyst_secret),
                "role": "analyst",
            },
        }
    )


def _build_client(monkeypatch, tmp_path, admin_secret: str, analyst_secret: str) -> TestClient:
    """Build test client with isolated API environment configuration."""

    monkeypatch.setenv("JWT_SECRET_KEY", token_urlsafe(32))
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("USERS", _build_users_payload(admin_secret, analyst_secret))
    monkeypatch.setenv("LOAN_BRE_DATABASE_URL", f"sqlite:///{(tmp_path / 'api_auth.db').as_posix()}")

    app = create_app()
    return TestClient(app)


def test_auth_token_issued_for_valid_credentials(monkeypatch, tmp_path) -> None:
    """Return bearer token payload when credentials are valid."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with _build_client(monkeypatch, tmp_path, admin_secret, analyst_secret) as client:
        response = client.post(
            "/auth/token",
            json=TokenRequest(username="admin", password=admin_secret).model_dump(),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["role"] == "admin"
    assert isinstance(payload["access_token"], str)
    assert payload["expires_in"] == 3600


def test_auth_token_rejected_for_invalid_password(monkeypatch, tmp_path) -> None:
    """Reject invalid credential combinations with HTTP 401."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)
    invalid_secret = token_urlsafe(24)

    with _build_client(monkeypatch, tmp_path, admin_secret, analyst_secret) as client:
        response = client.post(
            "/auth/token",
            json=TokenRequest(username="admin", password=invalid_secret).model_dump(),
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."
