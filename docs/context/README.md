# Multi-AI Context System

This directory replaces the old monolithic context file with a modular system that can be reused across future sessions.

Goals:
- Reuse the same context across multiple AI assistants.
- Keep section-level traceability.
- Simplify maintenance and incremental updates.

Structure:
- `00_meta.md`: scope, ownership, and update rules.
- `01_developer_profile.md` to `11_approval_criteria.md`: modular context sections.
- `10_session_history.md`: working log and session continuity.
- `agents/`: AI-specific adapters.

Recommended load order:
1. `00_meta.md`
2. `01_developer_profile.md`
3. `02_project_identity.md`
4. `03_architecture_modules.md`
5. `04_bre_module.md`
6. `05_audit_module.md`
7. `06_code_conventions.md`
8. `07_ai_assistant_rules.md`
9. `08_current_status_next_steps.md`
10. `09_glossary.md`
11. `11_approval_criteria.md`
12. `10_session_history.md`

Language convention:
- All internal context and instruction files are written in English for standardization and better token processing.
- The only Spanish documentation file is the project root `README.md`.

Maintenance:
- Update `10_session_history.md` at the end of every session.
- Keep business decisions in their original modules.
- Avoid duplicated content across modules.
