# Claude Adapter

Goal:
- Use the modular context system as the replacement for the original monolithic file.

Load instructions for Claude:
1. Read `docs/context/README.md`.
2. Load all context modules in the exact canonical order defined there.
3. Prioritize `07_ai_assistant_rules.md` for response style and constraints after full context load.
4. Apply `12_session_protocol.md` before phase-oriented work if context may have changed.
5. Update `10_session_history.md` at session close.

Language policy:
- Keep internal context and instruction artifacts in English.
- Keep only the root `README.md` in Spanish.

Note:
- This adapter preserves compatibility with workflows that still reference `CLAUDE.md`.
