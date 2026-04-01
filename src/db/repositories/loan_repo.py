"""Provide SQLAlchemy Core persistence helpers for loan applications.

This repository encapsulates CRUD-oriented access patterns for
`loan_applications` using SQLAlchemy Core and explicit table metadata.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, insert, select

from src.db.database import begin_connection
from src.db.schema import loan_applications
from src.loan_application import LoanApplication


class LoanRepository:
    """Persist and query loan application records.

    Args:
        engine: SQLAlchemy engine used by repository operations.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def insert_application(
        self,
        app: LoanApplication,
        applicant_id: str,
        source_file: str | None = None,
        loan_status: str | None = None,
    ) -> int:
        """Insert one loan application row and return its database identifier.

        Args:
            app: Domain object evaluated by the BRE.
            applicant_id: Stable applicant identifier for persistence.
            source_file: Optional source artifact path for lineage.
            loan_status: Optional historical status label for benchmarking.

        Returns:
            Inserted primary key from `loan_applications`.
        """

        payload = {
            "loan_id": app.loan_id,
            "applicant_id": applicant_id,
            "gender": app.gender,
            "married": app.married,
            "dependents": app.dependents,
            "education": app.education,
            "self_employed": app.self_employed,
            "applicant_income": int(app.applicant_income),
            "coapplicant_income": float(app.coapplicant_income),
            "loan_amount": float(app.loan_amount),
            "loan_amount_term": float(app.loan_amount_term),
            "credit_history": float(app.credit_history),
            "property_area": app.property_area,
            "loan_status": loan_status,
            "total_income": float(app.total_income),
            "loan_to_income_ratio": float(app.loan_to_income_ratio),
            "source_file": source_file,
        }

        with begin_connection(self._engine) as connection:
            result = connection.execute(insert(loan_applications).values(**payload))

        inserted_id = result.inserted_primary_key[0]
        if inserted_id is None:
            raise RuntimeError("Loan application insert did not return a primary key.")

        return int(inserted_id)

    def get_by_loan_id(self, loan_id: str) -> dict[str, Any] | None:
        """Fetch one persisted loan application by its business identifier.

        Args:
            loan_id: Business loan identifier.

        Returns:
            Dictionary payload when the row exists; otherwise None.
        """

        statement = select(loan_applications).where(loan_applications.c.loan_id == loan_id)

        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()

        return dict(row) if row is not None else None

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """List recently loaded loan applications ordered by insertion id.

        Args:
            limit: Maximum number of rows to return.

        Returns:
            Ordered list of persisted loan application dictionaries.
        """

        effective_limit = max(limit, 1)
        statement = (
            select(loan_applications)
            .order_by(loan_applications.c.id.desc())
            .limit(effective_limit)
        )

        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        return [dict(row) for row in rows]
