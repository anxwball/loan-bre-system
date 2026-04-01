"""Unit tests for JSONL audit persistence utilities."""

from __future__ import annotations

import json
from pathlib import Path

from src.db.database import build_sqlite_url, create_db_engine, dispose_engine, initialize_database
from src.db.repositories import AuditRepository, LoanRepository
from src.audit_logger import (
    append_jsonl_record,
    build_versioned_batch_audit_path,
    log_decision_audit,
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


def test_log_decision_jsonl_dual_writes_to_sql(
    tmp_path: Path,
    engine,
    build_application,
) -> None:
    """Logger should persist single-decision rows in JSONL and SQL when configured."""

    app = build_application(loan_id="LP_SINGLE_SQL_001")
    decision = engine.evaluate(app)
    output_path = tmp_path / "decision_explanations.jsonl"
    db_path = tmp_path / "audit_single.db"
    db_url = build_sqlite_url(db_path)

    created = log_decision_jsonl(
        app=app,
        decision=decision,
        output_path=output_path,
        model_version="bre-v1",
        sql_audit_database_url=db_url,
    )

    assert created == output_path.resolve()
    payload = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["audit_storage"] == "jsonl+sql"

    verify_engine = create_db_engine(database_url=db_url)
    initialize_database(verify_engine)
    try:
        loan_repository = LoanRepository(verify_engine)
        audit_repository = AuditRepository(verify_engine)

        loan_row = loan_repository.get_by_loan_id("LP_SINGLE_SQL_001")
        assert loan_row is not None

        evaluations = audit_repository.list_evaluations_for_application(int(loan_row["id"]))
        assert len(evaluations) == 1
        assert evaluations[0]["mode"] == "single"

        traces = audit_repository.list_rule_traces(int(evaluations[0]["id"]))
        assert len(traces) == len(decision.rules_triggered)
    finally:
        dispose_engine(verify_engine)


def test_log_decision_audit_defaults_to_sql_mode(
    tmp_path: Path,
    engine,
    build_application,
) -> None:
    """Policy entrypoint should persist SQL by default without writing JSONL."""

    app = build_application(loan_id="LP_SINGLE_SQL_DEFAULT")
    decision = engine.evaluate(app)
    output_path = tmp_path / "decision_explanations.jsonl"
    db_path = tmp_path / "audit_single_default.db"
    db_url = build_sqlite_url(db_path)

    result = log_decision_audit(
        app=app,
        decision=decision,
        output_path=output_path,
        sql_audit_database_url=db_url,
    )

    assert result["audit_mode"] == "sql"
    assert result["sql_persisted"] is True
    assert result["jsonl_path"] is None
    assert output_path.exists() is False

    verify_engine = create_db_engine(database_url=db_url)
    initialize_database(verify_engine)
    try:
        loan_repository = LoanRepository(verify_engine)
        audit_repository = AuditRepository(verify_engine)

        loan_row = loan_repository.get_by_loan_id("LP_SINGLE_SQL_DEFAULT")
        assert loan_row is not None

        evaluations = audit_repository.list_evaluations_for_application(int(loan_row["id"]))
        assert len(evaluations) == 1
        assert evaluations[0]["mode"] == "single"
    finally:
        dispose_engine(verify_engine)
