# 08. Current Status and Next Steps

Working:
- Complete project structure with professional packaging.
- EDA pipeline refactored to explicit Pipeline Pattern orchestration:
	`load_raw_data -> clean_data -> rename_columns -> add_basic_features -> split_labels -> save_processed_data`.
- Column canonicalization is enforced before persistence (`applicant_income`, `coapplicant_income`, `loan_amount`).
- Historical benchmark label handling is isolated via `split_labels()` into `data/processed/loan_labels.csv`; feature output excludes `loan_status`.
- EDA orchestration now calls `run_pipeline()` once and plots only from the returned processed features DataFrame.
- Bootstrap labels strategy is accepted as the current baseline to accelerate BRE development.
- Scope decision: exhaustive data analysis is out of scope for now; BRE functionality and traceability are the immediate priority.
- First commit and LinkedIn post published (Phase 1).
- Issue #1 baseline completed in pipeline: column canonicalization (`applicant_income`, `coapplicant_income`, `loan_amount`) and label split (`loan_labels.csv`) for benchmark-only `loan_status`.

Phase 2 status snapshot:
- `LoanApplication` with domain invariants in `__post_init__` is implemented.
- BRE with 3 hard rules and 8 soft rules is designed but not implemented.
- `RuleEngine` with full flow and traceable `DecisionResult` is designed but not implemented.
- Unit test suite with fixtures (`pytest tests/ -v`) is pending implementation.

Pending (prioritized):
1. Finalize Issue #1 closure checklist with frozen bootstrap baseline and documented benchmark policy.
2. Implement first traceable BRE rules and engine flow (Issue #2).
3. Add unit tests for approval/denial/borderline scenarios (Issue #3).
4. Batch evaluation on the cleaned dataset and comparison against bootstrap `loan_status` baseline.
5. Audit module with persistence in `.jsonl` or SQLite.
6. Phase 3 complementary ML with `scikit-learn`.
7. Phase 4 REST API with FastAPI.
8. Docker packaging for final README delivery.

Open decisions:
- Decide whether batch runner belongs in `notebooks/` or `src/batch_evaluator.py`.
- Decide the audit log destination.
- Decide whether ML replaces soft rules or is added as a new scored rule.
