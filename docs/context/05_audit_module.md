# 05. Audit Module

Status:
- Implemented baseline in JSONL with local file persistence.

Implemented components:
- `src/audit_logger.py` provides reusable JSONL persistence helpers.
- Decision logging is available via `log_decision_jsonl(...)` and `build_decision_audit_record(...)`.
- Batch evaluation now supports decision-level JSONL rows plus a batch performance record.
- Data pipeline execution now logs file-processing performance metrics to JSONL.

Decisions already made:
- Traceability is provided by `DecisionResult.rules_triggered` and summary fields.
- JSONL is the approved current storage format for local development and portfolio traceability.

Minimum expected log fields:

```text
timestamp, applicant_id, approved, score, hard_rejection,
rules_triggered (JSON), model_version
```

Pending decision:
- Keep JSONL as final destination or migrate to SQLite/external service for queryability and retention.
