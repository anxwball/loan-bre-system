"""Unit tests for batch BRE evaluation against historical labels."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.batch_evaluator import evaluate_batch_against_baseline


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    """Write helper CSV files for deterministic test scenarios."""

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_batch_evaluation_computes_expected_metrics(tmp_path: Path) -> None:
    """Batch evaluator should compute metrics, confusion counts, and output rows."""

    features_path = tmp_path / "features.csv"
    labels_path = tmp_path / "labels.csv"
    output_path = tmp_path / "batch_output.csv"

    feature_fieldnames = [
        "loan_id",
        "gender",
        "married",
        "dependents",
        "education",
        "self_employed",
        "applicant_income",
        "coapplicant_income",
        "loan_amount",
        "loan_amount_term",
        "credit_history",
        "property_area",
    ]
    label_fieldnames = ["loan_id", "loan_status"]

    _write_csv(
        features_path,
        rows=[
            {
                "loan_id": "L1",
                "gender": "Male",
                "married": "No",
                "dependents": "0",
                "education": "Graduate",
                "self_employed": "No",
                "applicant_income": 5000,
                "coapplicant_income": 0,
                "loan_amount": 100,
                "loan_amount_term": 360,
                "credit_history": 1,
                "property_area": "Urban",
            },
            {
                "loan_id": "L2",
                "gender": "Male",
                "married": "No",
                "dependents": "0",
                "education": "Graduate",
                "self_employed": "No",
                "applicant_income": 5000,
                "coapplicant_income": 0,
                "loan_amount": 100,
                "loan_amount_term": 360,
                "credit_history": 0,
                "property_area": "Urban",
            },
            {
                "loan_id": "L3",
                "gender": "Male",
                "married": "No",
                "dependents": "0",
                "education": "Graduate",
                "self_employed": "No",
                "applicant_income": 5000,
                "coapplicant_income": 0,
                "loan_amount": 0,
                "loan_amount_term": 360,
                "credit_history": 1,
                "property_area": "Urban",
            },
            {
                "loan_id": "L4",
                "gender": "Male",
                "married": "No",
                "dependents": "0",
                "education": "Graduate",
                "self_employed": "No",
                "applicant_income": 5000,
                "coapplicant_income": 0,
                "loan_amount": 100,
                "loan_amount_term": 360,
                "credit_history": 1,
                "property_area": "Urban",
            },
        ],
        fieldnames=feature_fieldnames,
    )
    _write_csv(
        labels_path,
        rows=[
            {"loan_id": "L1", "loan_status": "Approved"},
            {"loan_id": "L2", "loan_status": "Denied"},
            {"loan_id": "L3", "loan_status": "Approved"},
        ],
        fieldnames=label_fieldnames,
    )

    summary = evaluate_batch_against_baseline(
        features_path=features_path,
        labels_path=labels_path,
        output_path=output_path,
    )

    assert summary.total_feature_rows == 4
    assert summary.compared_rows == 2
    assert summary.missing_label_rows == 1
    assert summary.invalid_row_rows == 1
    assert summary.matched_rows == 2
    assert summary.mismatched_rows == 0
    assert summary.predicted_approved_actual_approved == 1
    assert summary.predicted_denied_actual_denied == 1
    assert summary.predicted_approved_actual_denied == 0
    assert summary.predicted_denied_actual_approved == 0
    assert summary.accuracy == 1.0
    assert summary.file_processing_seconds >= 0.0
    assert summary.compared_rows_per_second >= 0.0

    with output_path.open("r", newline="", encoding="utf-8") as output_file:
        rows = list(csv.DictReader(output_file))

    assert len(rows) == 2
    assert {row["loan_id"] for row in rows} == {"L1", "L2"}


def test_batch_evaluation_writes_jsonl_audit_when_path_is_provided(tmp_path: Path) -> None:
    """Batch evaluator should append one audit record per compared row."""

    features_path = tmp_path / "features.csv"
    labels_path = tmp_path / "labels.csv"
    batch_audit_path = tmp_path / "audit" / "batch_records.jsonl"

    feature_fieldnames = [
        "loan_id",
        "gender",
        "married",
        "dependents",
        "education",
        "self_employed",
        "applicant_income",
        "coapplicant_income",
        "loan_amount",
        "loan_amount_term",
        "credit_history",
        "property_area",
    ]
    label_fieldnames = ["loan_id", "loan_status"]

    _write_csv(
        features_path,
        rows=[
            {
                "loan_id": "L1",
                "gender": "Male",
                "married": "No",
                "dependents": "0",
                "education": "Graduate",
                "self_employed": "No",
                "applicant_income": 5000,
                "coapplicant_income": 0,
                "loan_amount": 100,
                "loan_amount_term": 360,
                "credit_history": 1,
                "property_area": "Urban",
            }
        ],
        fieldnames=feature_fieldnames,
    )
    _write_csv(
        labels_path,
        rows=[{"loan_id": "L1", "loan_status": "Approved"}],
        fieldnames=label_fieldnames,
    )

    summary = evaluate_batch_against_baseline(
        features_path=features_path,
        labels_path=labels_path,
        output_path=None,
        batch_audit_path=batch_audit_path,
    )

    assert summary.compared_rows == 1
    assert summary.file_processing_seconds >= 0.0
    assert summary.compared_rows_per_second >= 0.0
    lines = batch_audit_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    record = json.loads(lines[0])
    assert record["mode"] == "batch"
    assert record["applicant_id"] == "L1"
    assert record["predicted_status"] == "Approved"
    assert record["baseline_status"] == "Approved"
    assert record["matched"] is True

    performance_record = json.loads(lines[1])
    assert performance_record["mode"] == "batch_performance"
    assert performance_record["compared_rows"] == 1
    assert performance_record["file_processing_seconds"] >= 0.0
    assert performance_record["compared_rows_per_second"] >= 0.0
