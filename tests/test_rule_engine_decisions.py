"""Decision-flow tests for RuleEngine evaluate behavior."""


def test_low_risk_application_is_approved(engine, build_application) -> None:
    """A low-risk profile should be approved without review."""

    result = engine.evaluate(build_application())

    assert result.approved is True
    assert result.flagged_for_review is False
    assert result.hard_rejection is False
    assert result.score == 0
    assert "automatic approval band" in result.reasons[0]


def test_review_band_application_is_approved_with_flag(engine, build_application) -> None:
    """A score inside the review band should be approved with manual review."""

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
    assert "review band" in result.reasons[0]


def test_denial_band_application_is_denied(engine, build_application) -> None:
    """A score above the review band should be denied."""

    app = build_application(
        applicant_income=1000.0,
        loan_amount=7000.0,
        self_employed="Yes",
        dependents="3+",
    )

    result = engine.evaluate(app)

    assert result.score == 55
    assert result.approved is False
    assert result.flagged_for_review is False
    assert result.hard_rejection is False
    assert "denial band" in result.reasons[0]


def test_score_30_is_auto_approval_boundary(engine, build_application) -> None:
    """Score 30 is still in automatic approval range."""

    app = build_application(
        self_employed="Yes",
        dependents="3+",
        property_area="Semiurban",
    )

    result = engine.evaluate(app)

    assert result.score == 30
    assert result.approved is True
    assert result.flagged_for_review is False


def test_score_35_enters_review_band_boundary(engine, build_application) -> None:
    """Lowest reachable score above 30 should trigger review flag."""

    app = build_application(
        self_employed="Yes",
        dependents="3+",
        loan_amount=20000.0,
    )

    result = engine.evaluate(app)

    assert result.score == 35
    assert result.approved is True
    assert result.flagged_for_review is True


def test_score_50_stays_in_review_band_boundary(engine, build_application) -> None:
    """Score 50 should remain approved but flagged."""

    app = build_application(
        applicant_income=1000.0,
        loan_amount=7000.0,
        self_employed="Yes",
        dependents="2",
    )

    result = engine.evaluate(app)

    assert result.score == 50
    assert result.approved is True
    assert result.flagged_for_review is True


def test_score_55_is_denied_above_review_boundary(engine, build_application) -> None:
    """First reachable score above 50 should deny the application."""

    app = build_application(
        applicant_income=1000.0,
        loan_amount=7000.0,
        self_employed="Yes",
        dependents="3+",
    )

    result = engine.evaluate(app)

    assert result.score == 55
    assert result.approved is False
    assert result.flagged_for_review is False


def test_hard_rule_credit_history_denies_immediately(engine, build_application) -> None:
    """HARD-01 failure must deny and stop processing."""

    result = engine.evaluate(build_application(credit_history=0))

    assert result.approved is False
    assert result.hard_rejection is True
    assert result.score == 0
    assert result.rules_triggered[0].criterion_ref == "HARD-01"
    assert len(result.rules_triggered) == 1


def test_hard_rule_monthly_payment_capacity_denies_immediately(engine, build_application) -> None:
    """HARD-03 failure must deny without evaluating soft rules."""

    app = build_application(applicant_income=1000.0, loan_amount=500.0, loan_amount_term=1.0)

    result = engine.evaluate(app)

    assert result.approved is False
    assert result.hard_rejection is True
    assert result.score == 0
    assert result.rules_triggered[-1].criterion_ref == "HARD-03"
    assert len(result.rules_triggered) == 3


def test_hard_rule_positive_income_rejects_when_total_income_forced_to_zero(engine, build_application) -> None:
    """HARD-02 should reject if total income becomes zero at evaluation time."""

    app = build_application()
    app.total_income = 0.0

    result = engine.evaluate(app)

    assert result.approved is False
    assert result.hard_rejection is True
    assert result.rules_triggered[-1].criterion_ref == "HARD-02"


def test_rules_trace_contains_all_rules_on_non_hard_rejection(engine, build_application) -> None:
    """A full evaluation should include all hard and soft rule traces."""

    result = engine.evaluate(build_application())

    assert len(result.rules_triggered) == 11
    assert result.rules_triggered[0].criterion_ref == "HARD-01"
    assert result.rules_triggered[-1].criterion_ref == "SOFT-08"
