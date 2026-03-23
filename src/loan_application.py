
"""Represent a BRE-ready loan application with derived financial fields.

This module defines the domain input object used by the Business Rules Engine.
It stores applicant and loan request attributes, enforces invariants, and derives
`total_income` plus `loan_to_income_ratio` during initialization.
"""

from dataclasses import dataclass, field

@dataclass
class LoanApplication:
    """Store canonical loan attributes and enforce core invariants.

    Args:
        loan_id: Unique identifier of the loan application.
        gender: Applicant gender category.
        married: Applicant marital status.
        dependents: Number-of-dependents category.
        education: Education category.
        self_employed: Self-employment category.
        applicant_income: Applicant monthly income.
        coapplicant_income: Co-applicant monthly income.
        loan_amount: Requested loan amount.
        loan_amount_term: Loan repayment term.
        credit_history: Credit history flag, expected values are 0 or 1.
        property_area: Property area category.

    Returns:
        LoanApplication instance with derived `total_income` and
        `loan_to_income_ratio` fields.
    """
    loan_id: str
    gender: str
    married: str
    dependents: str
    education: str
    self_employed: str
    applicant_income: float
    coapplicant_income: float
    loan_amount: float
    loan_amount_term: float
    credit_history: int
    property_area: str
    total_income: float = field(init=False)
    loan_to_income_ratio: float = field(init=False)

    def __post_init__(self):
        """Validate invariants and derive aggregate financial fields.

        Returns:
            None.

        Raises:
            ValueError: If any numeric invariant is violated.
            ValueError: If loan_amount is zero.
            ValueError: If loan_amount_term is zero or negative.
        """
        if self.applicant_income < 0:
            raise ValueError("Applicant income cannot be negative.")
        if self.coapplicant_income < 0:
            raise ValueError("Co-applicant income cannot be negative.")
        if self.loan_amount < 0:
            raise ValueError("Loan amount cannot be negative.")
        if self.credit_history not in (0, 1):
            raise ValueError("Credit history must be either 0 or 1.")
        if self.loan_amount == 0:
            raise ValueError("Loan amount must be greater than zero.")
        if self.loan_amount_term <= 0:
            raise ValueError("Loan term must be a positive number of months.")

        self.total_income = self.applicant_income + self.coapplicant_income
        if self.total_income <= 0:
            raise ValueError("Total income must be greater than zero.")

        self.loan_to_income_ratio = self.loan_amount / self.total_income