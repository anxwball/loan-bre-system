# Prompt Templates — System Lifecycle
> v1.1.0 | Cycle: Requirements → Architecture → Implementation → Security → Deploy → Review

---

## Usage

- Each prompt consumes the previous output as `[INPUT]`.
- Replace `< >` values before running.
- Adjust the **Context** field to calibrate formality and depth.
- Save outputs to: `docs/<phase>/<project>-v<X.Y>.md`

**Context:** `personal` → prioritize speed and clarity. `work` → prioritize traceability and formal documentation.

---

## Context Update Protocol

Include this block at the start of any prompt session where the system context may need updating.

```
CONTEXT UPDATE PROTOCOL (run before any phase prompt):

1. Identify the active phase and project from the current session.
2. Review the existing context (CLAUDE.md, prior phase outputs, open issues).
3. Detect if any of the following have changed since the last session:
   - Project scope or requirements
   - Architectural decisions
   - Stack or dependencies
   - Active phase or next steps
4. If changes are detected:
   - Propose a minimal context diff (only what changed, not a full rewrite).
   - Label each change as: UPDATE | ADD | REMOVE
   - Do NOT apply any change until explicitly confirmed.
5. If no changes are detected: proceed directly to the requested phase prompt.
6. After confirmation, apply only the approved changes and continue.

RULE: Never refactor the full context to fit a new state.
      Patch forward; preserve what is still valid.
```

---

## PHASE 0 — Requirements

```
ROLE: Systems analyst. Adjust rigor to the indicated context.

TASK: Extract functional and non-functional requirements from the stated problem.

INPUT:
- Context: <personal | work>
- Problem: <brief description>
- Users: <who uses the system>
- Constraints: <time, technology, budget>

ANALYSIS & CONSTRAINTS:
- Separate FR (what it does) from NFR (how it behaves).
- Identify happy path + at least 2 critical edge cases.
- Flag external dependencies.
- If context=personal: skip formal numbering; use a simple list.

OUTPUT:
- Listed requirements (FR-### / NFR-### if work, plain list if personal).
- Use cases in structured text or Mermaid.
- Identified risks.

SYNTHESIS: 3 lines — what we're building, for whom, and what makes it complex.

NEXT STEPS: Pass to PHASE 1 with this document as input.
```

---

## PHASE 1 — Architecture (HLD)

```
ROLE: Solutions architect. Scale formality to context.

TASK: Design the high-level architecture based on the received requirements.

INPUT:
- Context: <personal | work>
- Requirements: <PHASE 0 output>
- Stack: <available or preferred technologies>
- Infra: <local, cloud, hybrid>

ANALYSIS & CONSTRAINTS:
- Justify every decision with explicit trade-offs.
- Apply: separation of concerns, low coupling.
- Name the patterns used and why (Gateway, Strategy, Pipeline, etc.).
- Identify SPOFs and how they are mitigated.
- If context=personal: one simple diagram is enough; skip the decision table.

OUTPUT:
- HLD diagram in Mermaid.
- Decision table (work) or key decisions list (personal).
- Component contracts (interfaces, not code).
- Architectural risks.

SYNTHESIS: 4 lines explaining the architecture as if for a portfolio.

NEXT STEPS: Pass to PHASE 2 with HLD + contracts.
```

---

## PHASE 2 — Technical Design (LLD)

```
ROLE: Senior backend engineer. Adjust detail to context and indicated module.

TASK: Translate the HLD into a technical design for module <name>.

INPUT:
- Context: <personal | work>
- Approved HLD: <PHASE 1 output>
- Module: <name and responsibility>
- Technical constraints: <framework, ORM, language version>

ANALYSIS & CONSTRAINTS:
- Define data model with types and relations before implementing.
- Specify class/function interfaces (Design by Contract).
- Apply SOLID where natural — justify each principle used.
- Define error handling per layer.
- Include API versioning (v1/, v2/) if there are external endpoints.
- If context=personal: informal diagram + pseudocode is enough.

OUTPUT:
- Class diagram or module schema.
- DB schema with types and constraints.
- API contract: method, route, body, response, errors.
- Validation checklist per endpoint.

SYNTHESIS: What pattern dominates this module and why was it the best choice?

NEXT STEPS: Pass to PHASE 3 with the complete LLD.
```

---

## PHASE 3 — Implementation

```
ROLE: Senior developer in <language>. Prioritize clean, testable code.

TASK: Implement module <name> following the received LLD.

INPUT:
- Context: <personal | work>
- LLD: <PHASE 2 output>
- Conventions: <naming, folder structure, code style>
- Existing codebase: <paste relevant snippets>

ANALYSIS & CONSTRAINTS:
- Respect LLD contracts — do not improvise interfaces.
- Every public function: docstring with purpose, parameters, return, and exceptions.
- No external dependencies not approved in the HLD.
- Use early return to reduce nesting.
- If context=personal: docstrings optional; prioritize readability over formality.

OUTPUT:
- Complete, functional module code.
- Inline comments on non-obvious decisions.
- List of accepted technical TODOs with justification.

SYNTHESIS: What technical debt was consciously accepted and why?

NEXT STEPS: Pass to PHASE 4 with the implemented module.
```

