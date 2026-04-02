# Release v0.2.0

## Executive Summary

Version `v0.2.0` marks the transition from a Phase-1 EDA baseline to a BRE-first project direction, with modular project context, governed label artifacts, and a refactored data pipeline aligned to downstream rule-engine development.

## Release Boundary

- Previous release: `v0.1.0` (`d4693e6`)
- Release baseline branch: `main`
- Release target commit on `main`: `d09ecbe`
- Included scope: bootstrap completion for Issue #1 and documentation realignment for Issue #2 kickoff

## GitHub Published Metadata (Verified)

- Release title on GitHub: `Baseline de datos y arquitectura para el BRE`
- Release type: `Pre-release`
- Tag and commit: `v0.2.0` -> `d09ecbe`
- Compare links shown on GitHub:
  - Since release to main: `v0.2.0...main`
  - Full release delta: `v0.1.0...v0.2.0`
- Assets: `0` custom uploaded assets (`2` auto-generated source archives: zip/tar)

## Requirement-to-Delivery Trace

- Issue #1 (bootstrap data and invariant groundwork)
  - Delivered through canonical schema normalization, label split governance, and feature/label separation in the processing flow.
- BRE-first project direction
  - Delivered through repository-wide documentation updates that repositioned EDA as support and BRE as the implementation priority.
- Long-lived context governance
  - Delivered through modular context files, assistant adapters, and explicit documentation policy.

## Changelog Entry (Detailed)

### Added

- Modular context system under `docs/context/` with architecture, glossary, status, and session history modules.
- Assistant adapters under `docs/context/agents/` (`chatgpt.md`, `claude.md`, `copilot.md`) to standardize context loading behavior.
- Context gateway file `CLAUDE.md` linking canonical context modules and operational conventions.
- Governed label outputs:
  - `data/processed/loan_labels.csv`
  - `data/labels/loan_labels_latest.csv`
  - versioned label snapshots under `data/labels/versions/`

### Changed

- `src/data_loader.py` refactored to pipeline-oriented processing with explicit schema normalization and label split stages.
- `notebooks/eda_analysis.py` aligned with new data flow and project scope decisions.
- `README.md` rewritten and synchronized with BRE-first bootstrap scope.
- `.gitignore` updated to reflect dataset and artifact tracking policy.
- Legacy raw dataset path (`data/raw/loans_data.csv`) replaced by normalized workflow inputs.

### Quality and Validation

- Documentation policy formalized in `docs/context/06_code_conventions.md` for executive module docstrings, technical docstrings, and sparse critical comments.
- Session continuity protocol established in `docs/context/10_session_history.md` as a mandatory update log.

## Technical Debt

| Item | Priority | Resolution Phase |
|---|---|---|
| Implement first traceable BRE rules and decision engine | High | Phase 2 / Issue #2 |
| Expand automated test suite from baseline to full domain coverage | High | Phase 2 / Issue #3 |
| Finalize SQL persistence strategy for audit records | Medium | Phase 4b |

## Lessons Learned

### What Worked (3)

1. Splitting context into modular files improved maintainability and onboarding speed.
2. Separating labels from processed features reduced ambiguity for downstream modeling and BRE logic.
3. Formalizing documentation style early reduced drift across rapidly changing modules.

### What to Improve (3)

1. Introduce stricter release templates earlier to reduce end-cycle reconstruction effort.
2. Add targeted tests in parallel with pipeline refactors to reduce verification lag.
3. Keep commit granularity narrower when combining data, docs, and architecture changes.

## Proposed Scope for v0.3.0

1. Implement first traceable BRE rules and decision orchestration.
2. Add modular test coverage for domain invariants and decision paths.
3. Introduce batch comparison and audit logging baseline.
4. Prepare SQL persistence foundations toward Phase 4b.