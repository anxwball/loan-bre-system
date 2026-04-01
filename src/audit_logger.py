"""Persist BRE decision audit records with JSONL-first dual-write support.

This module keeps JSONL persistence as the compatibility baseline and can
optionally dual-write single-decision audit records to the SQL persistence
layer introduced in Phase 4b.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.bre_engine import DecisionResult
from src.db.database import create_db_engine, dispose_engine, initialize_database
from src.db.repositories import AuditRepository, LoanRepository
from src.loan_application import LoanApplication


DEFAULT_AUDIT_JSONL_PATH = Path("data/audit/decisions_latest.jsonl")
DEFAULT_BATCH_AUDIT_DIR = Path("data/audit/batch")
SUPPORTED_AUDIT_MODES = {"sql", "dual", "jsonl"}


def build_versioned_batch_audit_path(
    output_dir: Path = DEFAULT_BATCH_AUDIT_DIR,
    prefix: str = "batch_decisions",
) -> Path:
    """Build a timestamped output path for batch audit logs.

    Args:
        output_dir: Directory where batch audit files are stored.
        prefix: File name prefix for batch artifacts.

    Returns:
        Versioned jsonl file path.
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    directory = output_dir
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{prefix}_{timestamp}.jsonl"


def append_jsonl_record(record: dict[str, Any], output_path: Path) -> Path:
    """Append one JSON-serializable record to a .jsonl file.

    Args:
        record: Dictionary payload to persist.
        output_path: Destination .jsonl path.

    Returns:
        Resolved path of the written jsonl file.

    Raises:
        ValueError: If record cannot be serialized to JSON.
    """

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        line = json.dumps(record, ensure_ascii=True)
    except TypeError as exc:
        raise ValueError("Audit record must be JSON-serializable.") from exc

    with destination.open("a", encoding="utf-8") as file_handle:
        file_handle.write(f"{line}\n")

    return destination.resolve()


def build_decision_audit_record(
    app: LoanApplication,
    decision: DecisionResult,
    model_version: str = "bre-v1",
    audit_storage: str = "jsonl",
) -> dict[str, Any]:
    """Build a JSON-serializable audit record for one BRE decision.

    Args:
        app: Loan application evaluated by the engine.
        decision: Final decision returned by RuleEngine.
        model_version: Version string for the decisioning logic.
        audit_storage: Storage descriptor used by downstream audit consumers.

    Returns:
        Dictionary aligned with minimum audit requirements.
    """

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "applicant_id": app.loan_id,
        "approved": decision.approved,
        "score": decision.score,
        "hard_rejection": decision.hard_rejection,
        "flagged_for_review": decision.flagged_for_review,
        "summary": decision.summary(),
        "rules_triggered": [asdict(rule) for rule in decision.rules_triggered],
        "model_version": model_version,
        "audit_storage": audit_storage,
    }


def _resolve_audit_mode(audit_mode: str | None, default_mode: str) -> str:
    """Resolve and validate audit mode for runtime persistence.

    Args:
        audit_mode: Optional explicit runtime audit mode.
        default_mode: Default mode used when `audit_mode` is None.

    Returns:
        Effective audit mode (`sql`, `dual`, or `jsonl`).

    Raises:
        ValueError: If mode is not supported.
    """

    effective_mode = default_mode if audit_mode is None else audit_mode.strip().lower()
    if effective_mode not in SUPPORTED_AUDIT_MODES:
        raise ValueError(
            f"Unsupported audit_mode: {audit_mode!r}. "
            f"Expected one of {sorted(SUPPORTED_AUDIT_MODES)}."
        )

    return effective_mode


def _resolve_storage_label(persist_jsonl: bool, persist_sql: bool) -> str:
    """Resolve storage label from effective sink toggles.

    Args:
        persist_jsonl: Whether JSONL persistence is enabled.
        persist_sql: Whether SQL persistence is enabled.

    Returns:
        Storage label used in audit payloads.
    """

    if persist_jsonl and persist_sql:
        return "jsonl+sql"
    if persist_jsonl:
        return "jsonl"
    return "sql"


