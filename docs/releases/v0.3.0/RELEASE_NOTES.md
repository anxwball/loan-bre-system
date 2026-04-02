# Release v0.3.0

## Executive Summary

Version `v0.3.0` consolidates the transition from a baseline BRE prototype to a production-oriented decision core with traceability, modular quality gates, batch benchmarking, and SQL persistence foundations (Phase 4b).

This release is built from `main` to avoid mixing in ongoing `v0.4.0` API-surface work.

## Release Boundary

- Previous release: `v0.2.0` (`d09ecbe`)
- Release baseline branch: `main`
- Release target commit on `main`: `91f6e84`
- Included Phase cutoff: through Phase 4b persistence enablement
- Excluded work: branch `feat/phase-4c-fastapi-layer` (ongoing `v0.4.0`)

## Requirement-to-Delivery Trace

- Issue #1 (deterministic approval criteria and domain invariants)
  - Delivered through criteria formalization and invariant hardening in `LoanApplication`.
- Issue #2 (traceable BRE first implementation)
  - Delivered through `RuleResult` trace model, hard/soft rules, and `DecisionResult` outputs.
- Issue #3 (comprehensive tests)
  - Delivered through modularized tests across rules, decisions, domain invariants, integral flow, audit, batch, and persistence repositories.
- Phase 4b persistence enablement
  - Delivered through SQLAlchemy Core schema, DB bootstrap, repository layer, and runtime integration paths.

## Changelog Entry (Detailed)

### Added

- Deterministic approval criteria source of truth in `docs/context/11_approval_criteria.md`.
- Traceable rules engine implementation in `src/bre_rules.py` and `src/bre_engine.py`.
- Batch comparison evaluator in `src/batch_evaluator.py` for BRE vs historical labels.
- JSONL audit + performance telemetry in `src/audit_logger.py` and `src/data_loader.py`.
- Phase 4b SQL persistence package in `src/db/`:
  - `schema.py` (tables, constraints, indexes)
  - `database.py` (URL resolution, engine lifecycle, schema bootstrap)
  - `repositories/loan_repo.py` and `repositories/audit_repo.py` (persistence operations)
- Repository persistence test coverage in `tests/test_db_repositories.py`.

### Changed

- Risk score handling clamps non-negative final values after soft compensatory points.
- Runtime audit sink policy supports `sql`, `dual`, and `jsonl` with SQL-default progression.
- Batch evaluator logic refactored to reduce cognitive complexity while preserving expected outputs.
- Context protocol formalized for session continuity and controlled doc updates.

### Quality and Validation

- Float assertions hardened using `pytest.approx(...)`.
- Data loader tests refactored to remove duplicated setup patterns.
- Focused test runs were recorded during release scope work:
  - Repository tests passed (`3/3`).
  - Audit + batch + pipeline migration tests passed (`11/11`).

## Technical Debt

| Item | Priority | Resolution Phase |
|---|---|---|
| Retire legacy JSONL wrappers after stabilization window | High | Phase 4c/4d |
| Define formal cutoff signoff checklist for `audit_mode` migration | High | Phase 4c |
| Add migration scripts for historical JSONL to SQL backfill | Medium | Phase 4d |
| Expand integration tests over API + persistence transaction boundaries | Medium | Phase 4c |

## Lessons Learned

### What Worked (3)

1. Designing rule traceability first made debugging and validation faster.
2. Splitting tests by responsibility lowered regression risk during refactors.
3. Introducing SQL persistence with compatibility modes reduced migration risk.

### What to Improve (3)

1. Reduce oversized commits by slicing Phase 4b changes into narrower PR increments.
2. Add release-candidate full-suite gates before final tagging.
3. Define release artifact templates earlier to avoid end-of-cycle documentation compression.

## Proposed Scope for v0.4.0

1. Complete FastAPI surface (auth, evaluate, audit routes) on top of Phase 4b persistence.
2. Stabilize SQL-first runtime and execute JSONL deprecation checkpoint.
3. Add API-focused test coverage and quality gates (contract + integration).
4. Prepare deployment baseline and operational runbook updates.
