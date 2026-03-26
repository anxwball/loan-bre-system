"""Define atomic BRE rules with explicit traceability metadata.

This module contains pure rule functions grouped as HARD and SOFT sets.
Each rule evaluates a single business criterion and returns a structured
`RuleResult` with identifiers that map directly to the approval criteria file.
"""

from dataclasses import dataclass
from typing import Callable

from src.loan_application import LoanApplication

MAX_MONTHLY_PAYMENT_RATIO = 0.40

@dataclass(frozen=True)
class RuleResult:
    """Represent the outcome of one business rule evaluation.

    Args:
        rule_id: Internal sequential identifier (R##).
        name: Stable rule name in PascalCase.
        criterion_ref: Business-criteria reference (for example HARD-01).
        rule_type: Rule family, expected values are hard or soft.
        passed: Whether the evaluated condition is acceptable.
        points: Risk delta contributed by this rule.
        reason: Human-readable explanation of the evaluation.

    Returns:
        Immutable rule result instance.
    """

    rule_id: str
    name: str
    criterion_ref: str
    rule_type: str
    passed: bool
    points: int
    reason: str


RuleFunction = Callable[[LoanApplication], RuleResult]


def rule_credit_history_required(app: LoanApplication) -> RuleResult:
    """Reject applications with missing or negative credit history.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion HARD-01.
    """

    passed = app.credit_history == 1
    reason = (
        "HARD-01 passed: credit history is positive."
        if passed
        else "HARD-01 failed: credit history is zero, application is denied."
    )
    return RuleResult("R01", "CreditHistoryRequired", "HARD-01", "hard", passed, 0, reason)


def rule_positive_total_income(app: LoanApplication) -> RuleResult:
    """Reject applications without repayment capacity.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion HARD-02.
    """

    passed = app.total_income > 0
    reason = (
        "HARD-02 passed: total income is greater than zero."
        if passed
        else "HARD-02 failed: total income is zero or negative, application is denied."
    )
    return RuleResult("R02", "PositiveTotalIncome", "HARD-02", "hard", passed, 0, reason)


def rule_monthly_payment_capacity(app: LoanApplication) -> RuleResult:
    """Reject applications where monthly payment burden is too high.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion HARD-03.
    """

    monthly_payment_ratio = (app.loan_amount / app.loan_amount_term) / app.total_income
    passed = monthly_payment_ratio <= MAX_MONTHLY_PAYMENT_RATIO
    reason = (
        f"HARD-03 passed: monthly payment ratio {monthly_payment_ratio:.3f} is within the 0.40 cap."
        if passed
        else f"HARD-03 failed: monthly payment ratio {monthly_payment_ratio:.3f} exceeds the 0.40 cap, application is denied."
    )
    return RuleResult("R03", "MonthlyPaymentCapacity", "HARD-03", "hard", passed, 0, reason)


def rule_high_leverage(app: LoanApplication) -> RuleResult:
    """Add risk for very high leverage.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-01.
    """

    triggered = app.loan_to_income_ratio > 6.0
    points = 20 if triggered else 0
    reason = (
        f"SOFT-01 triggered: loan_to_income_ratio {app.loan_to_income_ratio:.3f} is above 6.0 (+20 risk)."
        if triggered
        else f"SOFT-01 not triggered: loan_to_income_ratio {app.loan_to_income_ratio:.3f} is not above 6.0 (+0 risk)."
    )
    return RuleResult("R04", "HighLeverage", "SOFT-01", "soft", not triggered, points, reason)


def rule_moderate_leverage(app: LoanApplication) -> RuleResult:
    """Add risk for moderate leverage.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-02.
    """

    triggered = app.loan_to_income_ratio > 3.0
    points = 10 if triggered else 0
    reason = (
        f"SOFT-02 triggered: loan_to_income_ratio {app.loan_to_income_ratio:.3f} is above 3.0 (+10 risk)."
        if triggered
        else f"SOFT-02 not triggered: loan_to_income_ratio {app.loan_to_income_ratio:.3f} is not above 3.0 (+0 risk)."
    )
    return RuleResult("R05", "ModerateLeverage", "SOFT-02", "soft", not triggered, points, reason)


