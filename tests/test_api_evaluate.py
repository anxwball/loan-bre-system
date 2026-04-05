"""Validate single and batch evaluation API endpoints."""

from __future__ import annotations

from secrets import token_urlsafe



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


def test_single_evaluation_accepts_analyst_role(api_client_factory, issue_access_token) -> None:
    """Allow analyst to evaluate one application via /v1/evaluate."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with api_client_factory(admin_secret, analyst_secret, "api_evaluate.db") as client:
        analyst_token = issue_access_token(client, "analyst", analyst_secret)
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


def test_batch_evaluation_requires_admin_role(api_client_factory, issue_access_token) -> None:
    """Reject analyst calls for /v1/evaluate/batch with HTTP 403."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with api_client_factory(admin_secret, analyst_secret, "api_evaluate.db") as client:
        analyst_token = issue_access_token(client, "analyst", analyst_secret)
        response = client.post(
            "/v1/evaluate/batch",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"applications": [_base_payload()]},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role is required."


def test_batch_evaluation_returns_summary_for_admin(api_client_factory, issue_access_token) -> None:
    """Allow admin batch evaluations and return aggregate summary data."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with api_client_factory(admin_secret, analyst_secret, "api_evaluate.db") as client:
        admin_token = issue_access_token(client, "admin", admin_secret)
        response = client.post(
            "/v1/evaluate/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"applications": [_base_payload(), _base_payload()]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 2
    assert len(payload["results"]) == 2
