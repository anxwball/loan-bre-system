**# 11. Loan Approval Criteria — Deterministic Domain Definition**

> Issue #1: Define formal `loan_status` without proxy dependency.
> This document is the single source of truth for BRE rule design (Issue #2).

---

**## 1. Design Decision: Why No Proxy**

The original dataset contains `loan_status` as a historical human label — it reflects past approval decisions that may encode bias, incomplete information, or inconsistent criteria. Using it as ground truth would make the BRE a classifier that mimics history, not a rules engine that applies explicit credit logic.

**The BRE defines its own `approved` or `denied` outcome** based solely on domain variables available at application time. `loan_status` is retained only in `loan_labels.csv` for post-hoc benchmarking: how often does the BRE agree with historical decisions, and where does it diverge?

---

**## 2. Variables Used — Identified and Justified**

**### 2.1 Hard Rule Variables** *(deterministic blockers)*

| Variable | Type | Justification |
|---|---|---|
| `credit_history` | int (0/1) | Industry-standard binary signal. A score of 0 indicates prior default or no credit record — both are disqualifying in standard credit risk frameworks (Basel II/III). Non-negotiable gate. |
| `total_income` | float (derived) | Absolute income floor. No loan is viable if the applicant has no demonstrated repayment capacity regardless of loan size. |
| `monthly_payment_ratio` | float (computed in rule) | `(loan_amount / loan_amount_term) / total_income`. Measures whether monthly installment is payable. Industry threshold: < 0.40. |

> ⚠️ **Note on `loan_to_income_ratio`:** Computes `loan_amount / total_income` — mixes units (loan in thousands, income monthly). Unsuitable as deterministic gate. Used as soft rule leverage signal only.

**### 2.2 Soft Rule Variables** *(scored risk modifiers)*

| Variable | Justification |
|---|---|
| `self_employed` | Income volatility. Not disqualifying alone but increases risk score. |
| `dependents` | Higher count increases financial burden. Modulates repayment capacity indirectly. |
| `education` | Graduate status as income stability proxy. Weak signal — marginal tiebreaker only. |
| `property_area` | Urban/Semiurban correlates with higher collateral value vs Rural. |
| `married` | Dual-income households reduce risk. Positive signal when `coapplicant_income > 0`. |
| `loan_amount_term` | Shorter terms increase monthly burden. Signal for `monthly_payment_ratio` sensitivity. |
| `loan_to_income_ratio` | 3–6 = moderate leverage; > 6 = high leverage even if monthly payment passes. |

**### 2.3 Variables Excluded from BRE Logic**

| Variable | Reason |
|---|---|
| `gender` | Ethically excluded. Not a valid credit risk variable under fair lending standards. |
| `loan_id` | Identifier only. No domain semantics. |

---

**## 3. Formal Approval Criteria**

**### 3.1 Hard Rules — Any single failure = DENIED**

    HARD-01: credit_history == 0
             → DENY. Prior default or no credit record.

    HARD-02: total_income <= 0
             → DENY. No repayment capacity. (Also enforced as domain invariant.)

    HARD-03: monthly_payment_ratio > 0.40
             where monthly_payment_ratio = (loan_amount / loan_amount_term) / total_income
             → DENY. Monthly installment exceeds 40% of total income.

> **Why 40%?** The 28/36 rule (US) and similar frameworks cap total debt service at 36–43% of gross income. 40% is a conservative industry midpoint.

**### 3.2 Soft Rules — Scored (0–100)**

Each rule contributes a delta to a base score of 0.

    SOFT-01: loan_to_income_ratio > 6.0          → +20 risk  (high leverage)
    SOFT-02: loan_to_income_ratio > 3.0          → +10 risk  (moderate leverage)
    SOFT-03: self_employed == "Yes"              → +15 risk  (income volatility)
    SOFT-04: dependents == "3+"                  → +10 risk  (high financial burden)
    SOFT-05: dependents == "2"                   → +5  risk  (moderate burden)
    SOFT-06: property_area == "Rural"            → +10 risk  (lower collateral value)
    SOFT-07: property_area == "Semiurban"        → +5  risk  (moderate collateral)
    SOFT-08: married == "Yes" and
             coapplicant_income > 0              → -10 risk  (dual income stability)

> Score: 0–30 = APPROVE | 31–50 = APPROVE flagged | 51+ = DENY

---

**## 4. Decision Flow**

    LoanApplication
          │
          ▼
    [HARD-01] credit_history == 0? ──YES──→ DENIED (hard block)
          │ NO
          ▼
    [HARD-02] total_income <= 0? ────YES──→ DENIED (hard block)
          │ NO
          ▼
    [HARD-03] monthly_payment_ratio > 0.40? ─YES─→ DENIED (hard block)
          │ NO
          ▼
    [SOFT RULES] → accumulate risk score
          │
          ▼
    score ≤ 30  → APPROVED
    score 31–50 → APPROVED (flagged — review recommended)
    score ≥ 51  → DENIED (risk threshold exceeded)

---

**## 5. Edge Cases and Domain Invariants**

| Case | Behavior | Justification |
|---|---|---|
| `applicant_income = 0`, `coapplicant_income > 0` | Valid — passes HARD-02 | Co-applicant income is a legitimate repayment source |
| `coapplicant_income = 0`, `married = "Yes"` | SOFT-08 does NOT apply | Benefit only when co-applicant actually contributes |
| `loan_amount_term <= 0` | Blocked by domain invariant | Prevents division by zero in HARD-03 |
| `loan_amount = 0` | Blocked by domain invariant | Semantically invalid — zero loan has no purpose |
| `credit_history = 1` + all soft rules maxed (score = 75) | DENIED on soft rules | Extreme leverage overrides clean credit history |
| `self_employed = "Yes"` + `married = "Yes"` + `coapplicant_income > 0` | +15 - 10 = +5 net | Dual income partially compensates volatility |
| `dependents = "3+"` + `property_area = "Rural"` + `loan_to_income > 6` | Score = 40 → APPROVE flagged | High-risk but not disqualifying |

---

**## 6. Missing Invariants Identified — Resolved**

Both gaps identified during criteria design have been corrected in `src/loan_application.py`:

    if self.loan_amount == 0:
        raise ValueError("Loan amount must be greater than zero.")
    if self.loan_amount_term <= 0:
        raise ValueError("Loan term must be a positive number of months.")
