"""Expose audit and analyst queue endpoints backed by SQL persistence."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Connection, func, select

from src.api.dependencies import get_db, require_admin, require_analyst
from src.api.schemas.response import (
    AnalystQueueItem,
    AnalystQueueResponse,
    AuditEvaluationPage,
    AuditEvaluationRecord,
    RuleTraceResponse,
)
from src.db.schema import audit_evaluations, audit_rule_traces, loan_applications

RULE_NAMES_BY_ID = {
    "R01": "CreditHistoryRequired",
    "R02": "PositiveTotalIncome",
    "R03": "MonthlyPaymentCapacity",
    "R04": "HighLeverage",
    "R05": "ModerateLeverage",
    "R06": "SelfEmployedRisk",
    "R07": "HighDependentsBurden",
    "R08": "ModerateDependentsBurden",
    "R09": "RuralAreaRisk",
    "R10": "SemiurbanAreaRisk",
    "R11": "DualIncomeStability",
}

audit_router = APIRouter(tags=["audit"])
analyst_router = APIRouter(tags=["analyst"])


def _coerce_reasons(raw_reasons: str) -> list[str]:
    """Decode persisted reasons payload into list format."""

    try:
        decoded = json.loads(raw_reasons)
    except json.JSONDecodeError:
        return [raw_reasons]

    if isinstance(decoded, list):
        return [str(item) for item in decoded]

    return [str(decoded)]


def _trace_from_row(row: dict) -> RuleTraceResponse:
    """Map SQL trace row into API trace response contract."""

    points = int(row.get("points") or 0)
    triggered = bool(row.get("triggered"))
    rule_type = str(row.get("rule_type", ""))
    if rule_type == "hard":
        passed = not triggered
    else:
        passed = points <= 0

    rule_id = str(row.get("rule_id", ""))
    return RuleTraceResponse(
        rule_id=rule_id,
        name=RULE_NAMES_BY_ID.get(rule_id, "UnknownRule"),
        criterion_ref=str(row.get("criterion_ref") or ""),
        rule_type=rule_type,
        passed=passed,
        points=points,
        reason=str(row.get("reason") or ""),
    )


@audit_router.get(
    "/evaluations",
    response_model=AuditEvaluationPage,
    status_code=status.HTTP_200_OK,
)
def list_audit_evaluations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    _admin: dict[str, str] = Depends(require_admin),
    db: Connection = Depends(get_db),
) -> AuditEvaluationPage:
    """Return paginated persisted evaluations for admin users."""

    total = int(
        db.execute(select(func.count()).select_from(audit_evaluations)).scalar_one()
    )
    offset = (page - 1) * page_size

    statement = (
        select(
            audit_evaluations.c.id.label("evaluation_id"),
            loan_applications.c.loan_id,
            audit_evaluations.c.evaluated_at,
            audit_evaluations.c.decision,
            audit_evaluations.c.risk_score,
            audit_evaluations.c.hard_rejection,
            audit_evaluations.c.review_flag,
        )
        .join(
            loan_applications,
            loan_applications.c.id == audit_evaluations.c.loan_application_id,
        )
        .order_by(audit_evaluations.c.id.desc())
        .offset(offset)
        .limit(page_size)
    )

    rows = db.execute(statement).mappings().all()
    items = [
        AuditEvaluationRecord(
            evaluation_id=int(row["evaluation_id"]),
            loan_id=str(row["loan_id"]),
            evaluated_at=row["evaluated_at"],
            approved=str(row["decision"]).lower() == "approved",
            score=int(row["risk_score"]),
            hard_rejection=bool(row["hard_rejection"]),
            flagged_for_review=bool(row["review_flag"]),
            rule_traces=None,
        )
        for row in rows
    ]

    return AuditEvaluationPage(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@audit_router.get(
    "/evaluations/{evaluation_id}/traces",
    response_model=list[RuleTraceResponse],
    status_code=status.HTTP_200_OK,
)
def get_evaluation_traces(
    evaluation_id: int,
    _admin: dict[str, str] = Depends(require_admin),
    db: Connection = Depends(get_db),
) -> list[RuleTraceResponse]:
    """Return detailed rule traces for one persisted evaluation."""

    exists_statement = select(audit_evaluations.c.id).where(audit_evaluations.c.id == evaluation_id)
    if db.execute(exists_statement).scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found.",
        )

    trace_statement = (
        select(audit_rule_traces)
        .where(audit_rule_traces.c.evaluation_id == evaluation_id)
        .order_by(audit_rule_traces.c.id.asc())
    )
    rows = db.execute(trace_statement).mappings().all()
    return [_trace_from_row(dict(row)) for row in rows]


@analyst_router.get(
    "/queue",
    response_model=AnalystQueueResponse,
    status_code=status.HTTP_200_OK,
)
def list_analyst_queue(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    _analyst: dict[str, str] = Depends(require_analyst),
    db: Connection = Depends(get_db),
) -> AnalystQueueResponse:
    """Return paginated flagged evaluations for analyst queue consumption."""

    total_statement = (
        select(func.count())
        .select_from(audit_evaluations)
        .where(audit_evaluations.c.review_flag == 1)
    )
    total = int(db.execute(total_statement).scalar_one())
    offset = (page - 1) * page_size

    statement = (
        select(
            loan_applications.c.loan_id,
            audit_evaluations.c.evaluated_at,
            audit_evaluations.c.risk_score,
            audit_evaluations.c.review_flag,
            audit_evaluations.c.decision,
            audit_evaluations.c.reasons,
        )
        .join(
            loan_applications,
            loan_applications.c.id == audit_evaluations.c.loan_application_id,
        )
        .where(audit_evaluations.c.review_flag == 1)
        .order_by(audit_evaluations.c.id.desc())
        .offset(offset)
        .limit(page_size)
    )

    rows = db.execute(statement).mappings().all()
    items = [
        AnalystQueueItem(
            loan_id=str(row["loan_id"]),
            evaluated_at=row["evaluated_at"],
            score=int(row["risk_score"]),
            flagged_for_review=bool(row["review_flag"]),
            approved=str(row["decision"]).lower() == "approved",
            reasons=_coerce_reasons(str(row["reasons"])),
        )
        for row in rows
    ]

    return AnalystQueueResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )
