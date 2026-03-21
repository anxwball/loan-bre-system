# 06. Code Conventions

Naming:
- Files and modules: `snake_case.py`
- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Rules: `rule_` prefix + descriptive name
- Rule IDs: `R##` with two digits
- Constants: `UPPER_SNAKE_CASE`

Best practices:
- Public functions and classes must include docstrings (Args and Returns).
- Use `.copy()` before modifying DataFrames.
- Type hints are required for parameters and return values.
- Use section headers with `# === SECTION ===` in long modules.

Structure:
- `src/` for reusable logic.
- `notebooks/` for executable analysis scripts.

Extension patterns:
- New rule: add function in `bre_rules.py` + include in `HARD_RULES` or `SOFT_RULES`.
- New data feature: add a new function in `data_loader.py`.
- New test: use `test_<module>.py` or a dedicated class in `test_bre_engine.py`.
- Reuse pytest fixtures; avoid repeatedly building `LoanApplication` inline.

Language standard:
- Internal docs, context modules, and instruction files are maintained in English.
- The root project `README.md` is the only file intentionally kept in Spanish.
