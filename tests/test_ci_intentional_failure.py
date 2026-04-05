"""Temporary CI gate verification test: intentionally failing."""


def test_ci_intentional_failure() -> None:
    """Fail intentionally to verify PR merge gate behavior."""
    assert False, "Intentional failure to validate CI blocking behavior"
