# 05. Audit Module

Status:
- Pending implementation (to be designed in Phase 3 or before API exposure).

Decisions already made:
- Traceability already exists in `DecisionResult.rules_triggered`.
- `DecisionResult.summary()` provides human-readable output.
- Persistent logging (file or database) is still pending.

Minimum expected log fields:

```text
timestamp, applicant_id, approved, score, hard_rejection,
rules_triggered (JSON), model_version
```

Pending decision:
- Define the log destination: `.jsonl`, SQLite, or external service.
