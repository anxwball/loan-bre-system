"""Load, inspect, transform, and persist loan datasets for the EDA pipeline.

This module centralizes data lifecycle operations used in Phase 1:
input ingestion from CSV, null-profile inspection, deterministic cleaning,
lightweight feature engineering, and version-aware persistence of processed data.
"""

import json
from datetime import datetime
import pandas as pd
from pathlib import Path
from time import perf_counter

from src.audit_logger import append_jsonl_record
from src.db.database import create_db_engine, dispose_engine, initialize_database
from src.db.repositories import AuditRepository

LABELS_ROOT_PATH = Path("data/labels")
LABELS_VERSIONS_PATH = LABELS_ROOT_PATH / "versions"
LABELS_LATEST_PATH = LABELS_ROOT_PATH / "loan_labels_latest.csv"
LEGACY_LABELS_PATH = Path("data/processed/loan_labels.csv")
PIPELINE_PERFORMANCE_LOG_PATH = Path("data/audit/file_processing_latest.jsonl")

LABEL_VALUE_MAP = {
    "Y": "Approved",
    "N": "Denied",
    "APPROVED": "Approved",
    "DENIED": "Denied",
}

def load_raw_data(filepath: str) -> pd.DataFrame | None:
    """Load raw loan data from a CSV file.

    Args:
        filepath: Relative or absolute path to the raw CSV file.

    Returns:
        A DataFrame with raw records when the file is available and readable;
        otherwise None.

    Raises:
        FileNotFoundError: Raised internally when the target path does not exist.
    """
    try:
        if Path(filepath).exists():
            raw_df = pd.read_csv(filepath)
            print(f"Loaded raw data: {raw_df.shape[0]} rows, {raw_df.shape[1]} columns.")
            return raw_df
        else:
            raise FileNotFoundError(f"Missing file: {filepath}")
    except pd.errors.EmptyDataError:
        print("Input file is empty.")
    except Exception as e:
        print(f"Read error: {e}")

def inspect_dataset(df: pd.DataFrame) -> None:
    """Print a compact structural and missing-value summary of a dataset.

    Args:
        df: DataFrame to inspect.

    Returns:
        None. Outputs summary information to stdout.
    """
    print("\n" + "="*50)
    print("Dataset overview")
    print("="*50)
    df.info()

    print("\n" + "="*50)
    print("Null values by column")
    print("="*50)
    nulls = df.isnull().sum()
    null_percent = ((nulls / len(df)) * 100).round(2)
    null_summary = pd.DataFrame({'Null Count': nulls, 'Null Percentage': null_percent})
    print(null_summary[null_summary['Null Count'] > 0])

def inspect_data(df: pd.DataFrame) -> None:
    """Backward-compatible wrapper for dataset inspection.

    Args:
        df: DataFrame to inspect.

    Returns:
        None. Delegates to `inspect_dataset`.
    """
    inspect_dataset(df)

def load_processed_data(csv_path: str) -> pd.DataFrame | None:
    """Load the latest available processed dataset.

    The loader first searches for versioned files that match
    `<stem>_YYYYMMDD_HHMMSS<suffix>` in the same directory and returns the
    most recent one. If none exist, it falls back to the non-versioned file.

    Args:
        csv_path: Base path of the processed CSV file.

    Returns:
        A DataFrame with processed data, or None if no candidate file exists.
    """
    data_path = Path(csv_path)

    # Prioritize timestamped versions to keep reproducibility.
    versioned_files = sorted(data_path.parent.glob(f"{data_path.stem}_????????_??????{data_path.suffix}"))

    if versioned_files:
        # Rely on lexical order because format is YYYYMMDD_HHMMSS.
        latest_versioned = versioned_files[-1]
        processed_df = pd.read_csv(latest_versioned)
        print(f"Loaded latest versioned data: {latest_versioned} ({processed_df.shape[0]} rows, {processed_df.shape[1]} columns).")
        return processed_df

    if data_path.exists():
        processed_df = pd.read_csv(data_path)
        print(f"Loaded processed data: {data_path} ({processed_df.shape[0]} rows, {processed_df.shape[1]} columns).")
        return processed_df

    return None

