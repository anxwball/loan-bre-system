"""Unit tests for SQLAlchemy Core repository implementations."""

from __future__ import annotations

from pathlib import Path

from src.db.database import (
    build_sqlite_url,
    create_db_engine,
    dispose_engine,
    initialize_database,
)
from src.db.repositories.audit_repo import AuditRepository
from src.db.repositories.loan_repo import LoanRepository


def _build_test_engine(tmp_path: Path):
    """Create an isolated SQLite engine with initialized schema for testing."""

    db_path = tmp_path / "test_phase4b.db"
    engine = create_db_engine(database_url=build_sqlite_url(db_path))
    initialize_database(engine)
    return engine


def test_loan_repository_inserts_and_fetches_application(tmp_path: Path, build_application) -> None:
    """LoanRepository should persist one application and retrieve it by loan_id."""

    db_engine = _build_test_engine(tmp_path)

    try:
        repo = LoanRepository(db_engine)
        app = build_application(loan_id="LP_REPO_001")

        inserted_id = repo.insert_application(
            app=app,
            applicant_id="APPLICANT_001",
            source_file="data/processed/loans_cleaned.csv",
        )

        fetched = repo.get_by_loan_id("LP_REPO_001")

        assert inserted_id > 0
        assert fetched is not None
        assert fetched["id"] == inserted_id
        assert fetched["loan_id"] == "LP_REPO_001"
        assert fetched["applicant_id"] == "APPLICANT_001"
        assert fetched["source_file"] == "data/processed/loans_cleaned.csv"
    finally:
        dispose_engine(db_engine)


def test_audit_repository_persists_evaluation_and_rule_traces(
    tmp_path: Path,
    build_application,
    engine,
) -> None:
    """AuditRepository should persist decision rows and aligned rule traces."""

    db_engine = _build_test_engine(tmp_path)

    try:
        loan_repo = LoanRepository(db_engine)
        audit_repo = AuditRepository(db_engine)

        app = build_application(loan_id="LP_REPO_002")
        loan_application_id = loan_repo.insert_application(app=app, applicant_id="APPLICANT_002")

        decision = engine.evaluate(app)
        evaluation_id = audit_repo.insert_evaluation(
            loan_application_id=loan_application_id,
            decision=decision,
            mode="single",
        )
        inserted_trace_count = audit_repo.insert_rule_traces(
            evaluation_id=evaluation_id,
            rules=decision.rules_triggered,
        )

        evaluations = audit_repo.list_evaluations_for_application(loan_application_id)
        traces = audit_repo.list_rule_traces(evaluation_id)

        assert evaluation_id > 0
        assert inserted_trace_count == len(decision.rules_triggered)
        assert len(evaluations) == 1
        assert evaluations[0]["id"] == evaluation_id
        assert evaluations[0]["mode"] == "single"
        assert evaluations[0]["decision"] in {"Approved", "Denied"}
        assert len(traces) == len(decision.rules_triggered)
        assert {trace["rule_type"] for trace in traces}.issubset({"hard", "soft"})
    finally:
        dispose_engine(db_engine)


def test_audit_repository_persists_data_load_records(tmp_path: Path) -> None:
    """AuditRepository should persist and list data-load performance rows."""

    db_engine = _build_test_engine(tmp_path)

    try:
        audit_repo = AuditRepository(db_engine)

        inserted_id = audit_repo.insert_data_load(
            filepath="data/raw/loan_train.csv",
            processed_rows=614,
            file_processing_seconds=1.25,
            rows_per_second=491.2,
        )
        rows = audit_repo.list_data_loads(limit=5)

        assert inserted_id > 0
        assert len(rows) == 1
        assert rows[0]["id"] == inserted_id
        assert rows[0]["filepath"] == "data/raw/loan_train.csv"
        assert rows[0]["processed_rows"] == 614
    finally:
        dispose_engine(db_engine)
