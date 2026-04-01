# 05. Audit Module

Status:
- JSONL baseline is implemented and active; SQL persistence transition is in progress under Phase 4b.

Implemented components:
- `src/audit_logger.py` provides reusable JSONL persistence helpers.
- Decision logging is available via `log_decision_jsonl(...)` and `build_decision_audit_record(...)`.
- Batch evaluation now supports decision-level JSONL rows plus a batch performance record.
- Data pipeline execution now logs file-processing performance metrics to JSONL.
- `src/db/schema.py` now defines SQLAlchemy Core tables for loan applications and audit artifacts.
- `src/db/database.py` now provides engine creation, URL resolution, and schema initialization helpers.
- `src/db/repositories/loan_repo.py` and `src/db/repositories/audit_repo.py` now provide SQL persistence operations for loan rows, evaluations, rule traces, and data-load metrics.
- `src/batch_evaluator.py` now supports optional SQL dual-write using repositories while preserving JSONL compatibility.
- `src/data_loader.py` now supports optional SQL dual-write for pipeline performance records.

Decisions already made:
- Traceability is provided by `DecisionResult.rules_triggered` and summary fields.
- JSONL remains the active runtime path during migration, but long-term persistence direction is SQL-based.

Minimum expected log fields:

```text
timestamp, applicant_id, approved, score, hard_rejection,
rules_triggered (JSON), model_version
```

Pending decision:
- Final migration sequencing for single-decision flow from `src/audit_logger.py` to SQL persistence and deprecation policy cutoff.
