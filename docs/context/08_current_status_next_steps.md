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
- Issue #1 deterministic approval criteria are now documented in `docs/context/11_approval_criteria.md` as the single source of truth for Issue #2 design.
- `LoanApplication` invariants now block `loan_amount == 0` and `loan_amount_term <= 0` in `__post_init__`.

Phase 2 status snapshot:
- `LoanApplication` with domain invariants in `__post_init__` is implemented.
- BRE first version with 3 hard rules and 8 soft rules is implemented in `src/bre_rules.py`.
- `RuleEngine` flow with traceable `DecisionResult` is implemented in `src/bre_engine.py`.
- Issue #3 test suite is implemented with modular coverage in `tests/conftest.py`, `tests/test_rule_engine_decisions.py`, `tests/test_bre_rules.py`, `tests/test_loan_application.py`, and `tests/test_integral_dataset_flow.py`.
- Batch evaluation module is implemented in `src/batch_evaluator.py` with baseline comparison against `data/processed/loan_labels.csv` and row-level output support.
- Audit logging baseline is implemented in `src/audit_logger.py` with JSONL persistence for decision and batch flows.
- Batch evaluator now emits a versioned batch audit artifact and includes file-processing performance metrics.
- Data pipeline now exposes file-processing performance attributes and logs them to `data/audit/file_processing_latest.jsonl`.
- Decision score is now clamped to a non-negative floor (`score >= 0`) after compensatory soft rules.
- Current test run status: `pytest -q` -> 48 passed.
- Sonar-focused quality fixes are applied: explicit `sonar.python.version=3.13` in `sonar-project.properties` and float-comparison hardening with `pytest.approx(...)` in tests.
- Phase 2 implementation is complete on `main`; current execution focus is Phase 4b persistence enablement as a prerequisite for API exposure.

Pending (prioritized):
1. Phase 4b persistence layer (active):
	- SQLAlchemy Core schema in `src/db/schema.py` is implemented in the current session.
	- DB connection module in `src/db/database.py` is implemented in the current session.
	- Repositories under `src/db/repositories/` are implemented in the current session.
	- `src/batch_evaluator.py` now supports optional SQL dual-write for evaluations, traces, and performance metrics.
	- `src/data_loader.py` now supports optional SQL dual-write for pipeline performance metrics.
	- Remaining step: migrate single-decision audit writes from `src/audit_logger.py` to SQL and complete progressive deprecation.
2. Phase 3 complementary ML with `scikit-learn`.
3. Phase 4 REST API with FastAPI.
4. Docker packaging for final README delivery.

Open decisions:
- Define migration sequencing between JSONL and SQL persistence during Phase 4b.
- Decide whether ML replaces soft rules or is added as a new scored rule.
