"""Provide SQLAlchemy Core persistence helpers for audit artifacts.

This repository encapsulates insert and query operations for the audit tables:
`audit_evaluations`, `audit_rule_traces`, and `audit_data_loads`.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any

from sqlalchemy import Engine, insert, select

from src.bre_engine import DecisionResult
from src.bre_rules import RuleResult
from src.db.database import begin_connection
from src.db.schema import audit_data_loads, audit_evaluations, audit_rule_traces


class AuditRepository:
    """Persist and query decision evaluations plus traceability artifacts.

    Args:
        engine: SQLAlchemy engine used by repository operations.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def insert_evaluation(
        self,
        loan_application_id: int,
        decision: DecisionResult,
        mode: str,
        batch_id: str | None = None,
    ) -> int:
        """Insert one decision-evaluation record.

        Args:
            loan_application_id: Foreign key to `loan_applications.id`.
            decision: Final BRE decision with reasons and flags.
            mode: Evaluation mode (`single` or `batch`).
            batch_id: Optional batch identifier for grouped runs.

        Returns:
            Inserted primary key from `audit_evaluations`.
        """

        decision_label = "Approved" if decision.approved else "Denied"
        reasons_json = json.dumps(decision.reasons, ensure_ascii=True)

        payload = {
            "loan_application_id": loan_application_id,
            "decision": decision_label,
            "risk_score": decision.score,
            "hard_rejection": int(decision.hard_rejection),
            "review_flag": int(decision.flagged_for_review),
            "reasons": reasons_json,
            "mode": mode,
            "batch_id": batch_id,
        }

        with begin_connection(self._engine) as connection:
            result = connection.execute(insert(audit_evaluations).values(**payload))

        inserted_id = result.inserted_primary_key[0]
        if inserted_id is None:
            raise RuntimeError("Audit evaluation insert did not return a primary key.")

        return int(inserted_id)

    def insert_rule_traces(self, evaluation_id: int, rules: list[RuleResult]) -> int:
        """Insert rule-trace rows for one evaluation.

        Args:
            evaluation_id: Foreign key to `audit_evaluations.id`.
            rules: Ordered list of evaluated rule results.

        Returns:
            Number of inserted trace rows.
        """

        payloads: list[dict[str, Any]] = []
        for rule in rules:
            payloads.append(
                {
                    "evaluation_id": evaluation_id,
                    "rule_id": rule.rule_id,
                    "rule_type": rule.rule_type,
                    "criterion_ref": rule.criterion_ref,
                    "triggered": self._derive_triggered(rule),
                    "points": rule.points,
                    "reason": rule.reason,
                }
            )

        if not payloads:
            return 0

        with begin_connection(self._engine) as connection:
            connection.execute(insert(audit_rule_traces), payloads)

        return len(payloads)

    def insert_data_load(
        self,
        filepath: str,
        processed_rows: int,
        file_processing_seconds: float,
        rows_per_second: float,
    ) -> int:
        """Insert one data-load performance record.

        Args:
            filepath: Source file path processed by the pipeline.
            processed_rows: Number of processed rows.
            file_processing_seconds: End-to-end processing time.
            rows_per_second: Throughput metric over processing interval.

        Returns:
            Inserted primary key from `audit_data_loads`.
        """

        payload = {
            "filepath": filepath,
            "processed_rows": processed_rows,
            "file_processing_seconds": file_processing_seconds,
            "rows_per_second": rows_per_second,
        }

        with begin_connection(self._engine) as connection:
            result = connection.execute(insert(audit_data_loads).values(**payload))

        inserted_id = result.inserted_primary_key[0]
        if inserted_id is None:
            raise RuntimeError("Audit data-load insert did not return a primary key.")

        return int(inserted_id)

    def list_rule_traces(self, evaluation_id: int) -> list[dict[str, Any]]:
        """List persisted rule traces for one evaluation.

        Args:
            evaluation_id: Foreign key to `audit_evaluations.id`.

        Returns:
            Ordered list of rule-trace rows.
        """

        statement = (
            select(audit_rule_traces)
            .where(audit_rule_traces.c.evaluation_id == evaluation_id)
            .order_by(audit_rule_traces.c.id.asc())
        )

        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        return [dict(row) for row in rows]

    def list_evaluations_for_application(
        self,
        loan_application_id: int,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List evaluations for one loan application ordered by recency.

        Args:
            loan_application_id: Foreign key to `loan_applications.id`.
            limit: Maximum number of rows to return.

        Returns:
            Ordered list of evaluation rows.
        """

        effective_limit = max(limit, 1)
        statement = (
            select(audit_evaluations)
            .where(audit_evaluations.c.loan_application_id == loan_application_id)
            .order_by(audit_evaluations.c.id.desc())
            .limit(effective_limit)
        )

        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        return [dict(row) for row in rows]

    def list_data_loads(self, limit: int = 100) -> list[dict[str, Any]]:
        """List recent data-load performance records.

        Args:
            limit: Maximum number of rows to return.

        Returns:
            Ordered list of data-load rows.
        """

        effective_limit = max(limit, 1)
        statement = (
            select(audit_data_loads)
            .order_by(audit_data_loads.c.id.desc())
            .limit(effective_limit)
        )

        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        return [dict(row) for row in rows]

    def build_trace_payload(self, rule: RuleResult) -> dict[str, Any]:
        """Build a serialized trace payload for external audit consumers.

        Args:
            rule: Rule result object to serialize.

        Returns:
            Dictionary with serialized rule payload and derived trigger flag.
        """

        payload = asdict(rule)
        payload["triggered"] = self._derive_triggered(rule)
        return payload

    @staticmethod
    def _derive_triggered(rule: RuleResult) -> int:
        """Derive triggered flag aligned with hard/soft rule semantics.

        Args:
            rule: Rule result object from BRE execution.

        Returns:
            Integer flag (0 or 1) indicating whether the rule was triggered.
        """

        if rule.rule_type == "hard":
            return int(not rule.passed)

        return int(rule.points != 0)
