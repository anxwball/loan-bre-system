# CLAUDE.md - Loan BRE System Context Gateway

This file is a compatibility gateway for Claude-style workflows.
The canonical project context is now modularized under `docs/context/`.

Use this loading order:
1. `docs/context/README.md`
2. Load modules in the canonical order defined by `docs/context/README.md`.
3. Ensure `docs/context/12_session_protocol.md` is applied before phase-oriented work.
4. Update `docs/context/10_session_history.md` at the end of each session.

Language convention:
- Internal context and instruction files are maintained in English.
- The root `README.md` is intentionally kept in Spanish.

Operational rule:
- Update `docs/context/10_session_history.md` at the end of each work session.
- Keep branch-only implementation artifacts outside `main` until merge readiness.
- Current example: API artifacts (`src/api/`, `tests/test_api_*.py`) remain branch-scoped until integration.

Execution status:
- Phase 3 persistence layer is implemented and stable under SQL-default runtime policy.
- Phase 4 API exposure is currently in progress.
- `src/audit_logger.py` remains active but is pending progressive deprecation as SQL persistence modules are completed.

Phase naming alignment:
- Phase 3 (canonical on `main`) and historical Phase 4b labels refer to the same SQLAlchemy/SQLite persistence scope.
- `main` and release `v0.3.0` use Phase 3 naming due to roadmap reordering.
- Feature-branch traces may still reference Phase 4b as the first persistence implementation that enabled active API progress.

Documentation rule:
- Follow `docs/context/06_code_conventions.md` for module-level executive docstrings, technical docstrings on functions/classes, and sparse imperative critical comments.
