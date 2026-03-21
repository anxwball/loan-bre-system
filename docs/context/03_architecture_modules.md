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
|  |- __init__.py
|  |- data_loader.py        # Load, inspect, clean, and engineer features
|  |- loan_application.py   # BRE input dataclass + domain invariants
|  |- bre_rules.py          # Individual rules + HARD_RULES / SOFT_RULES
|  |- bre_engine.py         # Orchestrator: LoanApplication -> DecisionResult
|- tests/
|  |- test_bre_engine.py    # Unit tests for rules, engine, and invariants
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
test_bre_engine.py   -> bre_engine.py, bre_rules.py, loan_application.py
```

Import rule:
- Always import from the project root (`from src.module import ...`).
- Do not use `sys.path.append` (project uses editable install with `pip install -e .`).
