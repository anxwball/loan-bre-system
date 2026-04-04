# Multi-AI Context System

This directory replaces the old monolithic context file with a modular system that can be reused across future sessions.

Audience:
- Internal documentation for AI assistants and agent-style workflows operating in this repository.

Goals:
- Reuse the same context across multiple AI assistants.
- Keep section-level traceability.
- Simplify maintenance and incremental updates.

Structure:
- `00_meta.md`: scope, ownership, and update rules.
- `01_developer_profile.md` to `11_approval_criteria.md`: modular context sections.
- `12_session_protocol.md`: mandatory pre-phase context-update protocol.
- `10_session_history.md`: working log and session continuity.
- `DECISIONS.md`: centralized registry for cross-module open decisions.
- `agents/`: AI-specific adapters.

Project structure note:
- `src/db/`: Phase 3 persistence module for SQL schema, database connection setup, and repositories.

Terminology note:
- Canonical roadmap naming uses Phase 3 for SQL persistence.
- Historical branch/session traces may still use Phase 4b for the same persistence implementation scope.

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
12. `12_session_protocol.md`
13. `10_session_history.md`

Language convention:
- All internal context and instruction files are written in English for standardization and better token processing.
- The only Spanish documentation file is the project root `README.md`.

Maintenance:
- Update `10_session_history.md` at the end of every session.
- Apply `12_session_protocol.md` before phase-oriented work when context may have changed.
- Register open cross-module decisions in `DECISIONS.md` and mirror final outcomes in the affected source modules.
- Avoid duplicated content across modules.

Branch anti-collision rules:
- Keep `main` as canonical documentation baseline for roadmap semantics and public-facing state.
- Keep branch-specific implementation files outside `main` until merge readiness.
- Current example: API-layer artifacts stay branch-scoped (`src/api/`, `tests/test_api_*.py`) until integration.
- Record branch-specific narrative in `10_session_history.md` instead of rewriting canonical roadmap docs.
- Separate code and documentation commits before merge preparation.

Operational quickstart (internal):

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

Internal navigation shortcuts:

| Goal | File |
|---|---|
| Check current phase and priorities | `08_current_status_next_steps.md` |
| Resume the last session quickly | `10_session_history.md` |
| Review pending cross-module decisions | `DECISIONS.md` |
| Review architecture and module boundaries | `03_architecture_modules.md` |
| Review approval criteria and rule traceability | `11_approval_criteria.md` |
| Review internal coding/documentation conventions | `06_code_conventions.md` |

Daily assistant workflow:
1. Align active phase state with `08_current_status_next_steps.md`.
2. Implement requested updates in source modules.
3. Run targeted tests and then full regression (`pytest -q`) when relevant.
4. If scope or decisions changed, patch only impacted context modules.
5. Close session by updating `10_session_history.md` and decision status in `DECISIONS.md`.

Command shortcuts:

```bash
pytest -q
pytest tests/test_bre_rules.py -q
pytest tests/test_api_evaluate.py -q
python notebooks/eda_analysis.py
```
