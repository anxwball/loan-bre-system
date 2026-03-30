"""Unit tests for JSONL audit persistence utilities."""

from __future__ import annotations

import json
from pathlib import Path

from src.audit_logger import (
    append_jsonl_record,
    build_versioned_batch_audit_path,
    log_decision_jsonl,
)


def test_append_jsonl_record_creates_directory_and_writes_line(tmp_path: Path) -> None:
    """append_jsonl_record should create directories and persist one JSON line."""

    output_path = tmp_path / "audit" / "records.jsonl"
    record = {"k": "v", "n": 1}

    created = append_jsonl_record(record, output_path)

    assert created == output_path.resolve()
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == record


def test_append_jsonl_record_appends_multiple_entries(tmp_path: Path) -> None:
    """append_jsonl_record should append and preserve each line independently."""

    output_path = tmp_path / "audit" / "records.jsonl"

    append_jsonl_record({"id": "one"}, output_path)
    append_jsonl_record({"id": "two"}, output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"id": "one"}
    assert json.loads(lines[1]) == {"id": "two"}


def test_log_decision_jsonl_persists_minimum_required_fields(
    tmp_path: Path,
    engine,
    build_application,
) -> None:
    """High-level logger should persist deterministic audit fields."""

    app = build_application()
    decision = engine.evaluate(app)
    output_path = tmp_path / "decision_explanations.jsonl"

    created = log_decision_jsonl(
        app=app,
        decision=decision,
        output_path=output_path,
        model_version="bre-v1",
    )

    assert created == output_path.resolve()
    payload = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])

    assert payload["applicant_id"] == app.loan_id
    assert payload["approved"] == decision.approved
    assert payload["score"] == decision.score
    assert payload["hard_rejection"] == decision.hard_rejection
    assert payload["model_version"] == "bre-v1"
    assert payload["audit_storage"] == "jsonl"
    assert isinstance(payload["rules_triggered"], list)
    assert payload["rules_triggered"]


def test_build_versioned_batch_audit_path_creates_versioned_filename(tmp_path: Path) -> None:
    """Versioned batch path helper should create directory and return jsonl filename."""

    path = build_versioned_batch_audit_path(output_dir=tmp_path, prefix="batch_decisions")

    assert path.parent == tmp_path
    assert path.name.startswith("batch_decisions_")
    assert path.suffix == ".jsonl"
