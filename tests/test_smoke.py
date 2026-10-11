"""Smoke test: package imports cleanly. Replace/extend as modules land."""

import mcpdoc


def test_version_is_set() -> None:
    assert mcpdoc.__version__
