# 12. Session Protocol

Purpose:
- Make context updates consistent across sessions by enforcing a minimal-diff workflow.

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

Operational constraints:
- Never rewrite the full context for convenience.
- Patch forward and preserve all still-valid decisions.
- Record session closure updates in `docs/context/10_session_history.md`.