---

## PHASE 4 — Testing & Validation

```
ROLE: QA engineer / SDET. Scale coverage to context risk.

TASK: Design and implement the test suite for module <name>.

INPUT:
- Context: <personal | work>
- Implemented code: <PHASE 3 output>
- Edge cases: <PHASE 0 output>
- Module contract: <PHASE 2 output>

ANALYSIS & CONSTRAINTS:
- Cover: happy path, PHASE 0 edge cases, explicit error cases.
- Unit tests: no real I/O, mock external dependencies.
- Integration tests: validate contracts between modules.
- Naming: test_<module>_<scenario>_<expected_result>.
- If context=personal: basic unit tests + one integration test per critical flow.

OUTPUT:
- Organized suite (unit/, integration/).
- Coverage report with justified gaps.
- Uncovered cases with explicit reason.

SYNTHESIS: What confidence level does this suite provide and where are the blind spots?

NEXT STEPS: Pass to PHASE 5 with the coverage report.
```

---

## PHASE 5 — Security Review

```
ROLE: Security engineer. Calibrate depth to context and attack surface.

TASK: Review the security of the system implemented up to this point.

INPUT:
- Context: <personal | work>
- HLD: <PHASE 1 output>
- Code and contracts: <PHASE 2 and PHASE 3 outputs>
- Attack surface: <exposed endpoints, sensitive data handled>

ANALYSIS & CONSTRAINTS:
- Review against OWASP API Top 10 minimum: Broken Object Auth, Broken Auth,
  Excessive Data Exposure, Injection.
- Check secrets: in .env? hardcoded?
- Review authentication and authorization per endpoint.
- If context=personal: focus on exposed secrets + unvalidated inputs.

OUTPUT:
- Table: Finding | Severity | Risk | Remediation.
- Security checklist: Pass / Fail / N/A.
- Accepted risks documented with justification.

SYNTHESIS: Is this ready to be exposed to a real environment?

NEXT STEPS: Pass to PHASE 6 with findings resolved or documented.
```

---

## PHASE 6 — Deploy & Operations

```
ROLE: DevSecOps engineer. Adapt pipeline complexity to context.

TASK: Design the deployment pipeline and operational strategy for the system.

INPUT:
- Context: <personal | work>
- Architecture: <PHASE 1 output>
- Resolved security: <PHASE 5 output>
- Available infra: <Railway, VPS, Docker, K8s, etc.>

ANALYSIS & CONSTRAINTS:
- Define branching strategy with justification (GitFlow vs trunk-based).
- Specify environment variables per environment — never real values.
- Define rollback policy on failure.
- Include structured logging (JSON) with levels: DEBUG / INFO / WARNING / ERROR.
- If context=personal: docker-compose + manual deploy script is enough.

OUTPUT:
- Commented Dockerfile or docker-compose.
- CI/CD pipeline in pseudocode or YAML skeleton.
- Minimal runbook: start, monitor, rollback.
- Documented environment variables (names and description, no values).

SYNTHESIS: How reproducible and observable is this system in production?

NEXT STEPS: Pass to PHASE 7 with the full stack documented.
```

---

## PHASE 7 — Retrospective & Version Close

```
ROLE: Tech lead or project author. Facilitate the close of the current version.

TASK: Produce the version close document <vX.Y.Z> for project <name>.

INPUT:
- Context: <personal | work>
- Outputs from phases 0–6.
- Deviations or incidents that occurred.
- Received feedback (if applicable).

ANALYSIS & CONSTRAINTS:
- Follow Semantic Versioning: MAJOR.MINOR.PATCH with explicit criteria.
- Document technical debt with issue/ticket reference.
- Trace original requirements → delivered features.
- If context=personal: informal README notes are enough; skip formal CHANGELOG.

OUTPUT:
- CHANGELOG.md entry.
- Technical debt table: item | priority | resolution phase.
- Lessons learned: 3 that worked / 3 to improve.
- Proposed scope for next version.

SYNTHESIS: What version did we deliver, what did we commit to, what comes next?

NEXT STEPS: Archive in docs/releases/v<X.Y.Z>/ and open next iteration planning.
```

---

## Prompt Versioning

| Change | Version |
|---|---|
| Typo or clarity fix | PATCH (1.x.x) |
| New field or added section | MINOR (x.1.x) |
| Phase restructure or cycle change | MAJOR (1.0.x) |

> Path: `docs/prompts/v<X.Y.Z>/<phase>-prompt.md`