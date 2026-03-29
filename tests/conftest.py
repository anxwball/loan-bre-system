"""Shared pytest fixtures for BRE engine tests."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bre_engine import RuleEngine
from src.loan_application import LoanApplication

@pytest.fixture
def engine() -> RuleEngine:
    """Create a fresh rules engine instance for each test."""

    return RuleEngine()


@pytest.fixture
def build_application():
    """Build a valid baseline loan application with optional overrides."""

    def _build_application(**overrides) -> LoanApplication:
        base_data = {
            "loan_id": "LP001",
            "gender": "Male",
            "married": "No",
            "dependents": "0",
            "education": "Graduate",
            "self_employed": "No",
            "applicant_income": 5000.0,
            "coapplicant_income": 0.0,
            "loan_amount": 100.0,
            "loan_amount_term": 360.0,
            "credit_history": 1,
            "property_area": "Urban",
        }
        base_data.update(overrides)
        return LoanApplication(**base_data)

    return _build_application


def _coerce_cleaned_row(row: dict[str, str]) -> dict[str, object]:
    """Cast raw CSV values to LoanApplication-compatible field types."""

    return {
        "loan_id": row["loan_id"],
        "gender": row["gender"],
        "married": row["married"],
        "dependents": row["dependents"],
        "education": row["education"],
        "self_employed": row["self_employed"],
        "applicant_income": float(row["applicant_income"]),
        "coapplicant_income": float(row["coapplicant_income"]),
        "loan_amount": float(row["loan_amount"]),
        "loan_amount_term": float(row["loan_amount_term"]),
        "credit_history": int(float(row["credit_history"])),
        "property_area": row["property_area"],
    }


@pytest.fixture
def cleaned_row_lp001015() -> dict[str, object]:
    """Load one deterministic low-risk row for integral test execution."""

    dataset_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "loans_cleaned.csv"

    with dataset_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row["loan_id"] == "LP001015":
                return _coerce_cleaned_row(row)

    raise AssertionError("Expected loan_id LP001015 not found in loans_cleaned.csv")
