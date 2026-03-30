"""Orchestrate loan decisioning with traceable hard and soft BRE rules.

This module runs hard rules first and soft rules second, then maps the resulting
risk score to business decision bands. Output includes decision, reasons, and
rule trace for auditability.
"""

from dataclasses import dataclass

from src.bre_rules import HARD_RULES, SOFT_RULES, RuleResult
from src.loan_application import LoanApplication


@dataclass(frozen=True)
class DecisionResult:
    """Represent the final BRE decision plus traceability artifacts.

    Args:
        approved: Final approval decision.
        score: Aggregate risk score from soft rules.
        reasons: Ordered human-readable reasons supporting the decision.
        hard_rejection: Whether a hard rule caused immediate denial.
        flagged_for_review: Whether manual review is recommended.
        rules_triggered: Rule results that impacted the outcome.

    Returns:
        Immutable decision object ready for logging or API output.
    """

    approved: bool
    score: int
    reasons: list[str]
    hard_rejection: bool
    flagged_for_review: bool
    rules_triggered: list[RuleResult]

    def summary(self) -> str:
        """Build a compact human-readable summary.

        Returns:
            One-line summary with decision and risk score.
        """

        decision_label = "APPROVED" if self.approved else "DENIED"
        review_tag = " [REVIEW]" if self.flagged_for_review else ""
        return f"{decision_label}{review_tag} | score={self.score}"


class RuleEngine:
    """Evaluate loan applications against deterministic BRE rule sets.

    Public behavior follows the domain criteria contract:
    1) Hard-rule failure causes immediate denial.
    2) Soft rules accumulate risk score.
    3) Risk bands decide final outcome.
    """

    def evaluate(self, app: LoanApplication) -> DecisionResult:
        """Run full BRE evaluation for one loan application.

        Args:
            app: Valid domain application object.

        Returns:
            DecisionResult with decision and traceability details.
        """

        evaluated_rules: list[RuleResult] = []

        for hard_rule in HARD_RULES:
            hard_result = hard_rule(app)
            evaluated_rules.append(hard_result)

            if not hard_result.passed:
                return DecisionResult(
                    approved=False,
                    score=0,
                    reasons=[hard_result.reason],
                    hard_rejection=True,
                    flagged_for_review=False,
                    rules_triggered=evaluated_rules,
                )

        score = 0
        reason_details: list[str] = []

        for soft_rule in SOFT_RULES:
            soft_result = soft_rule(app)
            evaluated_rules.append(soft_result)

            if soft_result.points != 0:
                score += soft_result.points
                reason_details.append(soft_result.reason)

        if score < 0:
            score = 0

        if score <= 30:
            approved = True
            flagged_for_review = False
            decision_reason = "Final decision: score is within automatic approval band (0-30)."
        elif score <= 50:
            approved = True
            flagged_for_review = True
            decision_reason = "Final decision: score is in review band (31-50), manual review recommended."
        else:
            approved = False
            flagged_for_review = False
            decision_reason = "Final decision: score is in denial band (51+)."

        reasons = [decision_reason]
        reasons.extend(reason_details)

        return DecisionResult(
            approved=approved,
            score=score,
            reasons=reasons,
            hard_rejection=False,
            flagged_for_review=flagged_for_review,
            rules_triggered=evaluated_rules,
        )
