"""Validate authentication behavior for the Phase 4c API layer."""

from __future__ import annotations

from secrets import token_urlsafe

from src.api.schemas.auth import TokenRequest


def test_auth_token_issued_for_valid_credentials(api_client_factory) -> None:
    """Return bearer token payload when credentials are valid."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with api_client_factory(admin_secret, analyst_secret, "api_auth.db") as client:
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


def test_auth_token_rejected_for_invalid_password(api_client_factory) -> None:
    """Reject invalid credential combinations with HTTP 401."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)
    invalid_secret = token_urlsafe(24)

    with api_client_factory(admin_secret, analyst_secret, "api_auth.db") as client:
        response = client.post(
            "/auth/token",
            json=TokenRequest(username="admin", password=invalid_secret).model_dump(),
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."
