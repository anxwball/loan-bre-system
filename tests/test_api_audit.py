"""Validate audit and analyst queue endpoints for role-based access."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from passlib.context import CryptContext

from src.api.main import create_app


def _build_users_payload() -> str:
    """Create USERS env JSON with admin and analyst identities."""

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
    monkeypatch.setenv("LOAN_BRE_DATABASE_URL", f"sqlite:///{(tmp_path / 'api_audit.db').as_posix()}")

    app = create_app()
    return TestClient(app)


def _token_for(client: TestClient, username: str, password: str) -> str:
    """Issue token for one test identity."""

    response = client.post("/auth/token", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _review_payload() -> dict[str, object]:
    """Return payload expected to land in review band for analyst queue."""

    return {
        "gender": "Male",
        "married": "No",
        "dependents": "2",
        "education": "Graduate",
        "self_employed": "Yes",
        "applicant_income": 100,
        "coapplicant_income": 0,
        "loan_amount": 350,
        "loan_amount_term": 360,
        "credit_history": 1,
        "property_area": "Rural",
    }


def test_admin_can_list_audit_evaluations_and_traces(monkeypatch, tmp_path) -> None:
    """Allow admin to inspect evaluations and rule traces."""

    with _build_client(monkeypatch, tmp_path) as client:
        admin_token = _token_for(client, "admin", "secret")

        evaluate_response = client.post(
            "/v1/evaluate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=_review_payload(),
        )
        assert evaluate_response.status_code == 200

        list_response = client.get(
            "/v1/audit/evaluations",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 200
        list_payload = list_response.json()
        assert list_payload["total"] >= 1

        evaluation_id = list_payload["items"][0]["evaluation_id"]
        traces_response = client.get(
            f"/v1/audit/evaluations/{evaluation_id}/traces",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert traces_response.status_code == 200
    assert isinstance(traces_response.json(), list)


def test_analyst_queue_visible_for_analyst_role(monkeypatch, tmp_path) -> None:
    """Allow analyst role to query queue endpoint without trace overexposure."""

    with _build_client(monkeypatch, tmp_path) as client:
        admin_token = _token_for(client, "admin", "secret")
        analyst_token = _token_for(client, "analyst", "analyst")

        create_response = client.post(
            "/v1/evaluate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=_review_payload(),
        )
        assert create_response.status_code == 200

        queue_response = client.get(
            "/v1/analyst/queue",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )

    assert queue_response.status_code == 200
    payload = queue_response.json()
    assert payload["total"] >= 1
    assert "rule_traces" not in payload["items"][0]
