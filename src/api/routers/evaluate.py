"""Expose single and batch loan evaluation endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user, require_admin
from src.api.schemas.request import BatchEvaluationRequest, LoanEvaluationRequest
from src.api.schemas.response import (
    BatchEvaluationResponse,
    BatchSummary,
    DecisionResponse,
    EvaluationResponse,
    RuleTraceResponse,
)
from src.audit_logger import log_decision_audit
from src.bre_engine import DecisionResult, RuleEngine
from src.loan_application import LoanApplication

router = APIRouter(tags=["evaluate"])


def _build_loan_application(payload: LoanEvaluationRequest) -> LoanApplication:
    """Convert API payload into the domain object used by BRE.

    Args:
        payload: Validated API request payload.

    Returns:
        LoanApplication domain object.

    Raises:
        HTTPException: If domain invariants reject payload values.
    """

    try:
        return LoanApplication(
            loan_id=payload.loan_id,
            gender=payload.gender,
            married=payload.married,
            dependents=payload.dependents,
            education=payload.education,
            self_employed=payload.self_employed,
            applicant_income=payload.applicant_income,
            coapplicant_income=payload.coapplicant_income,
            loan_amount=payload.loan_amount,
            loan_amount_term=payload.loan_amount_term,
            credit_history=int(payload.credit_history),
            property_area=payload.property_area,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _rule_trace_to_response(rule_trace) -> RuleTraceResponse:
    """Map domain RuleResult to API trace response contract."""

    return RuleTraceResponse(
        rule_id=rule_trace.rule_id,
        name=rule_trace.name,
        criterion_ref=rule_trace.criterion_ref,
        rule_type=rule_trace.rule_type,
        passed=rule_trace.passed,
        points=rule_trace.points,
        reason=rule_trace.reason,
    )


def _decision_to_response(decision: DecisionResult) -> DecisionResponse:
    """Map domain DecisionResult into API response schema."""

    return DecisionResponse(
        approved=decision.approved,
        score=decision.score,
        hard_rejection=decision.hard_rejection,
        flagged_for_review=decision.flagged_for_review,
        summary=decision.summary(),
        reasons=list(decision.reasons),
        rule_traces=[_rule_trace_to_response(trace) for trace in decision.rules_triggered],
    )


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
def evaluate_single_application(
    payload: LoanEvaluationRequest,
    _user: Annotated[dict[str, str], Depends(get_current_user)],
) -> EvaluationResponse:
    """Evaluate one loan application and persist SQL audit artifacts."""

    evaluated_at = datetime.now(timezone.utc)
    app = _build_loan_application(payload)
    engine = RuleEngine()
    decision = engine.evaluate(app)

    log_decision_audit(
        app=app,
        decision=decision,
        applicant_id=app.loan_id,
        audit_mode="sql",
    )

    return EvaluationResponse(
        loan_id=app.loan_id,
        evaluated_at=evaluated_at,
        decision=_decision_to_response(decision),
    )


@router.post(
    "/batch",
    status_code=status.HTTP_200_OK,
)
def evaluate_batch_applications(
    payload: BatchEvaluationRequest,
    _admin: Annotated[dict[str, str], Depends(require_admin)],
) -> BatchEvaluationResponse:
    """Evaluate a bounded batch of applications with admin-only access."""

    evaluated_at = datetime.now(timezone.utc)
    engine = RuleEngine()
    results: list[EvaluationResponse] = []

    approved_count = 0
    denied_count = 0
    flagged_count = 0
    hard_rejections = 0
    scores: list[int] = []

    for item in payload.applications:
        app = _build_loan_application(item)
        decision = engine.evaluate(app)

        log_decision_audit(
            app=app,
            decision=decision,
            applicant_id=app.loan_id,
            audit_mode="sql",
        )

        if decision.approved:
            approved_count += 1
        else:
            denied_count += 1

        if decision.flagged_for_review:
            flagged_count += 1
        if decision.hard_rejection:
            hard_rejections += 1

        scores.append(decision.score)
        results.append(
            EvaluationResponse(
                loan_id=app.loan_id,
                evaluated_at=evaluated_at,
                decision=_decision_to_response(decision),
            )
        )

    summary = BatchSummary(
        total=len(results),
        approved=approved_count,
        denied=denied_count,
        flagged_for_review=flagged_count,
        hard_rejections=hard_rejections,
        avg_score=float(mean(scores)) if scores else 0.0,
    )

    return BatchEvaluationResponse(
        evaluated_at=evaluated_at,
        summary=summary,
        results=results,
    )