def _persist_decision_sql(
    app: LoanApplication,
    decision: DecisionResult,
    sql_audit_database_url: str | None,
    applicant_id: str,
) -> None:
    """Persist one single-decision audit flow to SQL repositories.

    Args:
        app: Loan application evaluated by the engine.
        decision: Final decision returned by RuleEngine.
        sql_audit_database_url: Optional SQLAlchemy database URL for audit
            persistence. If omitted, the default database configuration is used.
        applicant_id: Stable applicant identifier for persistence rows.

    Returns:
        None.
    """

    sql_engine = create_db_engine(database_url=sql_audit_database_url)
    initialize_database(sql_engine)
    try:
        loan_repository = LoanRepository(sql_engine)
        audit_repository = AuditRepository(sql_engine)

        persisted_loan = loan_repository.get_by_loan_id(app.loan_id)
        if persisted_loan is None:
            loan_application_id = loan_repository.insert_application(
                app=app,
                applicant_id=applicant_id,
                source_file=None,
                loan_status=None,
            )
        else:
            loan_application_id = int(persisted_loan["id"])

        evaluation_id = audit_repository.insert_evaluation(
            loan_application_id=loan_application_id,
            decision=decision,
            mode="single",
        )
        audit_repository.insert_rule_traces(
            evaluation_id=evaluation_id,
            rules=decision.rules_triggered,
        )
    finally:
        dispose_engine(sql_engine)


def log_decision_audit(
    app: LoanApplication,
    decision: DecisionResult,
    output_path: Path = DEFAULT_AUDIT_JSONL_PATH,
    model_version: str = "bre-v1",
    sql_audit_database_url: str | None = None,
    applicant_id: str | None = None,
    audit_mode: str | None = None,
) -> dict[str, Any]:
    """Persist one decision audit using policy-driven sink selection.

    Args:
        app: Loan application evaluated by the engine.
        decision: Final decision returned by RuleEngine.
        output_path: Destination .jsonl path for jsonl/dual modes.
        model_version: Version string for the decisioning logic.
        sql_audit_database_url: Optional SQLAlchemy URL for SQL persistence.
        applicant_id: Optional applicant identifier for SQL rows.
        audit_mode: Optional sink policy (`sql`, `dual`, `jsonl`). Defaults to
            `sql` for cutoff progression.

    Returns:
        Dictionary with effective mode and persistence outcomes.
    """

    effective_mode = _resolve_audit_mode(audit_mode, default_mode="sql")
    persist_jsonl = effective_mode in {"dual", "jsonl"}
    persist_sql = effective_mode in {"dual", "sql"}
    storage_label = _resolve_storage_label(
        persist_jsonl=persist_jsonl,
        persist_sql=persist_sql,
    )

    persisted_path: Path | None = None
    if persist_jsonl:
        audit_record = build_decision_audit_record(
            app=app,
            decision=decision,
            model_version=model_version,
            audit_storage=storage_label,
        )
        persisted_path = append_jsonl_record(audit_record, output_path)

    if persist_sql:
        resolved_applicant_id = applicant_id if applicant_id is not None else app.loan_id
        _persist_decision_sql(
            app=app,
            decision=decision,
            sql_audit_database_url=sql_audit_database_url,
            applicant_id=resolved_applicant_id,
        )

    return {
        "audit_mode": effective_mode,
        "jsonl_path": str(persisted_path) if persisted_path is not None else None,
        "sql_persisted": persist_sql,
    }


def log_decision_jsonl(
    app: LoanApplication,
    decision: DecisionResult,
    output_path: Path = DEFAULT_AUDIT_JSONL_PATH,
    model_version: str = "bre-v1",
    sql_audit_database_url: str | None = None,
    applicant_id: str | None = None,
) -> Path:
    """Build and persist a complete decision audit record.

    Args:
        app: Loan application evaluated by the engine.
        decision: Final decision returned by RuleEngine.
        output_path: Destination .jsonl path.
        model_version: Version string for the decisioning logic.
        sql_audit_database_url: Optional SQLAlchemy URL used to dual-write
            single-decision audit rows into SQL persistence.
        applicant_id: Optional applicant identifier for SQL persistence rows.

    Returns:
        Resolved path of the persisted .jsonl file.
    """

    effective_mode = "dual" if sql_audit_database_url is not None else "jsonl"
    result = log_decision_audit(
        app=app,
        decision=decision,
        output_path=output_path,
        model_version=model_version,
        sql_audit_database_url=sql_audit_database_url,
        applicant_id=applicant_id,
        audit_mode=effective_mode,
    )

    jsonl_path = result["jsonl_path"]
    if jsonl_path is None:
        raise RuntimeError("log_decision_jsonl expected JSONL persistence but no path was generated.")

    return Path(jsonl_path)
