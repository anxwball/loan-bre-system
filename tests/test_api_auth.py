"""Validate authentication behavior for the Phase 4c API layer."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from passlib.context import CryptContext

from src.api.main import create_app


def _build_users_payload() -> str:
    """Create USERS env JSON with hashed passwords for test identities."""

    context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return json.dumps(
        {
            "admin": {
                "password_hash": context.hash("secret"),
                "role": "admin",
            },
            "analyst": {
                "password_hash": context.hash("analyst"),
                "role": "analyst",
            },
        }
    )


def _build_client(monkeypatch, tmp_path) -> TestClient:
    """Build test client with isolated API environment configuration."""

    monkeypatch.setenv("JWT_SECRET_KEY", "phase4c-test-secret")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("USERS", _build_users_payload())
    monkeypatch.setenv("LOAN_BRE_DATABASE_URL", f"sqlite:///{(tmp_path / 'api_auth.db').as_posix()}")

    app = create_app()
    return TestClient(app)


def test_auth_token_issued_for_valid_credentials(monkeypatch, tmp_path) -> None:
    """Return bearer token payload when credentials are valid."""

    with _build_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/auth/token",
            json={"username": "admin", "password": "secret"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["role"] == "admin"
    assert isinstance(payload["access_token"], str)
    assert payload["expires_in"] == 3600


def test_auth_token_rejected_for_invalid_password(monkeypatch, tmp_path) -> None:
    """Reject invalid credential combinations with HTTP 401."""

    with _build_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/auth/token",
            json={"username": "admin", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."
