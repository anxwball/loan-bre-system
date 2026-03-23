# CLAUDE.md - Loan BRE System Context Gateway

This file is a compatibility gateway for Claude-style workflows.
The canonical project context is now modularized under `docs/context/`.

Use this loading order:
1. `docs/context/README.md`
2. `docs/context/00_meta.md`
3. `docs/context/01_developer_profile.md`
4. `docs/context/02_project_identity.md`
5. `docs/context/03_architecture_modules.md`
6. `docs/context/04_bre_module.md`
7. `docs/context/05_audit_module.md`
8. `docs/context/06_code_conventions.md`
9. `docs/context/07_ai_assistant_rules.md`
10. `docs/context/08_current_status_next_steps.md`
11. `docs/context/09_glossary.md`
12. `docs/context/11_approval_criteria.md`
13. `docs/context/10_session_history.md`

Language convention:
- Internal context and instruction files are maintained in English.
- The root `README.md` is intentionally kept in Spanish.

Operational rule:
- Update `docs/context/10_session_history.md` at the end of each work session.

Documentation rule:
- Follow `docs/context/06_code_conventions.md` for module-level executive docstrings, technical docstrings on functions/classes, and sparse imperative critical comments.
