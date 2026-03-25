# 04. BRE Module (Business Rules Engine)

Scope note:
- Formal deterministic approval criteria are defined in `docs/context/11_approval_criteria.md`.
- This module page summarizes the implementation contract for Issue #2.

Design pattern:
- Simplified Strategy Pattern.
- Each rule is a pure function that receives `LoanApplication` and returns `RuleResult`.
- `RuleEngine` orchestrates rules without knowing internal rule logic (Open/Closed Principle).

Rule template:

```python
def rule_name(app: LoanApplication) -> RuleResult:
    passed = <boolean_condition>
    return RuleResult(
        rule_id="R##",
        name="NameInPascalCase",
        passed=passed,
        points=<int>,
        reason="Human-readable explanation"
    )
```

Execution flow:
1. Add function to `HARD_RULES` or `SOFT_RULES` in `bre_rules.py`.
2. `RuleEngine.evaluate(app)` runs:
    - Hard rules first. If one fails, immediate rejection.
    - Soft rules next. They accumulate risk points.
    - Final decision by risk bands: 0-30 approve, 31-50 approve flagged, 51+ deny.

Implemented rule set (aligned with `11_approval_criteria.md`):

| ID  | Name | Type | Purpose |
|-----|--------|------|-----------|
| R01 | CreditHistoryRequired | Hard | Reject if `credit_history == 0` |
| R02 | PositiveTotalIncome | Hard | Reject if `total_income <= 0` |
| R03 | MonthlyPaymentCapacity | Hard | Reject if `(loan_amount / loan_amount_term) / total_income > 0.40` |
| R04 | HighLeverage | Soft | +20 risk if `loan_to_income_ratio > 6.0` |
| R05 | ModerateLeverage | Soft | +10 risk if `loan_to_income_ratio > 3.0` |
| R06 | SelfEmployedRisk | Soft | +15 risk if `self_employed == "Yes"` |
| R07 | HighDependentsBurden | Soft | +10 risk if `dependents == "3+"` |
| R08 | ModerateDependentsBurden | Soft | +5 risk if `dependents == "2"` |
| R09 | RuralAreaRisk | Soft | +10 risk if `property_area == "Rural"` |
| R10 | SemiurbanAreaRisk | Soft | +5 risk if `property_area == "Semiurban"` |
| R11 | DualIncomeStability | Soft | -10 risk if `married == "Yes"` and `coapplicant_income > 0` |

Decision policy:
- Hard fail -> denied immediately.
- Soft score 0-30 -> approved.
- Soft score 31-50 -> approved with manual-review flag.
- Soft score 51+ -> denied.