def rule_self_employed_risk(app: LoanApplication) -> RuleResult:
    """Add risk when the applicant is self-employed.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-03.
    """

    triggered = app.self_employed == "Yes"
    points = 15 if triggered else 0
    reason = (
        "SOFT-03 triggered: self-employed applicant profile (+15 risk)."
        if triggered
        else "SOFT-03 not triggered: applicant is not self-employed (+0 risk)."
    )
    return RuleResult("R06", "SelfEmployedRisk", "SOFT-03", "soft", not triggered, points, reason)


def rule_high_dependents_burden(app: LoanApplication) -> RuleResult:
    """Add risk for high dependents burden.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-04.
    """

    triggered = app.dependents == "3+"
    points = 10 if triggered else 0
    reason = (
        "SOFT-04 triggered: dependents category is 3+ (+10 risk)."
        if triggered
        else "SOFT-04 not triggered: dependents category is not 3+ (+0 risk)."
    )
    return RuleResult("R07", "HighDependentsBurden", "SOFT-04", "soft", not triggered, points, reason)


def rule_moderate_dependents_burden(app: LoanApplication) -> RuleResult:
    """Add risk for moderate dependents burden.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-05.
    """

    triggered = app.dependents == "2"
    points = 5 if triggered else 0
    reason = (
        "SOFT-05 triggered: dependents category is 2 (+5 risk)."
        if triggered
        else "SOFT-05 not triggered: dependents category is not 2 (+0 risk)."
    )
    return RuleResult("R08", "ModerateDependentsBurden", "SOFT-05", "soft", not triggered, points, reason)


def rule_rural_area_risk(app: LoanApplication) -> RuleResult:
    """Add risk when collateral context is rural.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-06.
    """

    triggered = app.property_area == "Rural"
    points = 10 if triggered else 0
    reason = (
        "SOFT-06 triggered: property area is Rural (+10 risk)."
        if triggered
        else "SOFT-06 not triggered: property area is not Rural (+0 risk)."
    )
    return RuleResult("R09", "RuralAreaRisk", "SOFT-06", "soft", not triggered, points, reason)


def rule_semiurban_area_risk(app: LoanApplication) -> RuleResult:
    """Add risk when collateral context is semiurban.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-07.
    """

    triggered = app.property_area == "Semiurban"
    points = 5 if triggered else 0
    reason = (
        "SOFT-07 triggered: property area is Semiurban (+5 risk)."
        if triggered
        else "SOFT-07 not triggered: property area is not Semiurban (+0 risk)."
    )
    return RuleResult("R10", "SemiurbanAreaRisk", "SOFT-07", "soft", not triggered, points, reason)


def rule_dual_income_stability(app: LoanApplication) -> RuleResult:
    """Reduce risk when dual-income household evidence exists.

    Args:
        app: Loan application domain object.

    Returns:
        RuleResult for criterion SOFT-08.
    """

    triggered = app.married == "Yes" and app.coapplicant_income > 0
    points = -10 if triggered else 0
    reason = (
        "SOFT-08 triggered: married with co-applicant income (+ stability, -10 risk)."
        if triggered
        else "SOFT-08 not triggered: no dual-income stability bonus (+0 risk)."
    )
    return RuleResult("R11", "DualIncomeStability", "SOFT-08", "soft", True, points, reason)


HARD_RULES: list[RuleFunction] = [
    rule_credit_history_required,
    rule_positive_total_income,
    rule_monthly_payment_capacity,
]

SOFT_RULES: list[RuleFunction] = [
    rule_high_leverage,
    rule_moderate_leverage,
    rule_self_employed_risk,
    rule_high_dependents_burden,
    rule_moderate_dependents_burden,
    rule_rural_area_risk,
    rule_semiurban_area_risk,
    rule_dual_income_stability,
]
