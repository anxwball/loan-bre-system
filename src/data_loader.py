"""Load, inspect, transform, and persist loan datasets for the EDA pipeline.

This module centralizes data lifecycle operations used in Phase 1:
input ingestion from CSV, null-profile inspection, deterministic cleaning,
lightweight feature engineering, and version-aware persistence of processed data.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def load_raw_data(csv_path: str) -> pd.DataFrame | None:
    """Load raw loan data from a CSV file.

    Args:
        csv_path: Relative or absolute path to the raw CSV file.

    Returns:
        A DataFrame with raw records when the file is available and readable;
        otherwise None.

    Raises:
        FileNotFoundError: Raised internally when the target path does not exist.
    """
    try:
        if Path(csv_path).exists():
            raw_df = pd.read_csv(csv_path)
            print(f"Loaded raw data: {raw_df.shape[0]} rows, {raw_df.shape[1]} columns.")
            return raw_df
        else:
            raise FileNotFoundError(f"Missing file: {csv_path}")
    except pd.errors.EmptyDataError:
        print("Input file is empty.")
    except Exception as e:
        print(f"Read error: {e}")

def inspect_data(dataset: pd.DataFrame) -> None:
    """Print a compact structural and missing-value summary of a dataset.

    Args:
        dataset: DataFrame to inspect.

    Returns:
        None. Outputs summary information to stdout.
    """
    print("\n" + "="*50)
    print("Dataset overview")
    print("="*50)
    dataset.info()

    print("\n" + "="*50)
    print("Null values by column")
    print("="*50)
    nulls = dataset.isnull().sum()
    null_percent = ((nulls / len(dataset)) * 100).round(2)
    null_summary = pd.DataFrame({'Null Count': nulls, 'Null Percentage': null_percent})
    print(null_summary[null_summary['Null Count'] > 0])

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

def clean_data(dataset: pd.DataFrame) -> pd.DataFrame:
    """Standardize schema and impute missing values with simple statistics.

    Processing rules:
    - Normalize column names to lowercase.
    - Fill categorical nulls with the mode of each column.
    - Fill numeric nulls with the median of each column.

    Args:
        dataset: Input DataFrame to clean.

    Returns:
        A cleaned copy of the input DataFrame.
    """
    cleaned_df = dataset.copy()

    # Normalize column names before downstream feature references.
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

def add_basic_features(dataset: pd.DataFrame) -> pd.DataFrame:
    """Create derived features required for exploratory analysis.

    Added columns:
    - `total_income`: applicant + coapplicant income.
    - `loan_to_income_ratio`: loan amount divided by total income (safe for zero income).
    - `loan_status`: temporary proxy label based on credit history.

    Args:
        dataset: Clean DataFrame used as the base for feature generation.

    Returns:
        A new DataFrame containing the engineered features.
    """
    featured_df = dataset.copy()
    # Compute aggregate income first; reuse it for ratio calculation.
    featured_df['total_income'] = featured_df['applicantincome'] + featured_df['coapplicantincome']
    
    featured_df['loan_to_income_ratio'] = np.where(
        featured_df['total_income'] > 0, 
        featured_df['loanamount'] / featured_df['total_income'], 
        0
    )

    # Keep this proxy label restricted to EDA scope.
    featured_df['loan_status'] = np.where(featured_df['credit_history'] == 1, 'Approved', 'Denied')
    
    print("\nFeature engineering complete: total_income, loan_to_income_ratio.")
    return featured_df

def save_processed_data(dataset: pd.DataFrame, output_csv_path: str, run_id: str | None = None) -> None:
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

if __name__ == "__main__":
    """Run a local smoke test for raw-data loading and inspection."""
    raw_csv_path = "data/raw/loans_data.csv"
    raw_data = load_raw_data(raw_csv_path)
    
    if raw_data is not None:
        inspect_data(raw_data)