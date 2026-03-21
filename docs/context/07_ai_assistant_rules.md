# 07. Rules for AI Assistants

Do not change without notice:
- Do not rename existing methods or classes without explicit notice.
- Do not change `APPROVAL_THRESHOLD` without asking first.
- Do not replace `@dataclass` with manual `__init__` unless technically justified.
- Do not use `sys.path.append`.
- Do not modify files under `data/raw/`.

Preferred response format:
- Provide complete, executable code.
- Add explanatory comments only when introducing a new concept.
- Include corresponding unit tests with new code changes.
- Explain the design pattern used and provide a short rationale.

Before refactoring:
- Confirm whether the user wants refactoring or only new functionality.
- If public interfaces change, list impacted files.

Language and style policy:
- Conversation language can remain Spanish for collaboration.
- Variable, function, class, and file names must be in English.
- Commits must be in English using semantic prefixes (`feat:`, `fix:`, `docs:`, `test:`).
- Internal context and AI instruction files must be written in English.
- The root project `README.md` is the only Spanish documentation file by convention.

Target technical level:
- Python basic to intermediate.
- Explain new concepts (OOP, patterns, decorators) when they first appear.
