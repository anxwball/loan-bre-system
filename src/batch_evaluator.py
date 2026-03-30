"""Run deterministic BRE batch evaluation against a historical baseline.

This module evaluates cleaned feature rows with the RuleEngine and compares
predicted decisions against baseline labels (`Approved`/`Denied`). It returns
aggregate metrics and can optionally persist row-level comparison output.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from src.audit_logger import (
    append_jsonl_record,
    build_decision_audit_record,
    build_versioned_batch_audit_path,
)
from src.bre_engine import RuleEngine
from src.loan_application import LoanApplication


DEFAULT_FEATURES_PATH = Path("data/processed/loans_cleaned.csv")
DEFAULT_LABELS_PATH = Path("data/processed/loan_labels.csv")
DEFAULT_OUTPUT_PATH = Path("data/processed/batch_evaluation_latest.csv")


@dataclass(frozen=True)
class BatchEvaluationSummary:
    """Represent aggregate metrics for a batch BRE-vs-baseline run.

    Args:
        total_feature_rows: Rows read from feature input.
        compared_rows: Rows successfully compared against baseline labels.
        missing_label_rows: Feature rows without baseline label.
        invalid_row_rows: Rows rejected before decision because of invalid data.
        matched_rows: Rows where prediction matches baseline label.
        mismatched_rows: Rows where prediction differs from baseline label.
        predicted_approved_actual_approved: True positives for approved class.
        predicted_approved_actual_denied: False positives for approved class.
        predicted_denied_actual_approved: False negatives for approved class.
        predicted_denied_actual_denied: True negatives for approved class.
        accuracy: Match ratio in [0, 1] over compared rows.
        file_processing_seconds: End-to-end file processing duration in seconds.
        compared_rows_per_second: Compared-row throughput over processing duration.
    """

    total_feature_rows: int
    compared_rows: int
    missing_label_rows: int
    invalid_row_rows: int
    matched_rows: int
    mismatched_rows: int
    predicted_approved_actual_approved: int
    predicted_approved_actual_denied: int
    predicted_denied_actual_approved: int
    predicted_denied_actual_denied: int
    accuracy: float
    file_processing_seconds: float
    compared_rows_per_second: float


def _normalize_label(raw_label: str) -> str:
    """Normalize baseline labels to canonical values.

    Args:
        raw_label: Label value from input file.

    Returns:
        Canonical label (`Approved` or `Denied`).

    Raises:
        ValueError: If the label cannot be normalized.
    """

    normalized = raw_label.strip().lower()
    if normalized in {"approved", "approve", "a", "1", "true", "yes", "y"}:
        return "Approved"
    if normalized in {"denied", "deny", "rejected", "reject", "d", "0", "false", "no", "n"}:
        return "Denied"
    raise ValueError(f"Unsupported label value: {raw_label!r}")


def _coerce_row_to_application(row: dict[str, str]) -> LoanApplication:
    """Cast one cleaned feature row into a LoanApplication object.

    Args:
        row: Raw CSV row keyed by cleaned feature schema.

    Returns:
        Validated LoanApplication instance.
    """

    return LoanApplication(
        loan_id=row["loan_id"],
        gender=row["gender"],
        married=row["married"],
        dependents=row["dependents"],
        education=row["education"],
        self_employed=row["self_employed"],
        applicant_income=float(row["applicant_income"]),
        coapplicant_income=float(row["coapplicant_income"]),
        loan_amount=float(row["loan_amount"]),
        loan_amount_term=float(row["loan_amount_term"]),
        credit_history=int(float(row["credit_history"])),
        property_area=row["property_area"],
    )


def _load_labels(labels_path: Path) -> dict[str, str]:
    """Load baseline labels keyed by loan_id.

    Args:
        labels_path: CSV path with columns `loan_id` and `loan_status`.

    Returns:
        Mapping from loan_id to canonical label.
    """

    labels_by_id: dict[str, str] = {}
    with labels_path.open("r", newline="", encoding="utf-8") as labels_file:
        reader = csv.DictReader(labels_file)
        for row in reader:
            labels_by_id[row["loan_id"]] = _normalize_label(row["loan_status"])
    return labels_by_id


def evaluate_batch_against_baseline(
    features_path: Path = DEFAULT_FEATURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    output_path: Path | None = DEFAULT_OUTPUT_PATH,
    batch_audit_path: Path | None = None,
) -> BatchEvaluationSummary:
    """Evaluate all features and compare BRE decisions against baseline labels.

    Args:
        features_path: Cleaned feature CSV path.
        labels_path: Baseline label CSV path.
        output_path: Optional destination for row-level comparison output.
        batch_audit_path: Optional destination for line-delimited audit records.

    Returns:
        BatchEvaluationSummary with aggregate evaluation metrics.
    """

    labels_by_id = _load_labels(labels_path)

    engine = RuleEngine()

    total_feature_rows = 0
    compared_rows = 0
    missing_label_rows = 0
    invalid_row_rows = 0
    matched_rows = 0
    mismatched_rows = 0
    predicted_approved_actual_approved = 0
    predicted_approved_actual_denied = 0
    predicted_denied_actual_approved = 0
    predicted_denied_actual_denied = 0

    output_rows: list[dict[str, object]] = []
    processing_start = perf_counter()

    with features_path.open("r", newline="", encoding="utf-8") as features_file:
        reader = csv.DictReader(features_file)
        for row in reader:
            total_feature_rows += 1
            loan_id = row["loan_id"]
            baseline_label = labels_by_id.get(loan_id)
            if baseline_label is None:
                missing_label_rows += 1
                continue

            try:
                app = _coerce_row_to_application(row)
                decision = engine.evaluate(app)
            except (ValueError, KeyError):
                invalid_row_rows += 1
                continue

            predicted_label = "Approved" if decision.approved else "Denied"

            compared_rows += 1
            is_match = predicted_label == baseline_label
            if is_match:
                matched_rows += 1
            else:
                mismatched_rows += 1

            if predicted_label == "Approved" and baseline_label == "Approved":
                predicted_approved_actual_approved += 1
            elif predicted_label == "Approved" and baseline_label == "Denied":
                predicted_approved_actual_denied += 1
            elif predicted_label == "Denied" and baseline_label == "Approved":
                predicted_denied_actual_approved += 1
            else:
                predicted_denied_actual_denied += 1

            output_rows.append(
                {
                    "loan_id": loan_id,
                    "predicted_status": predicted_label,
                    "baseline_status": baseline_label,
                    "matched": is_match,
                    "score": decision.score,
                    "hard_rejection": decision.hard_rejection,
                    "flagged_for_review": decision.flagged_for_review,
                    "decision_summary": decision.summary(),
                }
            )

            if batch_audit_path is not None:
                audit_record = build_decision_audit_record(app=app, decision=decision)
                audit_record["mode"] = "batch"
                audit_record["predicted_status"] = predicted_label
                audit_record["baseline_status"] = baseline_label
                audit_record["matched"] = is_match
                append_jsonl_record(audit_record, batch_audit_path)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as output_file:
            fieldnames = [
                "loan_id",
                "predicted_status",
                "baseline_status",
                "matched",
                "score",
                "hard_rejection",
                "flagged_for_review",
                "decision_summary",
            ]
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)

    accuracy = matched_rows / compared_rows if compared_rows > 0 else 0.0
    file_processing_seconds = perf_counter() - processing_start
    compared_rows_per_second = (
        compared_rows / file_processing_seconds if file_processing_seconds > 0 else 0.0
    )

    if batch_audit_path is not None:
        append_jsonl_record(
            {
                "mode": "batch_performance",
                "features_path": str(features_path),
                "labels_path": str(labels_path),
                "compared_rows": compared_rows,
                "total_feature_rows": total_feature_rows,
                "file_processing_seconds": file_processing_seconds,
                "compared_rows_per_second": compared_rows_per_second,
            },
            batch_audit_path,
        )

    return BatchEvaluationSummary(
        total_feature_rows=total_feature_rows,
        compared_rows=compared_rows,
        missing_label_rows=missing_label_rows,
        invalid_row_rows=invalid_row_rows,
        matched_rows=matched_rows,
        mismatched_rows=mismatched_rows,
        predicted_approved_actual_approved=predicted_approved_actual_approved,
        predicted_approved_actual_denied=predicted_approved_actual_denied,
        predicted_denied_actual_approved=predicted_denied_actual_approved,
        predicted_denied_actual_denied=predicted_denied_actual_denied,
        accuracy=accuracy,
        file_processing_seconds=file_processing_seconds,
        compared_rows_per_second=compared_rows_per_second,
    )


def main() -> None:
    """Run batch evaluation with default paths and print compact metrics."""

    audit_path = build_versioned_batch_audit_path()
    summary = evaluate_batch_against_baseline(batch_audit_path=audit_path)
    print("Batch evaluation complete")
    print(f"Compared rows: {summary.compared_rows}/{summary.total_feature_rows}")
    print(f"Accuracy: {summary.accuracy:.4f}")
    print(f"File processing seconds: {summary.file_processing_seconds:.6f} seconds")
    print(f"Compared rows/sec: {summary.compared_rows_per_second:.2f} rows/second")
    print(f"Missing labels: {summary.missing_label_rows}")
    print(f"Invalid rows: {summary.invalid_row_rows}")
    print(f"Batch audit path: {audit_path}")
    print(
        "Confusion (predicted x actual): "
        f"AA={summary.predicted_approved_actual_approved}, "
        f"AD={summary.predicted_approved_actual_denied}, "
        f"DA={summary.predicted_denied_actual_approved}, "
        f"DD={summary.predicted_denied_actual_denied}"
    )


if __name__ == "__main__":
    main()
