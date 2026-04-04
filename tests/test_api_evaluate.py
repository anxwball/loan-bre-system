"""Validate single and batch evaluation API endpoints."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from passlib.context import CryptContext

from src.api.main import create_app


def _build_users_payload() -> str:
    """Create USERS env JSON with hashed credentials for role testing."""

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
    monkeypatch.setenv("LOAN_BRE_DATABASE_URL", f"sqlite:///{(tmp_path / 'api_evaluate.db').as_posix()}")

    app = create_app()
    return TestClient(app)


def _token_for(client: TestClient, username: str, password: str) -> str:
    """Issue token for a test identity and return bearer token string."""

    response = client.post("/auth/token", json={"username": username, "password": password})
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

    with _build_client(monkeypatch, tmp_path) as client:
        analyst_token = _token_for(client, "analyst", "analyst")
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

    with _build_client(monkeypatch, tmp_path) as client:
        analyst_token = _token_for(client, "analyst", "analyst")
        response = client.post(
            "/v1/evaluate/batch",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"applications": [_base_payload()]},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role is required."


def test_batch_evaluation_returns_summary_for_admin(monkeypatch, tmp_path) -> None:
    """Allow admin batch evaluations and return aggregate summary data."""

    with _build_client(monkeypatch, tmp_path) as client:
        admin_token = _token_for(client, "admin", "secret")
        response = client.post(
            "/v1/evaluate/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"applications": [_base_payload(), _base_payload()]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 2
    assert len(payload["results"]) == 2
