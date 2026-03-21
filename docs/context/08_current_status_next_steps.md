# 08. Current Status and Next Steps

Working:
- Complete project structure with professional packaging.
- EDA pipeline: loading, cleaning, feature engineering, and visualizations.
- First commit and LinkedIn post published (Phase 1).

Designed but not implemented (Phase 2):
- `LoanApplication` with domain invariants in `__post_init__`.
- BRE with 3 hard rules and 8 soft rules.
- `RuleEngine` with full flow and traceable `DecisionResult`.
- Unit test suite with fixtures (`pytest tests/ -v`).

Pending (prioritized):
1. Batch evaluation on the cleaned dataset and comparison against real `loan_status`.
2. Audit module with persistence in `.jsonl` or SQLite.
3. Phase 3 complementary ML with `scikit-learn`.
4. Phase 4 REST API with FastAPI.
5. Docker packaging for final README delivery.

Open decisions:
- Decide whether batch runner belongs in `notebooks/` or `src/batch_evaluator.py`.
- Decide the audit log destination.
- Decide whether ML replaces soft rules or is added as a new scored rule.
