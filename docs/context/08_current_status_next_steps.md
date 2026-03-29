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
- Current test run status: `pytest -q` -> 40 passed.
- Sonar-focused quality fixes are applied: explicit `sonar.python.version=3.13` in `sonar-project.properties` and float-comparison hardening with `pytest.approx(...)` in tests.

Pending (prioritized):
1. Merge PR #7 to close Issue #3 in `main` and re-run Sonar analysis on target branch.
2. Batch evaluation on the cleaned dataset and comparison against bootstrap `loan_status` baseline.
3. Audit module with persistence in `.jsonl` or SQLite.
4. Phase 3 complementary ML with `scikit-learn`.
5. Phase 4 REST API with FastAPI.
6. Docker packaging for final README delivery.

Open decisions:
- Decide whether batch runner belongs in `notebooks/` or `src/batch_evaluator.py`.
- Decide the audit log destination.
- Decide whether ML replaces soft rules or is added as a new scored rule.
