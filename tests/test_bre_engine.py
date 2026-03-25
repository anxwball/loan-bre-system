"""Unit tests for the first traceable BRE implementation."""

from src.bre_engine import RuleEngine
from src.loan_application import LoanApplication


def build_application(**overrides) -> LoanApplication:
    """Create a valid baseline application and allow selective overrides.

    Args:
        **overrides: Field overrides for the base application.

    Returns:
        LoanApplication ready for evaluation.
    """

    base_data = {
        "loan_id": "LP001",
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
    base_data.update(overrides)
    return LoanApplication(**base_data)


def test_hard_rule_credit_history_denies_immediately() -> None:
    """A failed HARD-01 rule must deny without soft-score processing."""

    engine = RuleEngine()
    app = build_application(credit_history=0)

    result = engine.evaluate(app)

    assert result.approved is False
    assert result.hard_rejection is True
    assert result.score == 0
    assert result.rules_triggered[0].criterion_ref == "HARD-01"
    assert "HARD-01 failed" in result.reasons[0]


def test_low_risk_application_is_approved() -> None:
    """A low-risk profile should be approved without review flag."""

    engine = RuleEngine()
    app = build_application()

    result = engine.evaluate(app)

    assert result.approved is True
    assert result.flagged_for_review is False
    assert result.hard_rejection is False
    assert result.score == 0


def test_mid_risk_application_is_approved_with_review_flag() -> None:
    """Scores inside 31-50 band should approve with review recommendation."""

    engine = RuleEngine()
    app = build_application(
        self_employed="Yes",
        dependents="2",
        property_area="Rural",
        loan_amount=20000.0,
        loan_amount_term=360.0,
    )

    result = engine.evaluate(app)

    assert result.score == 40
    assert result.approved is True
    assert result.flagged_for_review is True
    assert result.hard_rejection is False


def test_high_risk_application_is_denied_by_soft_score() -> None:
    """Scores of 51 or more should deny even when hard rules pass."""

    engine = RuleEngine()
    app = build_application(
        self_employed="Yes",
        dependents="3+",
        property_area="Rural",
        loan_amount=32000.0,
        loan_amount_term=360.0,
    )

    result = engine.evaluate(app)

    assert result.score == 65
    assert result.approved is False
    assert result.flagged_for_review is False
    assert result.hard_rejection is False
