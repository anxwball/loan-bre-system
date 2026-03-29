"""Integral smoke test using the cleaned dataset as BRE input."""

from src.loan_application import LoanApplication


def test_integral_auto_approval_from_cleaned_dataset(engine, cleaned_row_lp001015) -> None:
    """Use one deterministic cleaned row and validate full decision output."""

    app = LoanApplication(**cleaned_row_lp001015)

    result = engine.evaluate(app)

    assert result.approved is True
    assert result.flagged_for_review is False
    assert result.hard_rejection is False
    assert result.score == 0
    assert result.reasons[0] == "Final decision: score is within automatic approval band (0-30)."

    criterion_refs = [rule.criterion_ref for rule in result.rules_triggered]
    assert len(criterion_refs) == 11
    assert criterion_refs[0] == "HARD-01"
    assert criterion_refs[-1] == "SOFT-08"
