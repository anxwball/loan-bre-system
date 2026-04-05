# 13. Branch Protection Policy

Scope:
- This policy applies to `main` as the protected canonical branch.
- Goal: prevent unreviewed changes and guarantee auditable merge gates.

Mandatory controls for `main`:
1. Pull request is required for all merges and branch updates.
2. At least 1 approval is required before merge.
3. Direct push to `main` is blocked.
4. Force push is blocked.
5. Bypass is disabled for all actors, including admins (default mode).
6. All review conversations must be resolved before merge.
7. Branch must be up to date before merge (strict required checks policy).

Official required checks (effective from 2026-04-05):
1. `ci-pytest`
2. `ci-static-validation`
3. `SonarCloud Code Analysis`

Reference CI workflow:
- `.github/workflows/main-guard-ci.yml`

Verification protocol (real evidence):
1. Confirm active ruleset and protection state with GitHub API (`gh api`).
2. Attempt a direct push to `main` from a non-main branch ref and confirm rejection.
3. Confirm pull request cannot be merged without at least one approval.
4. Confirm pull request cannot be merged with unresolved conversations.
5. Confirm outdated branch is blocked until synchronization and required checks pass.

Exit criteria:
1. No actor can push directly to `main`.
2. Every merge to `main` requires PR flow and human review.
3. Protection rule is active on GitHub and validated through a real push-rejection test.

Operational note:
- Emergency changes must use PR flow; temporary bypass enablement is out of policy and requires an explicit incident decision logged in `docs/context/DECISIONS.md`.

Recommended quality gate exit policy for new code:
1. Zero blocker issues.
2. Zero critical issues.
3. No degradation in maintainability rating.
4. No degradation in security rating.
5. New-code quality gate target: 100% pass (all gate conditions satisfied).
6. Pull request decoration must remain enabled so Sonar results are visible in PR checks and summaries.
