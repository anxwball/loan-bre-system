# 08. Current Status and Next Steps

Phase status quick reference:

| Phase | Scope | Status | Latest note |
|---|---|---|---|
| Phase 1 | EDA and data baseline | Complete | Stable |
| Phase 2 | BRE v1 + tests | Complete | Stable |
| Phase 4b | SQL persistence migration | Complete | SQL default active |
| Phase 4c | FastAPI exposure | In progress | Scaffolding started (2026-04-02) |
| Phase 3 | Complementary ML (`scikit-learn`) | Pending | Not started |

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
- Phase 2 implementation is complete on `main`; Phase 4b persistence baseline was released as `v0.3.0` on `main` (`91f6e84` tag baseline).
- Current `main` scope is stabilized around `v0.3.0`; Phase 4c API work is intentionally tracked outside this baseline until merge/release readiness.

Pending (prioritized):
1. Phase 4c REST API with FastAPI (active outside `main` baseline):
	- Continue implementation on dedicated branch until release-ready integration.
	- Keep `main` constrained to `v0.3.0` baseline until API quality gates are met.
2. Phase 4b persistence stabilization follow-up:
	- Remove legacy JSONL paths after stabilization window and backward-compatibility signoff.
3. Phase 3 complementary ML with `scikit-learn`.
4. Docker packaging for final README delivery.

Open decisions:
- D01 (`docs/context/DECISIONS.md`): Define legacy JSONL removal milestone after stabilization and backward-compatibility signoff.
- D02 (`docs/context/DECISIONS.md`): Decide whether ML replaces soft rules or is added as a new scored rule.
