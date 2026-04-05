"""Define input contracts for Phase 4c evaluation endpoints."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class LoanEvaluationRequest(BaseModel):
    """Represent one loan-application payload accepted by the API.

    Returns:
        Validated payload matching domain-ready loan attributes.
    """

    loan_id: str = Field(default_factory=lambda: f"API-{uuid.uuid4().hex[:8].upper()}")
    gender: Literal["Male", "Female"]
    married: Literal["Yes", "No"]
    dependents: Literal["0", "1", "2", "3+"]
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    applicant_income: float = Field(ge=0)
    coapplicant_income: float = Field(ge=0)
    loan_amount: float = Field(gt=0)
    loan_amount_term: float = Field(gt=0)
    credit_history: Literal[0, 1]
    property_area: Literal["Urban", "Semiurban", "Rural"]


class BatchEvaluationRequest(BaseModel):
    """Represent a bounded batch payload for multi-application evaluation.

    Returns:
        Validated list of applications with size limits.
    """

    applications: list[LoanEvaluationRequest] = Field(min_length=1, max_length=500)
