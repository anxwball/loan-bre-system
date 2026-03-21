# 09. Domain Glossary

| Term | Definition |
|------|------------|
| BRE (Business Rules Engine) | Engine that evaluates explicit business rules to make an automated decision |
| Hard Rule | Automatic and irreversible rejection rule; if it fails, no further rules are evaluated |
| Soft Rule | Rule that adds or subtracts points from score; aggregate score determines final decision |
| APPROVAL_THRESHOLD | Minimum score (40 pts) required for approval after passing hard rules |
| DecisionResult | BRE output object containing decision, score, reason, and triggered rules |
| LoanApplication | BRE input object with applicant data validated by invariants |
| loan_to_income_ratio | Loan amount divided by total household income |
| total_income | Sum of `applicantincome` + `coapplicantincome` |
| credit_history | Binary field: 1 positive history, 0 negative history |
| Auditability | Ability to reconstruct exactly why a decision was made |
| Editable install | `pip install -e .` installs package linked to source for development |
| Domain invariant | Condition that must always hold for object validity |