def rename_columns(dataset: pd.DataFrame) -> pd.DataFrame:
    """Rename specific legacy columns to canonical snake_case names.

    Args:
        dataset: DataFrame whose columns were already lowercased.

    Returns:
        A copy of the input DataFrame with selected columns renamed.
    """
    renamed_df = dataset.copy()
    renamed_df = renamed_df.rename(columns={
        "applicantincome": "applicant_income",
        "coapplicantincome": "coapplicant_income",
        "loanamount": "loan_amount",
    })
    return renamed_df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize schema and impute missing values with simple statistics.

    Processing rules:
    - Normalize column names to lowercase.
    - Fill categorical nulls with the mode of each column.
    - Fill numeric nulls with the median of each column.

    Args:
        df: Input DataFrame to clean.

    Returns:
        A cleaned copy of the input DataFrame.
    """
    cleaned_df = df.copy()

    # Normalize column names before downstream transformations.
    cleaned_df.columns = [column_name.lower() for column_name in cleaned_df.columns]

    categorical_columns = cleaned_df.select_dtypes(include="object").columns.to_list()
    numeric_columns = cleaned_df.select_dtypes(include=["int64", "float64"]).columns.to_list()

    for column_name in categorical_columns:
        if cleaned_df[column_name].isnull().sum() > 0:
            mode = cleaned_df[column_name].mode()[0]
            cleaned_df[column_name] = cleaned_df[column_name].fillna(mode)
            print(f"Filled missing values in '{column_name}' with mode: {mode}")

    for column_name in numeric_columns:
        if cleaned_df[column_name].isnull().sum() > 0:
            median = cleaned_df[column_name].median()
            cleaned_df[column_name] = cleaned_df[column_name].fillna(median)
            print(f"Filled missing values in '{column_name}' with median: {median}")

    print("\nCleaning complete. No missing values.")
    return cleaned_df

def split_labels(dataset: pd.DataFrame) -> pd.DataFrame:
    """Separate benchmark labels from feature columns and persist label pairs.

    The function extracts `loan_id` and `loan_status` to a dedicated labels file
    and returns a feature-only DataFrame without `loan_status`.

    Args:
        dataset: Cleaned DataFrame that includes the historical target label.

    Returns:
        A copy of the input DataFrame without the `loan_status` column when the
        label exists; otherwise an unchanged copy.
    """
    split_df = dataset.copy()

    if "loan_status" not in split_df.columns:
        print("No 'loan_status' column found. Skipping label split.")
        return split_df

    if "loan_id" not in split_df.columns:
        print("No 'loan_id' column found. Skipping label split.")
        return split_df

    labels_df = split_df[["loan_id", "loan_status"]].copy()
    normalized_labels_df = normalize_label_values(labels_df)
    validation_report = validate_labels_integrity(normalized_labels_df)
    coverage_report = validate_label_coverage(split_df[["loan_id"]].copy(), normalized_labels_df)

    if validation_report["null_id_count"] > 0:
        raise ValueError("Label integrity error: loan_id contains null values.")
    if validation_report["duplicate_id_count"] > 0:
        raise ValueError("Label integrity error: duplicate loan_id values detected.")
    if validation_report["null_label_count"] > 0:
        raise ValueError("Label integrity error: loan_status contains null values.")
    if validation_report["invalid_label_count"] > 0:
        raise ValueError("Label integrity error: loan_status contains values outside the approved dictionary.")

    print(
        "Label coverage: "
        f"{coverage_report['matched_feature_rows']} of {coverage_report['feature_rows']} "
        f"feature rows ({coverage_report['coverage_pct']:.2f}%)."
    )

    save_labels_data(
        normalized_labels_df,
        source="pipeline_split_labels",
        owner="unassigned",
        quality_notes="Generated from pipeline input dataset.",
    )

    feature_df = split_df.drop(columns=["loan_status"]).copy()
    return feature_df


def normalize_label_values(labels_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw label values into canonical business classes.

    Accepted source values are `Y/N` or `Approved/Denied` in any case.

    Args:
        labels_df: DataFrame containing `loan_id` and `loan_status` columns.

    Returns:
        A normalized copy where `loan_status` uses canonical values.
    """
    normalized_df = labels_df.copy()

    normalized_df["loan_id"] = normalized_df["loan_id"].astype("string").str.strip()
    normalized_df["loan_status"] = normalized_df["loan_status"].astype("string").str.strip().str.upper()
    normalized_df["loan_status"] = normalized_df["loan_status"].map(LABEL_VALUE_MAP)

    return normalized_df


