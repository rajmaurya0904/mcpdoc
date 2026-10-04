"""Smoke test: package imports cleanly. Replace/extend as modules land."""

import auto_mcp_server_config_linter_and_doctor


def test_version_is_set() -> None:
    assert auto_mcp_server_config_linter_and_doctor.__version__
