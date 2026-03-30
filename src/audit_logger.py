"""Persist BRE decision audit records using JSON Lines format.

This module provides lightweight local persistence for auditability while the
project is still deciding its long-term storage destination.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.bre_engine import DecisionResult
from src.loan_application import LoanApplication


DEFAULT_AUDIT_JSONL_PATH = Path("data/audit/decisions_latest.jsonl")
DEFAULT_BATCH_AUDIT_DIR = Path("data/audit/batch")


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
) -> dict[str, Any]:
    """Build a JSON-serializable audit record for one BRE decision.

    Args:
        app: Loan application evaluated by the engine.
        decision: Final decision returned by RuleEngine.
        model_version: Version string for the decisioning logic.

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
        "audit_storage": "jsonl",
    }


def log_decision_jsonl(
    app: LoanApplication,
    decision: DecisionResult,
    output_path: Path = DEFAULT_AUDIT_JSONL_PATH,
    model_version: str = "bre-v1",
) -> Path:
    """Build and persist a complete decision audit record.

    Args:
        app: Loan application evaluated by the engine.
        decision: Final decision returned by RuleEngine.
        output_path: Destination .jsonl path.
        model_version: Version string for the decisioning logic.

    Returns:
        Resolved path of the persisted .jsonl file.
    """

    audit_record = build_decision_audit_record(
        app=app,
        decision=decision,
        model_version=model_version,
    )
    return append_jsonl_record(audit_record, output_path)
