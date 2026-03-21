# Claude Adapter

Goal:
- Use the modular context system as the replacement for the original monolithic file.

Load instructions for Claude:
1. Read `docs/context/README.md`.
2. Load modules `00` to `10` in the recommended order.
3. Prioritize `07_ai_assistant_rules.md` for response style and constraints.

Language policy:
- Keep internal context and instruction artifacts in English.
- Keep only the root `README.md` in Spanish.

Note:
- This adapter preserves compatibility with workflows that still reference `CLAUDE.md`.
