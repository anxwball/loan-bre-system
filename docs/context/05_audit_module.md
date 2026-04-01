# 05. Audit Module

Status:
- SQL persistence is now the default runtime path; JSONL remains as legacy compatibility mode during deprecation.

Implemented components:
- `src/audit_logger.py` provides reusable JSONL persistence helpers.
- `src/audit_logger.py` now supports optional SQL dual-write for single-decision persistence.
- Decision logging is available via `log_decision_jsonl(...)` and `build_decision_audit_record(...)`.
- Batch evaluation now supports decision-level JSONL rows plus a batch performance record.
- Data pipeline execution now logs file-processing performance metrics to JSONL.
- `src/db/schema.py` now defines SQLAlchemy Core tables for loan applications and audit artifacts.
- `src/db/database.py` now provides engine creation, URL resolution, and schema initialization helpers.
- `src/db/repositories/loan_repo.py` and `src/db/repositories/audit_repo.py` now provide SQL persistence operations for loan rows, evaluations, rule traces, and data-load metrics.
- `src/batch_evaluator.py` now supports optional SQL dual-write using repositories while preserving JSONL compatibility.
- `src/data_loader.py` now supports optional SQL dual-write for pipeline performance records.
- Runtime audit policy now supports explicit modes (`sql`, `dual`, `jsonl`) with SQL as default.

Decisions already made:
- Traceability is provided by `DecisionResult.rules_triggered` and summary fields.
- SQL is the active default runtime path; JSONL remains an explicit legacy compatibility mode (`audit_mode=jsonl` or `audit_mode=dual`) during deprecation.

Minimum expected log fields:

```text
timestamp, applicant_id, approved, score, hard_rejection,
rules_triggered (JSON), model_version
```

Pending decision:
- Define removal milestone for JSONL compatibility wrappers after production-parity validation.
