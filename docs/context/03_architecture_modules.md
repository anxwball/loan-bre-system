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
|  |  |- schema.py          # SQLAlchemy Core schema for Phase 3 (implemented)
|  |  |- database.py        # Engine and connection factory (implemented)
|  |  |- repositories/      # Persistence repositories (implemented)
|  |- api/                  # Branch-scoped Phase 4 FastAPI layer (active feature work)
|  |  |- __init__.py
|  |  |- main.py            # FastAPI app factory and router wiring
|  |  |- dependencies.py    # DB/session dependencies and JWT role guards
|  |  |- routers/           # auth, evaluate, audit, analyst endpoints
|  |  |- schemas/           # request/response contracts for API layer
|- tests/
|  |- conftest.py           # Shared fixtures for LoanApplication and RuleEngine
|  |- test_rule_engine_decisions.py
|  |- test_bre_rules.py
|  |- test_loan_application.py
|  |- test_integral_dataset_flow.py
|  |- test_batch_evaluator.py
|  |- test_audit_logger.py
|  |- test_data_loader.py
|  |- test_api_auth.py      # Branch-scoped auth endpoint validation
|  |- test_api_evaluate.py  # Branch-scoped single/batch endpoint validation
|  |- test_api_audit.py     # Branch-scoped audit and analyst queue validation
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
src/db/repositories/loan_repo.py  -> src/db/schema.py, src/loan_application.py
src/db/repositories/audit_repo.py -> src/db/schema.py, src/bre_engine.py, src/bre_rules.py
src/api/main.py               -> src/api/routers/*.py, src/db/database.py
src/api/routers/evaluate.py   -> src/loan_application.py, src/bre_engine.py, src/audit_logger.py
src/api/routers/audit.py      -> src/db/schema.py
tests/test_api_*.py           -> src/api/main.py, src/api/routers/*.py
```

Import rule:
- Always import from the project root (`from src.module import ...`).
- Runtime code must not use `sys.path` mutation.
- Test bootstrapping may use `tests/conftest.py` path injection when editable install is not guaranteed in local CI/dev shells.

Phase 3 status:
- `src/db/schema.py` is implemented.
- `src/db/database.py` is implemented.
- `src/db/repositories/` is implemented.

Phase 4 branch snapshot (feature-scoped):
- `src/api/main.py`, `src/api/dependencies.py`, `src/api/routers/`, and `src/api/schemas/` are implemented on the active feature branch.
- `tests/test_api_auth.py`, `tests/test_api_evaluate.py`, and `tests/test_api_audit.py` validate the current API scope.
- Validation snapshot (2026-04-04): `pytest tests/test_api_auth.py tests/test_api_evaluate.py tests/test_api_audit.py -q` -> 7 passed.
