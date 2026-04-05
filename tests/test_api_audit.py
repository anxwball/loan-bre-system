"""Validate audit and analyst queue endpoints for role-based access."""

from __future__ import annotations

from secrets import token_urlsafe



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


def test_admin_can_list_audit_evaluations_and_traces(api_client_factory, issue_access_token) -> None:
    """Allow admin to inspect evaluations and rule traces."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with api_client_factory(admin_secret, analyst_secret, "api_audit.db") as client:
        admin_token = issue_access_token(client, "admin", admin_secret)

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


def test_analyst_queue_visible_for_analyst_role(api_client_factory, issue_access_token) -> None:
    """Allow analyst role to query queue endpoint without trace overexposure."""

    admin_secret = token_urlsafe(24)
    analyst_secret = token_urlsafe(24)

    with api_client_factory(admin_secret, analyst_secret, "api_audit.db") as client:
        admin_token = issue_access_token(client, "admin", admin_secret)
        analyst_token = issue_access_token(client, "analyst", analyst_secret)

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
