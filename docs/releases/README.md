# Releases Documentation Policy

This repository uses a dual-track release documentation model:

- Internal context track (English):
  - Path: `docs/releases/vX.Y.Z/RELEASE_NOTES.md`
  - Purpose: engineering traceability, requirements mapping, technical debt, and session continuity.
- Public publication track (Spanish):
  - Path: `.github/release-notes/es/vX.Y.Z.md`
  - Purpose: GitHub release body for publication.

## Standardization Rules

1. Keep all `docs/context/` and `docs/releases/` internal notes in English.
2. Keep all public release copy in Spanish under `.github/release-notes/es/`.
3. Public release files must follow `.github/release-notes/es/TEMPLATE.md`.
4. For each new release, update both tracks in the same session.
5. Cross-check published GitHub metadata (title, prerelease/release flag, tag, date) before final publication.

## Current Coverage

- Internal English notes:
  - `docs/releases/v0.1.0/RELEASE_NOTES.md`
  - `docs/releases/v0.2.0/RELEASE_NOTES.md`
  - `docs/releases/v0.3.0/RELEASE_NOTES.md`
- Public Spanish notes:
  - `.github/release-notes/es/v0.1.0.md`
  - `.github/release-notes/es/v0.2.0.md`
  - `.github/release-notes/es/v0.3.0.md`
