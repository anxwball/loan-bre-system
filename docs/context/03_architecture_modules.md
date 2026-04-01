# 03. Architecture and Modules

Expected structure:

```text
loan-bre-system/
|- data/
|  |- raw/                  # Original Kaggle dataset - NEVER modify
|  |- processed/            # Clean CSVs + EDA-generated charts
|- notebooks/
|  |- eda_analysis.py       # Executable EDA script (not Jupyter)
|- src/
|  |- data_loader.py        # Load, inspect, clean, and engineer features
|  |- loan_application.py   # BRE input dataclass + domain invariants
|  |- bre_rules.py          # Individual rules + HARD_RULES / SOFT_RULES
|  |- bre_engine.py         # Orchestrator: LoanApplication -> DecisionResult
|  |- batch_evaluator.py    # Batch BRE-vs-baseline metrics and row-level outputs
|  |- audit_logger.py       # JSONL audit persistence helpers for decision and batch flows
|  |- db/
|  |  |- __init__.py        # Public exports for persistence-layer symbols
|  |  |- schema.py          # SQLAlchemy Core schema for Phase 4b (implemented)
|  |  |- database.py        # Engine and connection factory (planned)
|  |  |- repositories/      # Persistence repositories (planned)
|- tests/
|  |- conftest.py           # Shared fixtures for LoanApplication and RuleEngine
|  |- test_rule_engine_decisions.py
|  |- test_bre_rules.py
|  |- test_loan_application.py
|  |- test_integral_dataset_flow.py
|  |- test_batch_evaluator.py
|  |- test_audit_logger.py
|  |- test_data_loader.py
|- pyproject.toml
|- requirements.txt
|- .gitignore
|- README.md
```

Module relationships:

```text
eda_analysis.py      -> data_loader.py
bre_engine.py        -> bre_rules.py -> loan_application.py
bre_engine.py        -> loan_application.py
test_rule_engine_decisions.py -> bre_engine.py, loan_application.py
test_bre_rules.py             -> bre_rules.py, loan_application.py
test_loan_application.py      -> loan_application.py
test_integral_dataset_flow.py -> bre_engine.py, loan_application.py, data/processed/loans_cleaned.csv
test_batch_evaluator.py       -> batch_evaluator.py, bre_engine.py, loan_application.py
test_audit_logger.py          -> audit_logger.py, bre_engine.py, loan_application.py
test_data_loader.py           -> data_loader.py
src/db/__init__.py            -> src/db/schema.py
```

Import rule:
- Always import from the project root (`from src.module import ...`).
- Runtime code must not use `sys.path` mutation.
- Test bootstrapping may use `tests/conftest.py` path injection when editable install is not guaranteed in local CI/dev shells.

Phase 4b status:
- `src/db/schema.py` is implemented.
- `src/db/database.py` and `src/db/repositories/` remain pending.
