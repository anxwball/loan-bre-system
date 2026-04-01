"""Define the SQLAlchemy Core schema for the Phase 4b persistence layer.

This module centralizes table metadata for the loan decision persistence model
using SQLAlchemy Core only (no ORM declarative models). It defines the
foundational relational schema required before API and repository integration in
Phase 4b. Connection setup and schema creation are intentionally out of scope
for this module and belong to `src/db/database.py`.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    func,
)

metadata = MetaData()

loan_applications = Table(
    "loan_applications",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("loan_id", Text, unique=True, nullable=False),
    Column("applicant_id", Text, nullable=False),
    Column("gender", Text, nullable=True),
    Column("married", Text, nullable=True),
    Column("dependents", Text, nullable=True),
    Column("education", Text, nullable=False),
    Column("self_employed", Text, nullable=True),
    Column("applicant_income", Integer, nullable=False),
    Column("coapplicant_income", Float, nullable=False),
    Column("loan_amount", Float, nullable=False),
    Column("loan_amount_term", Float, nullable=True),
    Column("credit_history", Float, nullable=True),
    Column("property_area", Text, nullable=False),
    Column("loan_status", Text, nullable=True),
    Column("total_income", Float, nullable=False),
    Column("loan_to_income_ratio", Float, nullable=False),
    Column("loaded_at", DateTime, nullable=False, server_default=func.now()),
    Column("source_file", Text, nullable=True),
)

audit_evaluations = Table(
    "audit_evaluations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "loan_application_id",
        Integer,
        ForeignKey("loan_applications.id"),
        nullable=False,
    ),
    Column("evaluated_at", DateTime, nullable=False, server_default=func.now()),
    Column("decision", Text, nullable=False),
    Column("risk_score", Integer, nullable=False),
    Column("hard_rejection", Integer, nullable=False),
    Column("review_flag", Integer, nullable=False),
    Column("reasons", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("batch_id", Text, nullable=True),
    CheckConstraint("mode IN ('single', 'batch')", name="ck_audit_eval_mode"),
)

audit_rule_traces = Table(
    "audit_rule_traces",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("evaluation_id", Integer, ForeignKey("audit_evaluations.id"), nullable=False),
    Column("rule_id", Text, nullable=False),
    Column("rule_type", Text, nullable=False),
    Column("criterion_ref", Text, nullable=True),
    Column("triggered", Integer, nullable=False),
    Column("points", Integer, nullable=True),
    Column("reason", Text, nullable=False),
    CheckConstraint("rule_type IN ('hard', 'soft')", name="ck_rule_trace_type"),
)

audit_data_loads = Table(
    "audit_data_loads",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("loaded_at", DateTime, nullable=False, server_default=func.now()),
    Column("filepath", Text, nullable=False),
    Column("processed_rows", Integer, nullable=False),
    Column("file_processing_seconds", Float, nullable=False),
    Column("rows_per_second", Float, nullable=False),
)

Index("ix_audit_evaluations_loan_application_id", audit_evaluations.c.loan_application_id)
Index("ix_audit_evaluations_batch_id", audit_evaluations.c.batch_id)
Index("ix_audit_evaluations_decision", audit_evaluations.c.decision)

Index("ix_audit_rule_traces_evaluation_id", audit_rule_traces.c.evaluation_id)
Index("ix_audit_rule_traces_rule_id", audit_rule_traces.c.rule_id)
Index(
    "ix_audit_rule_traces_rule_type_triggered",
    audit_rule_traces.c.rule_type,
    audit_rule_traces.c.triggered,
)

__all__ = [
    "metadata",
    "loan_applications",
    "audit_evaluations",
    "audit_rule_traces",
    "audit_data_loads",
]
