# Copilot Adapter

Goal:
- Define how to consume the modular context system in VS Code Copilot sessions.

Load instructions for Copilot:
1. Read `docs/context/README.md`.
2. Load all context modules in the canonical order defined there for full-session work.
3. For quick implementation tasks, prioritize `01`, `03`, `06`, `07`, and `08`, and load `04` and `05` when working on BRE or audit topics.
4. Apply `12_session_protocol.md` before phase-oriented work if context might have changed.
5. Update `10_session_history.md` at session close.

Language policy:
- Internal context and instruction files are maintained in English.
- The root `README.md` remains in Spanish.
