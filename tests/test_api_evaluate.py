"""Validate single and batch evaluation API endpoints."""

from __future__ import annotations

import json
from secrets import token_urlsafe

from fastapi.testclient import TestClient
from passlib.context import CryptContext

from src.api.main import create_app
from src.api.schemas.auth import TokenRequest


def _build_users_payload(admin_secret: str, analyst_secret: str) -> str:
    """Create USERS env JSON with runtime-generated credentials for role testing."""

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
    monkeypatch.setenv("LOAN_BRE_DATABASE_URL", f"sqlite:///{(tmp_path / 'api_evaluate.db').as_posix()}")

    app = create_app()
    return TestClient(app)


def _token_for(client: TestClient, username: str, user_secret: str) -> str:
    """Issue token for a test identity and return bearer token string."""

    response = client.post(
        "/auth/token",
        json=TokenRequest(username=username, password=user_secret).model_dump(),
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _base_payload() -> dict[str, object]:
    """Return one deterministic valid payload for single evaluation."""

    return {
        "gender": "Male",
        "married": "Yes",
        "dependents": "0",
        "education": "Graduate",
        "self_employed": "No",
        "applicant_income": 5000,
        "coapplicant_income": 2000,
        "loan_amount": 150,
        "loan_amount_term": 360,
        "credit_history": 1,
        "property_area": "Urban",
    }


def test_single_evaluation_accepts_analyst_role(monkeypatch, tmp_path) -> None:
    """Allow analyst to evaluate one application via /v1/evaluate."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with _build_client(monkeypatch, tmp_path, admin_secret, analyst_secret) as client:
        analyst_token = _token_for(client, "analyst", analyst_secret)
        response = client.post(
            "/v1/evaluate",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json=_base_payload(),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["summary"].startswith(("APPROVED", "DENIED"))
    assert isinstance(payload["decision"]["rule_traces"], list)
    assert payload["loan_id"].startswith("API-")


def test_batch_evaluation_requires_admin_role(monkeypatch, tmp_path) -> None:
    """Reject analyst calls for /v1/evaluate/batch with HTTP 403."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with _build_client(monkeypatch, tmp_path, admin_secret, analyst_secret) as client:
        analyst_token = _token_for(client, "analyst", analyst_secret)
        response = client.post(
            "/v1/evaluate/batch",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"applications": [_base_payload()]},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role is required."


def test_batch_evaluation_returns_summary_for_admin(monkeypatch, tmp_path) -> None:
    """Allow admin batch evaluations and return aggregate summary data."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with _build_client(monkeypatch, tmp_path, admin_secret, analyst_secret) as client:
        admin_token = _token_for(client, "admin", admin_secret)
        response = client.post(
            "/v1/evaluate/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"applications": [_base_payload(), _base_payload()]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 2
    assert len(payload["results"]) == 2
