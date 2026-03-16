import pandas as pd
import numpy as np
from pathlib import Path

# Data access
def load_raw_data(csv_path: str) -> pd.DataFrame | None:
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

# Quick dataset inspection
def inspect_data(dataset: pd.DataFrame) -> None:
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
    data_path = Path(csv_path)

    # Match files like loans_cleaned_YYYYMMDD_HHMMSS.csv
    versioned_files = sorted(data_path.parent.glob(f"{data_path.stem}_????????_??????{data_path.suffix}"))

    if versioned_files:
        # Filename sorting works because the timestamp is YYYYMMDD_HHMMSS.
        latest_versioned = versioned_files[-1]
        processed_df = pd.read_csv(latest_versioned)
        print(f"Loaded latest versioned data: {latest_versioned} ({processed_df.shape[0]} rows, {processed_df.shape[1]} columns).")
        return processed_df

    if data_path.exists():
        processed_df = pd.read_csv(data_path)
        print(f"Loaded processed data: {data_path} ({processed_df.shape[0]} rows, {processed_df.shape[1]} columns).")
        return processed_df

    return None


# Data cleaning
def clean_data(dataset: pd.DataFrame) -> pd.DataFrame:
    cleaned_df = dataset.copy()

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

# Basic feature engineering
def add_basic_features(dataset: pd.DataFrame) -> pd.DataFrame:
    featured_df = dataset.copy()
    # Add income-based features used in the EDA charts.
    featured_df['total_income'] = featured_df['applicantincome'] + featured_df['coapplicantincome']
    
    featured_df['loan_to_income_ratio'] = np.where(
        featured_df['total_income'] > 0, 
        featured_df['loanamount'] / featured_df['total_income'], 
        0
    )

    # Temporary proxy target for EDA only.
    featured_df['loan_status'] = np.where(featured_df['credit_history'] == 1, 'Approved', 'Denied')
    
    print("\nFeature engineering complete: total_income, loan_to_income_ratio.")
    return featured_df

# Persist processed data (latest + optional versioned copy)
def save_processed_data(dataset: pd.DataFrame, output_csv_path: str, run_id: str | None = None) -> None:
    try:
        output_path = Path(output_csv_path)
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
    # Local smoke test
    raw_csv_path = "data/raw/loans_data.csv"
    raw_data = load_raw_data(raw_csv_path)
    
    if raw_data is not None:
        inspect_data(raw_data)