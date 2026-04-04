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

Execution status:
- Phase 4b persistence layer is implemented and stable under SQL-default runtime policy.
- Phase 4c API exposure is currently in progress.
- `src/audit_logger.py` remains active but is pending progressive deprecation as SQL persistence modules are completed.

Documentation rule:
- Follow `docs/context/06_code_conventions.md` for module-level executive docstrings, technical docstrings on functions/classes, and sparse imperative critical comments.
