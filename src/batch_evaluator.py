"""Run deterministic BRE batch evaluation against a historical baseline.

This module evaluates cleaned feature rows with the RuleEngine and compares
predicted decisions against baseline labels (`Approved`/`Denied`). It returns
aggregate metrics and can optionally persist row-level comparison output.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter

from src.audit_logger import (
    append_jsonl_record,
    build_decision_audit_record,
    build_versioned_batch_audit_path,
)
from src.bre_engine import RuleEngine
from src.db.database import create_db_engine, dispose_engine, initialize_database
from src.db.repositories import AuditRepository, LoanRepository
from src.loan_application import LoanApplication


DEFAULT_FEATURES_PATH = Path("data/processed/loans_cleaned.csv")
DEFAULT_LABELS_PATH = Path("data/processed/loan_labels.csv")
DEFAULT_OUTPUT_PATH = Path("data/processed/batch_evaluation_latest.csv")
SUPPORTED_AUDIT_MODES = {"sql", "dual", "jsonl"}


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


@dataclass
class _BatchRuntimeState:
    """Keep mutable counters and row outputs during batch evaluation."""

    total_feature_rows: int = 0
    compared_rows: int = 0
    missing_label_rows: int = 0
    invalid_row_rows: int = 0
    matched_rows: int = 0
    mismatched_rows: int = 0
    predicted_approved_actual_approved: int = 0
    predicted_approved_actual_denied: int = 0
    predicted_denied_actual_approved: int = 0
    predicted_denied_actual_denied: int = 0
    output_rows: list[dict[str, object]] = field(default_factory=list)


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


def _resolve_audit_mode(audit_mode: str | None, default_mode: str = "sql") -> str:
    """Resolve and validate audit sink policy for batch processing.

    Args:
        audit_mode: Optional explicit sink policy (`sql`, `dual`, `jsonl`).
        default_mode: Fallback mode used when `audit_mode` is None.

    Returns:
        Effective audit mode.

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
        Storage label used in emitted audit payloads.
    """

    if persist_jsonl and persist_sql:
        return "jsonl+sql"
    if persist_jsonl:
        return "jsonl"
    return "sql"


def _build_sql_repositories(
    persist_sql: bool,
    sql_audit_database_url: str | None,
) -> tuple[object | None, LoanRepository | None, AuditRepository | None]:
    """Create SQL engine and repositories only when SQL persistence is enabled."""

    if not persist_sql:
        return None, None, None

    sql_engine = create_db_engine(database_url=sql_audit_database_url)
    initialize_database(sql_engine)
    loan_repository = LoanRepository(sql_engine)
    audit_repository = AuditRepository(sql_engine)
    return sql_engine, loan_repository, audit_repository


def _update_confusion_counters(
    state: _BatchRuntimeState,
    predicted_label: str,
    baseline_label: str,
) -> bool:
    """Update comparison counters and return match status for one prediction."""

    state.compared_rows += 1
    is_match = predicted_label == baseline_label

    if is_match:
        state.matched_rows += 1
    else:
        state.mismatched_rows += 1

    if predicted_label == "Approved" and baseline_label == "Approved":
        state.predicted_approved_actual_approved += 1
    elif predicted_label == "Approved" and baseline_label == "Denied":
        state.predicted_approved_actual_denied += 1
    elif predicted_label == "Denied" and baseline_label == "Approved":
        state.predicted_denied_actual_approved += 1
    else:
        state.predicted_denied_actual_denied += 1

    return is_match


def _append_output_row(
    state: _BatchRuntimeState,
    loan_id: str,
    predicted_label: str,
    baseline_label: str,
    is_match: bool,
    decision,
) -> None:
    """Append one row-level comparison payload for CSV output."""

    state.output_rows.append(
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


def _persist_jsonl_decision(
    app: LoanApplication,
    decision,
    predicted_label: str,
    baseline_label: str,
    is_match: bool,
    storage_label: str,
    batch_audit_path: Path,
) -> None:
    """Persist one compared decision row to JSONL audit output."""

    audit_record = build_decision_audit_record(
        app=app,
        decision=decision,
        audit_storage=storage_label,
    )
    audit_record["mode"] = "batch"
    audit_record["predicted_status"] = predicted_label
    audit_record["baseline_status"] = baseline_label
    audit_record["matched"] = is_match
    append_jsonl_record(audit_record, batch_audit_path)


def _persist_sql_decision(
    loan_repository: LoanRepository,
    audit_repository: AuditRepository,
    app: LoanApplication,
    decision,
    baseline_label: str,
    features_path: Path,
    batch_run_id: str | None,
) -> None:
    """Persist one compared decision row to SQL audit tables."""

    persisted_loan = loan_repository.get_by_loan_id(app.loan_id)
    if persisted_loan is None:
        loan_application_id = loan_repository.insert_application(
            app=app,
            applicant_id=app.loan_id,
            source_file=str(features_path),
            loan_status=baseline_label,
        )
    else:
        loan_application_id = int(persisted_loan["id"])

    evaluation_id = audit_repository.insert_evaluation(
        loan_application_id=loan_application_id,
        decision=decision,
        mode="batch",
        batch_id=batch_run_id,
    )
    audit_repository.insert_rule_traces(
        evaluation_id=evaluation_id,
        rules=decision.rules_triggered,
    )


def _process_feature_row(
    row: dict[str, str],
    labels_by_id: dict[str, str],
    engine: RuleEngine,
    state: _BatchRuntimeState,
    persist_jsonl: bool,
    batch_audit_path: Path | None,
    storage_label: str,
    loan_repository: LoanRepository | None,
    audit_repository: AuditRepository | None,
    features_path: Path,
    batch_run_id: str | None,
) -> None:
    """Evaluate one feature row and update in-memory and persisted outputs."""

    state.total_feature_rows += 1
    loan_id = row["loan_id"]
    baseline_label = labels_by_id.get(loan_id)
    if baseline_label is None:
        state.missing_label_rows += 1
        return

    try:
        app = _coerce_row_to_application(row)
        decision = engine.evaluate(app)
    except (ValueError, KeyError):
        state.invalid_row_rows += 1
        return

    predicted_label = "Approved" if decision.approved else "Denied"
    is_match = _update_confusion_counters(
        state=state,
        predicted_label=predicted_label,
        baseline_label=baseline_label,
    )

    _append_output_row(
        state=state,
        loan_id=loan_id,
        predicted_label=predicted_label,
        baseline_label=baseline_label,
        is_match=is_match,
        decision=decision,
    )

    if persist_jsonl and batch_audit_path is not None:
        _persist_jsonl_decision(
            app=app,
            decision=decision,
            predicted_label=predicted_label,
            baseline_label=baseline_label,
            is_match=is_match,
            storage_label=storage_label,
            batch_audit_path=batch_audit_path,
        )

    if loan_repository is not None and audit_repository is not None:
        _persist_sql_decision(
            loan_repository=loan_repository,
            audit_repository=audit_repository,
            app=app,
            decision=decision,
            baseline_label=baseline_label,
            features_path=features_path,
            batch_run_id=batch_run_id,
        )


def _write_output_rows(output_path: Path | None, output_rows: list[dict[str, object]]) -> None:
    """Persist row-level comparison CSV when output is enabled."""

    if output_path is None:
        return

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


def _compute_performance_metrics(
    compared_rows: int,
    processing_start: float,
) -> tuple[float, float]:
    """Compute elapsed processing time and compared-row throughput."""

    file_processing_seconds = perf_counter() - processing_start
    compared_rows_per_second = (
        compared_rows / file_processing_seconds if file_processing_seconds > 0 else 0.0
    )
    return file_processing_seconds, compared_rows_per_second


def _build_summary(
    state: _BatchRuntimeState,
    file_processing_seconds: float,
    compared_rows_per_second: float,
) -> BatchEvaluationSummary:
    """Build immutable summary object from mutable runtime counters."""

    accuracy = state.matched_rows / state.compared_rows if state.compared_rows > 0 else 0.0
    return BatchEvaluationSummary(
        total_feature_rows=state.total_feature_rows,
        compared_rows=state.compared_rows,
        missing_label_rows=state.missing_label_rows,
        invalid_row_rows=state.invalid_row_rows,
        matched_rows=state.matched_rows,
        mismatched_rows=state.mismatched_rows,
        predicted_approved_actual_approved=state.predicted_approved_actual_approved,
        predicted_approved_actual_denied=state.predicted_approved_actual_denied,
        predicted_denied_actual_approved=state.predicted_denied_actual_approved,
        predicted_denied_actual_denied=state.predicted_denied_actual_denied,
        accuracy=accuracy,
        file_processing_seconds=file_processing_seconds,
        compared_rows_per_second=compared_rows_per_second,
    )


def evaluate_batch_against_baseline(
    features_path: Path = DEFAULT_FEATURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    output_path: Path | None = DEFAULT_OUTPUT_PATH,
    batch_audit_path: Path | None = None,
    sql_audit_database_url: str | None = None,
    audit_mode: str | None = None,
) -> BatchEvaluationSummary:
    """Evaluate all features and compare BRE decisions against baseline labels.

    Args:
        features_path: Cleaned feature CSV path.
        labels_path: Baseline label CSV path.
        output_path: Optional destination for row-level comparison output.
        batch_audit_path: Optional destination for line-delimited audit records.
        sql_audit_database_url: Optional SQLAlchemy URL used to dual-write
            audit records into SQL persistence during migration.
        audit_mode: Optional sink policy (`sql`, `dual`, `jsonl`). Defaults
            to `sql` for runtime cutoff progression.

    Returns:
        BatchEvaluationSummary with aggregate evaluation metrics.
    """

    labels_by_id = _load_labels(labels_path)
    engine = RuleEngine()
    state = _BatchRuntimeState()
    processing_start = perf_counter()

    effective_audit_mode = _resolve_audit_mode(audit_mode)
    persist_jsonl = effective_audit_mode in {"dual", "jsonl"}
    persist_sql = effective_audit_mode in {"dual", "sql"}
    storage_label = _resolve_storage_label(
        persist_jsonl=persist_jsonl,
        persist_sql=persist_sql,
    )

    sql_engine, loan_repository, audit_repository = _build_sql_repositories(
        persist_sql=persist_sql,
        sql_audit_database_url=sql_audit_database_url,
    )
    batch_run_id = batch_audit_path.stem if batch_audit_path is not None else None

    try:
        with features_path.open("r", newline="", encoding="utf-8") as features_file:
            reader = csv.DictReader(features_file)
            for row in reader:
                _process_feature_row(
                    row=row,
                    labels_by_id=labels_by_id,
                    engine=engine,
                    state=state,
                    persist_jsonl=persist_jsonl,
                    batch_audit_path=batch_audit_path,
                    storage_label=storage_label,
                    loan_repository=loan_repository,
                    audit_repository=audit_repository,
                    features_path=features_path,
                    batch_run_id=batch_run_id,
                )

        _write_output_rows(
            output_path=output_path,
            output_rows=state.output_rows,
        )

        file_processing_seconds, compared_rows_per_second = _compute_performance_metrics(
            compared_rows=state.compared_rows,
            processing_start=processing_start,
        )

        if persist_jsonl and batch_audit_path is not None:
            append_jsonl_record(
                {
                    "mode": "batch_performance",
                    "audit_storage": storage_label,
                    "features_path": str(features_path),
                    "labels_path": str(labels_path),
                    "compared_rows": state.compared_rows,
                    "total_feature_rows": state.total_feature_rows,
                    "file_processing_seconds": file_processing_seconds,
                    "compared_rows_per_second": compared_rows_per_second,
                },
                batch_audit_path,
            )

        if audit_repository is not None:
            audit_repository.insert_data_load(
                filepath=str(features_path),
                processed_rows=state.compared_rows,
                file_processing_seconds=file_processing_seconds,
                rows_per_second=compared_rows_per_second,
            )

        return _build_summary(
            state=state,
            file_processing_seconds=file_processing_seconds,
            compared_rows_per_second=compared_rows_per_second,
        )
    finally:
        if sql_engine is not None:
            dispose_engine(sql_engine)


def main() -> None:
    """Run batch evaluation with default paths and print compact metrics."""

    audit_path = build_versioned_batch_audit_path()
    summary = evaluate_batch_against_baseline(
        batch_audit_path=audit_path,
        audit_mode="dual",
    )
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
