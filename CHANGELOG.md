# Changelog

All notable changes to this project are documented in this file.

This repository follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

## [Unreleased]

### Added
- FastAPI API surface integrated on `main` with role-aware routes for auth, evaluation, audit, and analyst queue (`src/api/`).
- API-focused automated tests added to mainline regression suite (`tests/test_api_auth.py`, `tests/test_api_evaluate.py`, `tests/test_api_audit.py`).

### Changed
- API router signatures aligned with FastAPI `Annotated` dependency style for role guard dependencies.
- Redundant `response_model` declarations removed where return type annotations already define response contracts.

### Quality
- API test setup deduplicated through shared fixtures in `tests/conftest.py`.
- Mainline validation snapshot updated: `pytest` -> 62 passed.

## [0.3.0] - 2026-04-02

### Release Cut
- Base release: `v0.2.0` (`d09ecbe`)
- Target baseline: `main` at `91f6e84`
- Scope boundary: includes all changes up to Phase 4b persistence enablement
- Explicitly excluded: ongoing `v0.4.0` API-forward work on branch `feat/phase-4c-fastapi-layer`

### Added
- Deterministic approval criteria formalized and linked to domain invariants (`docs/context/11_approval_criteria.md`, `src/loan_application.py`).
- First traceable BRE implementation with explicit hard/soft rule traces (`src/bre_rules.py`, `src/bre_engine.py`).
- Modular test suite expansion across decision flow, rule behavior, domain invariants, and integral dataset path (`tests/`).
- Batch evaluator for BRE vs historical baseline with row-level outputs and aggregate metrics (`src/batch_evaluator.py`).
- JSONL audit logging and performance telemetry for batch and data pipeline paths (`src/audit_logger.py`, `src/data_loader.py`).
- Phase 4b SQL persistence layer with SQLAlchemy Core schema, engine/bootstrap utilities, and repositories (`src/db/`).

### Changed
- BRE scoring pipeline now clamps non-negative final score after compensatory rules.
- Runtime audit policy now supports explicit sink modes (`sql`, `dual`, `jsonl`) with SQL-default progression paths.
- Batch evaluation flow was refactored to lower cognitive complexity while preserving behavior (`src/batch_evaluator.py`).

### Quality
- Sonar alignment updates: `pytest.approx(...)` for float assertions and reduced duplicated test setup.
- Additional repository-layer persistence tests for Phase 4b database operations.

### Documentation
- Context protocol operationalized with lifecycle template and session continuity rules.
- README and context modules synchronized with BRE-first scope and persistence progress.

## [0.2.0] - 2026-03-22

### Release Cut
- Base release: `v0.1.0` (`d4693e6`)
- Target baseline: `main` at `d09ecbe`
- Scope boundary: bootstrap completion for Issue #1 and BRE-first documentation realignment

### Added
- Modular context system under `docs/context/` including architecture, glossary, status, and session history sections.
- Context adapters in `docs/context/agents/` and compatibility gateway in `CLAUDE.md`.
- Governed label artifacts under `data/labels/` and `data/processed/loan_labels.csv`.

### Changed
- Data processing flow was refactored in `src/data_loader.py` to support canonical schema normalization and label split strategy.
- `notebooks/eda_analysis.py` was aligned to the updated processed-data and benchmark-label workflow.
- `README.md` and context files were synchronized to a BRE-first project scope.
- Legacy raw source file policy was updated, replacing tracked `data/raw/loans_data.csv` with the new workflow contract.

### Documentation
- Documentation quality policy formalized in `docs/context/06_code_conventions.md`.
- Session continuity operating model established in `docs/context/10_session_history.md`.

## [0.1.0] - 2026-03-16

### Release Cut
- Base baseline: repository initial commit (`4080306`)
- Target baseline: `main` at `d4693e6`
- Scope boundary: Phase-1 EDA bootstrap and project packaging

### Added
- Baseline data pipeline implementation in `src/data_loader.py`.
- Exploratory workflow in `notebooks/eda_analysis.py`.
- Initial datasets in `data/raw/` and `data/processed/`.
- Packaging and dependency manifests (`pyproject.toml`, `requirements.txt`).
- First project `README.md` version with setup and context.

### Changed
- `.gitignore` policy refined for generated graph artifacts and versioned processed outputs.
- README scope wording and execution terminology refined (`d4693e6`).

### Quality
- Baseline functionality validated through deterministic pipeline outputs; formal automated tests were introduced in later releases.
