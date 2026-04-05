"""Define output contracts for evaluation, audit, and queue endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RuleTraceResponse(BaseModel):
    """Represent one rule-level trace in API responses."""

    rule_id: str
    name: str
    criterion_ref: str
    rule_type: str
    passed: bool
    points: int
    reason: str


class DecisionResponse(BaseModel):
    """Represent one normalized decision payload."""

    approved: bool
    score: int
    hard_rejection: bool
    flagged_for_review: bool
    summary: str
    reasons: list[str]
    rule_traces: list[RuleTraceResponse]


class EvaluationResponse(BaseModel):
    """Represent one evaluated loan record."""

    loan_id: str
    evaluated_at: datetime
    decision: DecisionResponse


class BatchSummary(BaseModel):
    """Represent aggregate metrics for a batch evaluation run."""

    total: int
    approved: int
    denied: int
    flagged_for_review: int
    hard_rejections: int
    avg_score: float


class BatchEvaluationResponse(BaseModel):
    """Represent full batch evaluation output."""

    evaluated_at: datetime
    summary: BatchSummary
    results: list[EvaluationResponse]


class AuditEvaluationRecord(BaseModel):
    """Represent one persisted evaluation row from audit storage."""

    evaluation_id: int
    loan_id: str
    evaluated_at: datetime
    approved: bool
    score: int
    hard_rejection: bool
    flagged_for_review: bool
    rule_traces: list[RuleTraceResponse] | None = None


class AuditEvaluationPage(BaseModel):
    """Represent paginated audit evaluation results."""

    total: int
    page: int
    page_size: int
    items: list[AuditEvaluationRecord]


class AnalystQueueItem(BaseModel):
    """Represent one analyst queue item without full trace details."""

    loan_id: str
    evaluated_at: datetime
    score: int
    flagged_for_review: bool
    approved: bool
    reasons: list[str]


class AnalystQueueResponse(BaseModel):
    """Represent paginated analyst queue response."""

    total: int
    page: int
    page_size: int
    items: list[AnalystQueueItem]