def validate_labels_integrity(labels_df: pd.DataFrame) -> dict:
    """Validate structural and semantic integrity for the label dataset.

    Args:
        labels_df: DataFrame containing normalized labels.

    Returns:
        A dictionary with integrity and distribution metrics.
    """
    validation_df = labels_df.copy()

    null_id_count = int(validation_df["loan_id"].isna().sum())
    duplicate_id_count = int(validation_df["loan_id"].duplicated().sum())
    null_label_count = int(validation_df["loan_status"].isna().sum())
    invalid_label_count = int((~validation_df["loan_status"].isin(["Approved", "Denied"]) & validation_df["loan_status"].notna()).sum())

    class_distribution = validation_df["loan_status"].value_counts(dropna=True).to_dict()

    return {
        "row_count": int(len(validation_df)),
        "null_id_count": null_id_count,
        "duplicate_id_count": duplicate_id_count,
        "null_label_count": null_label_count,
        "invalid_label_count": invalid_label_count,
        "class_distribution": class_distribution,
    }


def validate_label_coverage(features_df: pd.DataFrame, labels_df: pd.DataFrame, id_column: str = "loan_id") -> dict:
    """Measure label coverage against a feature dataset by identifier.

    Args:
        features_df: Feature DataFrame that should be label-addressable.
        labels_df: Label DataFrame containing at least `loan_id`.
        id_column: Join key used to measure coverage.

    Returns:
        Coverage metrics for governance and quality controls.
    """
    features_copy = features_df.copy()
    labels_copy = labels_df.copy()

    features_ids = set(features_copy[id_column].dropna().astype("string").str.strip())
    labels_ids = set(labels_copy[id_column].dropna().astype("string").str.strip())

    feature_rows = len(features_copy)
    matched_feature_rows = int(features_copy[id_column].astype("string").str.strip().isin(labels_ids).sum())
    unmatched_feature_rows = feature_rows - matched_feature_rows
    labels_without_feature = len(labels_ids - features_ids)

    coverage_pct = 0.0
    if feature_rows > 0:
        coverage_pct = (matched_feature_rows / feature_rows) * 100

    return {
        "feature_rows": int(feature_rows),
        "matched_feature_rows": int(matched_feature_rows),
        "unmatched_feature_rows": int(unmatched_feature_rows),
        "labels_without_feature": int(labels_without_feature),
        "coverage_pct": float(round(coverage_pct, 2)),
    }


