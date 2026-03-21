"""Execute the EDA workflow for the loan dataset and generate chart artifacts.

This script orchestrates dataset acquisition (processed-first fallback to raw),
profiling, cleaning/feature-enrichment when needed, and batch export of plots to
both versioned and latest graph directories.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from pathlib import Path
from src.data_loader import (
    load_raw_data,
    load_processed_data,
    inspect_data,
    clean_data,
    add_basic_features,
    save_processed_data
)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['figure.figsize'] = (10, 5)
plt.rcParams['font.size'] = 12

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
GRAPH_ROOT = Path("graphs")
GRAPH_RUN_DIR = GRAPH_ROOT / RUN_ID
GRAPH_LATEST_DIR = GRAPH_ROOT / "latest"

# Main pipeline

PROCESSED_DATA_PATH = "data/processed/loans_cleaned.csv"
RAW_DATA_PATH = "data/raw/loans_data.csv"

def run_eda():
    """Run the end-to-end EDA pipeline and produce all visual outputs.

    Flow:
    - Attempt to load the latest processed dataset.
    - If unavailable, load raw data, inspect, clean, engineer features, and persist.
    - Generate and save all configured charts.

    Returns:
        None. Prints progress and writes files to disk.
    """
    print("\nStarting EDA run...")

    dataset = load_processed_data(PROCESSED_DATA_PATH)

    if dataset is not None:
        print("Using latest processed data. Raw step skipped.")
        inspect_data(dataset)
    else:
        print("No processed data found. Running from raw source.")
        raw_dataset = load_raw_data(RAW_DATA_PATH)
        if raw_dataset is None:
            print("Raw data load failed.")
            return
        inspect_data(raw_dataset)
        print("\nRunning cleaning step...")
        cleaned_dataset = clean_data(raw_dataset)
        inspect_data(cleaned_dataset)
        dataset = add_basic_features(cleaned_dataset)
        inspect_data(dataset)
        save_processed_data(
            dataset,
            PROCESSED_DATA_PATH,
            run_id=RUN_ID
        )

    print("\nGenerating charts...")
    print(f"Run artifacts path: {GRAPH_RUN_DIR}")
    plot_all_charts(dataset)

def plot_all_charts(dataset: pd.DataFrame) -> None:
    """Generate the full set of EDA charts for a prepared dataset.

    Args:
        dataset: DataFrame containing EDA-ready columns.

    Returns:
        None. Saves charts through `save_plot`.
    """
    # Generate charts in a fixed order for reproducible reporting.
    plot_target_distribution(dataset)
    plot_categorical_vs_target(dataset)
    plot_numerical_distributions(dataset)
    plot_correlation_heatmap(dataset)
    plot_loan_to_income(dataset)

def save_plot(filename: str, dpi: int = 300) -> None:
    """Save the active Matplotlib figure to versioned and latest locations.

    Args:
        filename: Output file name for the chart image.
        dpi: Export resolution in dots per inch.

    Returns:
        None. Writes image files and closes the current figure.
    """
    # Ensure both output directories exist before writing files.
    GRAPH_RUN_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_LATEST_DIR.mkdir(parents=True, exist_ok=True)

    run_file_path = GRAPH_RUN_DIR / filename
    latest_file_path = GRAPH_LATEST_DIR / filename

    plt.savefig(run_file_path, dpi=dpi)
    plt.savefig(latest_file_path, dpi=dpi)
    plt.close()
    print(f"Saved chart: {run_file_path}")
    print(f"Updated latest chart: {latest_file_path}")

def plot_target_distribution(dataset: pd.DataFrame) -> None:
    """Plot approval-status distribution with percentage labels.

    Args:
        dataset: DataFrame that includes the `loan_status` column.

    Returns:
        None. Renders and saves the chart.
    """
    fig, ax = plt.subplots()
    counts = dataset['loan_status'].value_counts()
    color_map = {"Approved": "#4CAF50", "Denied": "#F44336"}
    colors = [color_map.get(label, "#999999") for label in counts.index]
    bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="white", width=0.5)

    # Annotate percentages to make class balance immediately visible.
    total = counts.sum()
    for bar, val in zip(bars, counts.values):
        pct = f"{val/total*100:.1f}%"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, pct, ha='center', va='bottom', fontweight="bold")

    ax.set_title("Distribution of Loan Approvals", fontweight="bold")
    ax.set_xlabel("Loan Status")
    ax.set_ylabel("Number of Applicants")
    plt.tight_layout()
    save_plot("loan_approval_distribution.png")
    plt.show()

def plot_categorical_vs_target(dataset: pd.DataFrame) -> None:
    """Plot categorical-feature distributions segmented by loan status.

    Args:
        dataset: DataFrame containing candidate categorical columns and `loan_status`.

    Returns:
        None. Renders and saves a multi-panel chart, or exits if no features exist.
    """
    categorical_features = ['gender', 'married', 'education', 'self_employed', 'property_area', 'credit_history']

    # Filter unavailable features to keep the function robust across schema changes.
    categorical_features = [feature_name for feature_name in categorical_features if feature_name in dataset.columns]

    if not categorical_features:
        print("No categorical features found for plotting.")
        return

    n_cols = 2
    n_rows = (len(categorical_features) + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4 * n_rows))
    axes = axes.flatten()

    legend_handles = None
    legend_labels = None

    for ax, feature_name in zip(axes, categorical_features):
        category_order = dataset[feature_name].value_counts().index
        sns.countplot(
            data=dataset,
            x=feature_name,
            hue="loan_status",
            order=category_order,
            ax=ax,
            palette={"Approved": "#4CAF50", "Denied": "#F44336"}
        )
        ax.set_title(feature_name.replace("_", " ").title(), fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("Applicants")
        ax.tick_params(axis="x", rotation=20)

        handles, labels = ax.get_legend_handles_labels()
        if handles and labels:
            legend_handles = handles
            legend_labels = labels
        if ax.get_legend() is not None:
            ax.get_legend().remove()

    for ax in axes[len(categorical_features):]:
        ax.set_visible(False)
    
    fig.suptitle("Categorical Variables vs Loan Approval Status",
                 fontsize=14, fontweight="bold")
    if legend_handles and legend_labels:
        fig.legend(legend_handles, legend_labels, title="Loan Status", loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.01))
    plt.tight_layout(rect=[0, 0.07, 1, 0.94])
    save_plot("categorical_vs_target.png")
    plt.show()

def plot_numerical_distributions(dataset: pd.DataFrame) -> None:
    """Plot histogram and KDE distributions for core numeric variables.

    Args:
        dataset: DataFrame containing numeric EDA columns.

    Returns:
        None. Renders and saves the chart grid.
    """
    numeric_features = ['applicantincome', 'loanamount', 'total_income', 'loan_to_income_ratio']
    numeric_features = [feature_name for feature_name in numeric_features if feature_name in dataset.columns]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for ax, feature_name in zip(axes, numeric_features):
        sns.histplot(dataset[feature_name], kde=True, ax=ax, color="#5C85D6", edgecolor="white")
        ax.set_title(feature_name.replace("_", " ").title(), fontweight="bold")
        ax.set_xlabel("")

    fig.suptitle("Distribution of Numerical Features", fontsize=14, fontweight="bold")
    plt.tight_layout()
    save_plot("numerical_distributions.png", dpi=300)
    plt.show()

def plot_correlation_heatmap(dataset: pd.DataFrame) -> None:
    """Plot a correlation heatmap for numeric columns.

    Args:
        dataset: DataFrame with numeric columns to correlate.

    Returns:
        None. Renders and saves the heatmap.
    """
    numeric_df = dataset.select_dtypes(include=["int64", "float64"])
    corr = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5, ax=ax, square=True)
    ax.set_title("Correlation Heatmap of Numerical Features", fontsize=14, fontweight="bold")
    plt.tight_layout()
    save_plot("correlation_heatmap.png", dpi=300)
    plt.show()

def plot_loan_to_income(dataset: pd.DataFrame) -> None:
    """Plot loan-to-income ratio distribution grouped by loan status.

    Args:
        dataset: DataFrame that should include `loan_to_income_ratio` and `loan_status`.

    Returns:
        None. Renders and saves the chart, or exits if required columns are missing.
    """

    if 'loan_to_income_ratio' not in dataset.columns:
        # Abort early when prerequisite feature is not available.
        print("Missing 'loan_to_income_ratio'. Skipping chart.")
        return
    
    fig, ax = plt.subplots()
    sns.boxplot(data=dataset, x="loan_status", y="loan_to_income_ratio", hue="loan_status", legend=False, ax=ax, palette={"Approved": "#4CAF50", "Denied": "#F44336"})
    ax.set_title("Loan-to-Income Ratio by Loan Status", fontsize=14, fontweight="bold")
    ax.set_xlabel("Loan Status")
    ax.set_ylabel("Loan-to-Income Ratio")
    plt.tight_layout()
    save_plot("loan_to_income_ratio_by_status.png", dpi=300)
    plt.show()

if __name__ == "__main__":
    run_eda()