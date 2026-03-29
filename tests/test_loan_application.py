"""Domain invariant tests for LoanApplication."""

import pytest

from src.loan_application import LoanApplication


def _base_payload() -> dict[str, object]:
    """Return a minimal valid payload for LoanApplication construction."""

    return {
        "loan_id": "LPTEST001",
        "gender": "Male",
        "married": "No",
        "dependents": "0",
        "education": "Graduate",
        "self_employed": "No",
        "applicant_income": 5000.0,
        "coapplicant_income": 0.0,
        "loan_amount": 100.0,
        "loan_amount_term": 360.0,
        "credit_history": 1,
        "property_area": "Urban",
    }


@pytest.mark.parametrize(
    "field, value, expected_message",
    [
        ("applicant_income", -1.0, "Applicant income cannot be negative."),
        ("coapplicant_income", -1.0, "Co-applicant income cannot be negative."),
        ("loan_amount", -1.0, "Loan amount cannot be negative."),
        ("loan_amount", 0.0, "Loan amount must be greater than zero."),
        ("loan_amount_term", 0.0, "Loan term must be a positive number of months."),
        ("loan_amount_term", -1.0, "Loan term must be a positive number of months."),
        ("credit_history", 2, "Credit history must be either 0 or 1."),
    ],
)
def test_invalid_inputs_raise_value_error(field, value, expected_message) -> None:
    """Invalid numeric or enum inputs should raise clear domain errors."""

    payload = _base_payload()
    payload[field] = value

    with pytest.raises(ValueError, match=expected_message):
        LoanApplication(**payload)


def test_total_income_must_be_positive() -> None:
    """A profile with zero combined income should be rejected by invariant."""

    payload = _base_payload()
    payload["applicant_income"] = 0.0
    payload["coapplicant_income"] = 0.0

    with pytest.raises(ValueError, match="Total income must be greater than zero."):
        LoanApplication(**payload)


def test_derived_fields_are_computed_on_init() -> None:
    """Initialization should compute total_income and loan_to_income_ratio."""

    app = LoanApplication(**_base_payload())

    assert app.total_income == pytest.approx(5000.0)
    assert app.loan_to_income_ratio == pytest.approx(0.02)
