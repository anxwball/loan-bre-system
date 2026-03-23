# 10. Session History

## 2026-03-22
- Issue #1 domain invariants were finalized in `src/loan_application.py` by enforcing `loan_amount == 0` as invalid and `loan_amount_term <= 0` as invalid.
- Approval criteria context file was normalized from a placeholder name to `docs/context/11_approval_criteria.md` and aligned internally with section number 11.
- Context loading indexes were updated in `CLAUDE.md` and `docs/context/README.md` to include `11_approval_criteria.md` before session history.
- Coherence alignment was added across context modules: `docs/context/04_bre_module.md` now marks prior rules as pre-finalization draft and references `11_approval_criteria.md` as the formal source for Issue #2.
- `docs/context/08_current_status_next_steps.md` was updated to mark Issue #1 documentation closure and reprioritize remaining work from Issue #2 onward.

## 2026-03-22
- Documentation scope was updated to prioritize BRE functionality over exhaustive EDA analysis.
- Bootstrap labels were formally accepted as the current benchmark baseline to continue Issue #1 pragmatically.
- Root `README.md` and `docs/context/08_current_status_next_steps.md` were aligned with this decision.
- Next execution focus remains BRE implementation and benchmark evaluation flow.
- Clarification: current EDA execution path is pipeline-from-raw plus in-memory label merge for plots; the previous processed-first note is historical and no longer the active behavior.

## 2026-03-22
- Refactored `src/data_loader.py` to a strict function-chained pipeline and removed deprecated feature/label derivations to keep labels historical-only.
- Confirmed canonical schema normalization (`applicant_income`, `coapplicant_income`, `loan_amount`) and explicit label split (`loan_labels.csv`) before saving feature data.
- Next step: implement Issue #2 by wiring the first traceable BRE rule set and engine flow against the cleaned feature dataset.

## 2026-03-22
- Issue #1 implementation started and aligned with repository backlog order (#1 -> #2 -> #3).
- `src/data_loader.py` was updated with `rename_columns()` to canonicalize legacy column names to snake_case (`applicant_income`, `coapplicant_income`, `loan_amount`).
- `split_labels()` was added to persist benchmark labels into `data/processed/loan_labels.csv` and return a feature-only DataFrame without `loan_status`.
- `add_basic_features()` was converted into a placeholder hook that returns the input unchanged, because `total_income` and `loan_to_income_ratio` are now domain-derived in `LoanApplication` and `loan_status` is benchmark-only.
- Processed output persistence was standardized to the canonical file `data/processed/loans_cleaned.csv`.
- `notebooks/eda_analysis.py` pipeline was updated to raw -> clean -> split labels -> save processed features -> plot, and the raw input path was aligned to `data/raw/loan_train.csv`.
- Plotting functions were made resilient when `loan_status` or ratio-derived fields are unavailable in feature-only processed datasets.
- `notebooks/eda_analysis.py` was then updated to a processed-first I/O flow: EDA now loads `data/processed/loans_cleaned.csv` as the default base input, bootstraps from raw only when missing, and optionally merges `data/processed/loan_labels.csv` for target-based visualizations.
- `src/data_loader.py` was refactored to an explicit Pipeline Pattern with `run_pipeline(input_path)` chaining: `load_raw_data -> clean_data -> rename_columns -> add_basic_features -> split_labels -> save_processed_data`.
- Schema normalization was decoupled from cleaning: `clean_data()` now focuses on lowercase + imputation, while `rename_columns()` is an explicit dedicated step.
- `save_processed_data()` now defaults to `data/processed/loans_cleaned.csv` while preserving optional versioned snapshots.
- `notebooks/eda_analysis.py` was simplified to orchestration-only behavior: `run_eda()` now calls `run_pipeline()` once and sends the returned DataFrame to `plot_all()`.

## 2026-03-21
- Full 4-phase project architecture was designed and the professional technical stack was defined.
- Phase 1 was fully implemented: EDA pipeline with `data_loader.py`, 5 visualizations, and packaging with `pyproject.toml`; first commit and LinkedIn post were published.
- Phase 2 (BRE, rules, engine, tests) was fully designed with implementation-ready code; user stories and `CLAUDE.md` were created and aligned with the developer portfolio roadmap.
- The context system was standardized in English: modular files were renamed to English, adapters were translated, and language policy was made explicit (only root `README.md` remains in Spanish).
- Source documentation quality was improved in `src/data_loader.py` with a module executive docstring, technical function docstrings, and sparse imperative critical comments.
- Documentation policy was formalized in `docs/context/06_code_conventions.md` and referenced from `CLAUDE.md`.
- Source documentation quality was also improved in `notebooks/eda_analysis.py` with the same policy: module executive docstring, technical function docstrings, and sparse critical comments.

## 2025-03-17
- Full 4-phase project architecture was designed and the professional technical stack was defined.
- Phase 1 was fully implemented: EDA pipeline with `data_loader.py`, 5 visualizations, and project packaging via `pyproject.toml`; first commit and LinkedIn post were completed.
- Phase 2 (BRE, rules, engine, tests) was fully designed with implementation-ready code, pending execution.
