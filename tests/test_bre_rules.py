"""Unit tests for atomic hard and soft BRE rule functions."""

import pytest

from src.bre_rules import (
    rule_credit_history_required,
    rule_dual_income_stability,
    rule_high_dependents_burden,
    rule_high_leverage,
    rule_moderate_dependents_burden,
    rule_moderate_leverage,
    rule_monthly_payment_capacity,
    rule_positive_total_income,
    rule_rural_area_risk,
    rule_semiurban_area_risk,
    rule_self_employed_risk,
)


@pytest.mark.parametrize(
    "overrides, rule_fn, expected_points, expected_ref",
    [
        ({"loan_amount": 35000.0}, rule_high_leverage, 20, "SOFT-01"),
        ({"loan_amount": 20000.0}, rule_moderate_leverage, 10, "SOFT-02"),
        ({"self_employed": "Yes"}, rule_self_employed_risk, 15, "SOFT-03"),
        ({"dependents": "3+"}, rule_high_dependents_burden, 10, "SOFT-04"),
        ({"dependents": "2"}, rule_moderate_dependents_burden, 5, "SOFT-05"),
        ({"property_area": "Rural"}, rule_rural_area_risk, 10, "SOFT-06"),
        ({"property_area": "Semiurban"}, rule_semiurban_area_risk, 5, "SOFT-07"),
        ({"married": "Yes", "coapplicant_income": 1000.0}, rule_dual_income_stability, -10, "SOFT-08"),
    ],
)
def test_soft_rules_trigger_expected_points(
    build_application,
    overrides,
    rule_fn,
    expected_points,
    expected_ref,
) -> None:
    """Each soft rule should return its configured risk delta when triggered."""

    result = rule_fn(build_application(**overrides))

    assert result.points == expected_points
    assert result.criterion_ref == expected_ref


@pytest.mark.parametrize(
    "rule_fn, expected_ref",
    [
        (rule_high_leverage, "SOFT-01"),
        (rule_moderate_leverage, "SOFT-02"),
        (rule_self_employed_risk, "SOFT-03"),
        (rule_high_dependents_burden, "SOFT-04"),
        (rule_moderate_dependents_burden, "SOFT-05"),
        (rule_rural_area_risk, "SOFT-06"),
        (rule_semiurban_area_risk, "SOFT-07"),
        (rule_dual_income_stability, "SOFT-08"),
    ],
)
def test_soft_rules_return_zero_points_when_not_triggered(
    build_application,
    rule_fn,
    expected_ref,
) -> None:
    """Soft rules should return neutral points for baseline profile."""

    result = rule_fn(build_application())

    assert result.points == 0
    assert result.criterion_ref == expected_ref


def test_rule_credit_history_required_fails_with_zero_history(build_application) -> None:
    """Hard rule HARD-01 should fail when credit history is zero."""

    result = rule_credit_history_required(build_application(credit_history=0))

    assert result.passed is False
    assert result.criterion_ref == "HARD-01"


def test_rule_positive_total_income_fails_when_total_income_forced_to_zero(build_application) -> None:
    """Hard rule HARD-02 should fail when total income is forced to zero."""

    app = build_application()
    app.total_income = 0.0

    result = rule_positive_total_income(app)

    assert result.passed is False
    assert result.criterion_ref == "HARD-02"


def test_rule_monthly_payment_capacity_fails_above_ratio_cap(build_application) -> None:
    """Hard rule HARD-03 should fail if monthly payment ratio exceeds 0.40."""

    app = build_application(applicant_income=1000.0, loan_amount=500.0, loan_amount_term=1.0)

    result = rule_monthly_payment_capacity(app)

    assert result.passed is False
    assert result.criterion_ref == "HARD-03"