def save_labels_data(
    labels_df: pd.DataFrame,
    source: str,
    owner: str,
    quality_notes: str = "",
    run_id: str | None = None,
) -> None:
    """Persist labels to latest and versioned snapshots with metadata.

    Args:
        labels_df: Validated labels DataFrame with `loan_id` and `loan_status`.
        source: Human-readable source descriptor for governance records.
        owner: Accountable owner of the label snapshot.
        quality_notes: Optional quality summary for governance and audits.
        run_id: Optional snapshot identifier in `YYYYMMDD_HHMMSS` format.

    Returns:
        None. Writes CSV and metadata JSON files to disk.
    """
    safe_labels_df = labels_df.copy()

    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    LABELS_ROOT_PATH.mkdir(parents=True, exist_ok=True)
    LABELS_VERSIONS_PATH.mkdir(parents=True, exist_ok=True)
    LEGACY_LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)

    latest_file_path = LABELS_LATEST_PATH
    versioned_file_path = LABELS_VERSIONS_PATH / f"loan_labels_{run_id}.csv"
    metadata_file_path = LABELS_VERSIONS_PATH / f"loan_labels_{run_id}.meta.json"

    safe_labels_df.to_csv(latest_file_path, index=False)
    safe_labels_df.to_csv(versioned_file_path, index=False)

    # Keep legacy path available while downstream modules migrate to data/labels.
    safe_labels_df.to_csv(LEGACY_LABELS_PATH, index=False)

    validation_report = validate_labels_integrity(safe_labels_df)
    metadata = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "owner": owner,
        "quality_notes": quality_notes,
        "integrity_report": validation_report,
    }
    metadata_file_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Updated latest labels file: {latest_file_path}")
    print(f"Saved versioned labels file: {versioned_file_path}")
    print(f"Saved labels metadata file: {metadata_file_path}")


