# 04. BRE Module (Business Rules Engine)

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
   - Hard rules first. If one fails, immediate rejection with `score=0`.
   - Soft rules next. They accumulate positive or negative points.
   - Final approval if `score >= APPROVAL_THRESHOLD (40)`.

Implemented rules:

| ID  | Name | Type | Purpose |
|-----|--------|------|-----------|
| R01 | CreditHistoryRequired | Hard | Reject if `credit_history == 0` |
| R02 | MinimumIncome | Hard | Reject if `total_income < 2500` |
| R03 | LoanAmountSanity | Hard | Reject if `loan_amount <= 0` |
| R04 | LowDebtRatio | Soft | +30 pts if `loan_to_income_ratio <= 0.35` |
| R05 | ModerateDebtRatio | Soft | +10 pts if ratio is between `0.35` and `0.50` |
| R06 | HighDebtRatio | Soft | -20 pts if ratio `> 0.50` |
| R07 | IsMarried | Soft | +15 pts if `married == "Yes"` |
| R08 | IsGraduate | Soft | +10 pts if `education == "Graduate"` |
| R09 | IsNotSelfEmployed | Soft | +10 pts if `self_employed == "No"` |
| R10 | HasNoDependents | Soft | +10 pts if `dependents == "0"` |
| R11 | LongLoanTerm | Soft | +5 pts if `loan_amount_term >= 360` |

Approval threshold:
- `APPROVAL_THRESHOLD = 40` defined in `bre_engine.py`.
