"""Unit tests for pipeline performance logging in data_loader."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src import data_loader
from src.db.database import build_sqlite_url, create_db_engine, dispose_engine, initialize_database
from src.db.repositories import AuditRepository


def test_run_pipeline_exposes_performance_attrs_and_writes_log(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """run_pipeline should expose perf attrs and write one JSONL perf record."""

    input_df = pd.DataFrame(
        {
            "loan_id": ["L1", "L2"],
            "loan_status": ["Approved", "Denied"],
        }
    )

    monkeypatch.setattr(data_loader, "load_raw_data", lambda _path: input_df.copy())
    monkeypatch.setattr(data_loader, "clean_data", lambda df: df.copy())
    monkeypatch.setattr(data_loader, "rename_columns", lambda df: df.copy())
    monkeypatch.setattr(data_loader, "add_basic_features", lambda df: df.copy())
    monkeypatch.setattr(
        data_loader,
        "split_labels",
        lambda df: df.drop(columns=["loan_status"]).copy(),
    )
    monkeypatch.setattr(data_loader, "save_processed_data", lambda _df: None)

    performance_log_path = tmp_path / "audit" / "file_processing.jsonl"

    result_df = data_loader.run_pipeline(
        input_path="dummy.csv",
        performance_log_path=performance_log_path,
        audit_mode="jsonl",
    )

    assert "file_processing_seconds" in result_df.attrs
    assert "processed_rows_per_second" in result_df.attrs
    assert result_df.attrs["file_processing_seconds"] >= 0.0
    assert result_df.attrs["processed_rows_per_second"] >= 0.0

    lines = performance_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["mode"] == "pipeline_performance"
    assert record["input_path"] == "dummy.csv"
    assert record["processed_rows"] == 2
    assert record["file_processing_seconds"] >= 0.0
    assert record["processed_rows_per_second"] >= 0.0


def test_run_pipeline_dual_writes_performance_to_sql(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """run_pipeline should persist one SQL performance row when URL is provided."""

    input_df = pd.DataFrame(
        {
            "loan_id": ["L1", "L2"],
            "loan_status": ["Approved", "Denied"],
        }
    )

    monkeypatch.setattr(data_loader, "load_raw_data", lambda _path: input_df.copy())
    monkeypatch.setattr(data_loader, "clean_data", lambda df: df.copy())
    monkeypatch.setattr(data_loader, "rename_columns", lambda df: df.copy())
    monkeypatch.setattr(data_loader, "add_basic_features", lambda df: df.copy())
    monkeypatch.setattr(
        data_loader,
        "split_labels",
        lambda df: df.drop(columns=["loan_status"]).copy(),
    )
    monkeypatch.setattr(data_loader, "save_processed_data", lambda _df: None)

    db_path = tmp_path / "audit_pipeline.db"
    db_url = build_sqlite_url(db_path)

    result_df = data_loader.run_pipeline(
        input_path="dummy.csv",
        performance_log_path=None,
        sql_audit_database_url=db_url,
        audit_mode="sql",
    )

    assert "file_processing_seconds" in result_df.attrs
    assert "processed_rows_per_second" in result_df.attrs

    verify_engine = create_db_engine(database_url=db_url)
    initialize_database(verify_engine)
    try:
        audit_repository = AuditRepository(verify_engine)
        rows = audit_repository.list_data_loads(limit=5)

        assert len(rows) == 1
        assert rows[0]["filepath"] == "dummy.csv"
        assert rows[0]["processed_rows"] == 2
        assert rows[0]["file_processing_seconds"] >= 0.0
        assert rows[0]["rows_per_second"] >= 0.0
    finally:
        dispose_engine(verify_engine)