def ingest_human_labels(
    labels_path: str,
    id_column: str = "loan_id",
    label_column: str = "loan_status",
    source: str = "human_review",
    owner: str = "unassigned",
    quality_notes: str = "",
    run_id: str | None = None,
) -> pd.DataFrame:
    """Ingest an external human-label file and persist governed label snapshots.

    Args:
        labels_path: CSV path containing human-generated labels.
        id_column: Identifier column name in the external file.
        label_column: Label column name in the external file.
        source: Source descriptor for audit metadata.
        owner: Responsible owner for the label snapshot.
        quality_notes: Optional quality summary.
        run_id: Optional explicit run identifier.

    Returns:
        The validated canonical labels DataFrame.

    Raises:
        FileNotFoundError: If the external labels file does not exist.
        ValueError: If required columns or integrity validations fail.
    """
    input_path = Path(labels_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    raw_labels_df = pd.read_csv(input_path)
    working_df = raw_labels_df.copy()
    working_df.columns = [column_name.lower() for column_name in working_df.columns]

    normalized_id_column = id_column.lower()
    normalized_label_column = label_column.lower()

    if normalized_id_column not in working_df.columns:
        raise ValueError(f"Missing id column in labels file: {id_column}")
    if normalized_label_column not in working_df.columns:
        raise ValueError(f"Missing label column in labels file: {label_column}")

    canonical_labels_df = working_df[[normalized_id_column, normalized_label_column]].copy()
    canonical_labels_df = canonical_labels_df.rename(columns={
        normalized_id_column: "loan_id",
        normalized_label_column: "loan_status",
    })

    canonical_labels_df = normalize_label_values(canonical_labels_df)
    validation_report = validate_labels_integrity(canonical_labels_df)

    if validation_report["null_id_count"] > 0:
        raise ValueError("Label integrity error: loan_id contains null values.")
    if validation_report["duplicate_id_count"] > 0:
        raise ValueError("Label integrity error: duplicate loan_id values detected.")
    if validation_report["null_label_count"] > 0:
        raise ValueError("Label integrity error: loan_status contains null values.")
    if validation_report["invalid_label_count"] > 0:
        raise ValueError("Label integrity error: loan_status contains values outside the approved dictionary.")

    save_labels_data(
        canonical_labels_df,
        source=source,
        owner=owner,
        quality_notes=quality_notes,
        run_id=run_id,
    )
    return canonical_labels_df

def add_basic_features(dataset: pd.DataFrame) -> pd.DataFrame:
    """Placeholder hook for future feature engineering extensions.

    Current behavior intentionally keeps the dataset unchanged because
    `total_income` and `loan_to_income_ratio` are derived in `LoanApplication`
    and `loan_status` is managed as an external benchmark label.

    Args:
        dataset: Clean DataFrame used as the base for optional feature generation.

    Returns:
        An unchanged copy of the input DataFrame.
    """
    featured_df = dataset.copy()
    print("\nNo additional EDA features were applied in this run.")
    return featured_df

def save_processed_data(dataset: pd.DataFrame, output_csv_path: str = "data/processed/loans_cleaned.csv", run_id: str | None = None) -> None:
    """Persist processed data as latest and optionally as a versioned snapshot.

    Args:
        dataset: Processed DataFrame to persist.
        output_csv_path: Canonical output path for the latest processed file.
        run_id: Optional run identifier appended to create a versioned copy.

    Returns:
        None. Writes files to disk.
    """
    try:
        output_path = Path(output_csv_path)
        # Guarantee output directory exists before writing files.
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dataset.to_csv(output_path, index=False)
        print(f"Updated latest processed file: {output_path}")

        if run_id:
            run_file_path = output_path.parent / f"{output_path.stem}_{run_id}{output_path.suffix}"
            dataset.to_csv(run_file_path, index=False)
            print(f"Saved versioned processed file: {run_file_path}")
    except Exception as e:
        print(f"Write error: {e}")

def run_pipeline(
    input_path: str,
    performance_log_path: Path | None = PIPELINE_PERFORMANCE_LOG_PATH,
    sql_audit_database_url: str | None = None,
) -> pd.DataFrame:
    """Run the explicit data preparation pipeline from raw input to processed output.

    Pipeline order:
    - Load
    - Clean
    - Rename schema fields
    - Apply feature hook
    - Split benchmark labels
    - Save processed features

    Args:
        input_path: Source CSV path used as pipeline input.
        performance_log_path: Optional JSONL path used to persist one
            performance record per pipeline execution.
        sql_audit_database_url: Optional SQLAlchemy URL used to dual-write
            pipeline performance metrics into SQL persistence.

    Returns:
        The processed feature DataFrame generated by the pipeline.

    Raises:
        FileNotFoundError: If input data cannot be loaded.
    """
    pipeline_start = perf_counter()

    df = load_raw_data(input_path)
    if df is None:
        raise FileNotFoundError(f"Pipeline input could not be loaded: {input_path}")

    df = clean_data(df)
    df = rename_columns(df)
    df = add_basic_features(df)
    df = split_labels(df)
    save_processed_data(df)

    file_processing_seconds = perf_counter() - pipeline_start
    processed_rows = len(df)
    processed_rows_per_second = (
        processed_rows / file_processing_seconds if file_processing_seconds > 0 else 0.0
    )

    df.attrs["file_processing_seconds"] = file_processing_seconds
    df.attrs["processed_rows_per_second"] = processed_rows_per_second

    if performance_log_path is not None:
        append_jsonl_record(
            {
                "mode": "pipeline_performance",
                "input_path": input_path,
                "processed_rows": processed_rows,
                "file_processing_seconds": file_processing_seconds,
                "processed_rows_per_second": processed_rows_per_second,
            },
            performance_log_path,
        )

    if sql_audit_database_url is not None:
        sql_engine = create_db_engine(database_url=sql_audit_database_url)
        initialize_database(sql_engine)
        audit_repository = AuditRepository(sql_engine)
        try:
            audit_repository.insert_data_load(
                filepath=input_path,
                processed_rows=processed_rows,
                file_processing_seconds=file_processing_seconds,
                rows_per_second=processed_rows_per_second,
            )
        finally:
            dispose_engine(sql_engine)

    return df

if __name__ == "__main__":
    """Run a local smoke test for the full pipeline."""
    pipeline_df = run_pipeline("data/raw/loan_train.csv")
    inspect_dataset(pipeline_df)