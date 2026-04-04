# 12. Session Protocol

Purpose:
- Make context updates consistent across sessions by enforcing a minimal-diff workflow.
- Prevent branch collisions between mainline documentation and branch-specific implementation work.

Source:
- Prompt asset: `docs/prompts/v.1.1.0/lifecycle_template.md`.
- Section: `Context Update Protocol`.

Mandatory pre-phase flow:
1. Identify the active phase and project for the current session.
2. Review the current context baseline (`CLAUDE.md`, prior phase outputs, open issues).
3. Detect deltas since the previous session in:
   - scope or requirements
   - architecture decisions
   - stack or dependencies
   - active phase or next steps
4. If there are deltas, propose a minimal context patch and label each item as `UPDATE`, `ADD`, or `REMOVE`.
5. Do not apply context edits until explicit user confirmation is received.
6. After approval, apply only the confirmed patch items.

Documentation layers (canonical):
- External/mainline docs (human entry and release communication):
   - `README.md`
   - `CHANGELOG.md`
   - `docs/releases/README.md`
- Internal/assistant docs (operational context and continuity):
   - `docs/context/*`

Branch isolation policy:
- Keep branch-specific implementation artifacts outside `main` until merge readiness.
- Do not introduce branch-only implementation files into `main` during documentation-only sessions.
- Current example: API-layer artifacts remain branch-scoped (`src/api/`, `tests/test_api_*.py`) until release-ready integration.
- Keep `main` documentation as canonical roadmap truth; represent branch differences as explicit deltas.

Feature-branch start checklist:
1. Sync branch baseline from `main`.
2. Confirm canonical phase naming in `docs/context/08_current_status_next_steps.md`.
3. Classify intended changes as:
    - Mainline-canonical documentation updates
    - Branch-scoped implementation updates
4. Keep both change classes in separate commits.

Feature-branch close checklist:
1. Update `docs/context/10_session_history.md` with branch delta notes.
2. Update `docs/context/DECISIONS.md` only when decision status changes.
3. Avoid rewriting canonical mainline docs unless the change is roadmap-level.

Pre-merge anti-collision checklist:
1. Split code and documentation commits.
2. Ensure phase naming aligns with canonical roadmap labels.
3. Verify `main` does not carry branch-only implementation files.
4. Resolve doc conflicts by preserving canonical `main` semantics and keeping branch details in session history.

Operational constraints:
- Never rewrite the full context for convenience.
- Patch forward and preserve all still-valid decisions.
- Record session closure updates in `docs/context/10_session_history.md`.
- Register cross-module pending decisions in `docs/context/DECISIONS.md`.
- Use `docs/prompts/v.1.1.0/session_changelog_template.md` as the default closeout format.
