"""Tests for the MCPConfig data model and validation functions."""

import json

from auto_mcp_server_config_linter_and_doctor.mcp_linter import (
    MCPConfig,
    check_bad_env_vars,
    check_duplicate_servers,
    check_missing_binaries,
    check_unreachable_endpoints,
    run_checks,
)


def test_mcp_config_defaults() -> None:
    config = MCPConfig()
    assert config.servers == {}
    assert config.env_vars == {}
    assert config.binaries == []


def test_mcp_config_fields() -> None:
    config = MCPConfig(
        servers={"my-server": {"command": "node", "args": ["server.js"]}},
        env_vars={"API_KEY": "secret"},
        binaries=["node"],
    )
    assert config.servers == {"my-server": {"command": "node", "args": ["server.js"]}}
    assert config.env_vars == {"API_KEY": "secret"}
    assert config.binaries == ["node"]


def test_mcp_config_repr_shows_all_fields() -> None:
    config = MCPConfig(
        servers={"my-server": {"command": "node"}},
        env_vars={"API_KEY": "secret"},
        binaries=["node"],
    )
    r = repr(config)
    assert "servers" in r
    assert "env_vars" in r
    assert "binaries" in r
    assert "my-server" in r
    assert "API_KEY" in r
    assert "node" in r


def test_check_duplicate_servers_always_empty() -> None:
    # Since servers is a dict, duplicate keys are impossible.
    config = MCPConfig(servers={"a": {}, "b": {}})
    assert check_duplicate_servers(config) == []


def test_check_missing_binaries() -> None:
    config = MCPConfig(
        servers={
            "ok": {"command": "node"},
            "missing": {"command": "python"},
        },
        binaries=["node"],
    )
    errors = check_missing_binaries(config)
    assert len(errors) == 1
    assert "Server 'missing' specifies binary 'python'" in errors[0]


def test_check_missing_binaries_clean() -> None:
    config = MCPConfig(
        servers={
            "ok": {"command": "node"},
            "also_ok": {"command": "python"},
        },
        binaries=["node", "python"],
    )
    assert check_missing_binaries(config) == []


def test_check_bad_env_vars() -> None:
    config = MCPConfig(
        env_vars={
            "GOOD": "value",
            "BAD": "",
            "WHITESPACE": "   ",
            "NOT_STRING": 123,
        }
    )
    errors = check_bad_env_vars(config)
    # We expect errors for BAD, WHITESPACE, and NOT_STRING
    assert len(errors) == 3
    error_messages = " ".join(errors)
    assert "Environment variable 'BAD'" in error_messages
    assert "Environment variable 'WHITESPACE'" in error_messages
    assert "Environment variable 'NOT_STRING'" in error_messages


def test_check_bad_env_vars_clean() -> None:
    config = MCPConfig(env_vars={"KEY1": "val1", "KEY2": "val2"})
    assert check_bad_env_vars(config) == []


def test_check_unreachable_endpoints_always_empty() -> None:
    config = MCPConfig()
    assert check_unreachable_endpoints(config) == []


def test_run_checks_with_clean_config(tmp_path) -> None:
    config_data = {
        "servers": {"server1": {"command": "node"}},
        "binaries": ["node"],
        "env_vars": {"KEY": "value"},
    }
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    result = run_checks(str(config_file))
    assert result == {
        "duplicate_servers": [],
        "missing_binaries": [],
        "bad_env_vars": [],
        "unreachable_endpoints": [],
    }


def test_run_checks_with_errors(tmp_path) -> None:
    config_data = {
        "servers": {
            "ok": {"command": "node"},
            "missing": {"command": "python"},
        },
        "binaries": ["node"],
        "env_vars": {"BAD": ""},
    }
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    result = run_checks(str(config_file))
    assert result["duplicate_servers"] == []
    assert len(result["missing_binaries"]) == 1
    assert "Server 'missing' specifies binary 'python'" in result["missing_binaries"][0]
    assert len(result["bad_env_vars"]) == 1
    assert "Environment variable 'BAD'" in result["bad_env_vars"][0]
    assert result["unreachable_endpoints"] == []


def test_run_checks_with_multiple_issues(tmp_path) -> None:
    """End-to-end test: config with multiple issues across all check categories."""
    config_data = {
        "servers": {
            "ok": {"command": "node"},
            "missing_bin": {"command": "python"},
            "also_missing": {"command": "ruby"},
        },
        "binaries": ["node"],
        "env_vars": {
            "GOOD": "value",
            "EMPTY": "",
            "WHITESPACE": "   \t\n",
            "NOT_STRING": 42,
        },
    }
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    result = run_checks(str(config_file))

    # duplicate_servers: always empty with current dict-based servers
    assert result["duplicate_servers"] == []

    # missing_binaries: two errors
    missing = result["missing_binaries"]
    assert len(missing) == 2
    assert any("Server 'missing_bin' specifies binary 'python'" in m for m in missing)
    assert any("Server 'also_missing' specifies binary 'ruby'" in m for m in missing)

    # bad_env_vars: three errors (EMPTY, WHITESPACE, NOT_STRING)
    bad = result["bad_env_vars"]
    assert len(bad) == 3
    bad_messages = " ".join(bad)
    assert "Environment variable 'EMPTY'" in bad_messages
    assert "Environment variable 'WHITESPACE'" in bad_messages
    assert "Environment variable 'NOT_STRING'" in bad_messages

    # unreachable_endpoints: always empty
    assert result["unreachable_endpoints"] == []


def test_add_fix_comments_adds_placeholder_lines(tmp_path) -> None:
    """Test that add_fix_comments adds the expected placeholder comments."""
    from auto_mcp_server_config_linter_and_doctor.mcp_linter import add_fix_comments

    # Create a config file with some initial content
    config_file = tmp_path / ".mcp.json"
    initial_content = '{"servers": {"test": {"command": "python"}}}'
    config_file.write_text(initial_content, encoding="utf-8")

    missing_binaries = {"python", "ruby"}
    add_fix_comments(str(config_file), missing_binaries)

    # Read the file and check for the expected lines
    content = config_file.read_text(encoding="utf-8")
    # Ensure original content is preserved
    assert initial_content in content
    # Check that the placeholder lines are present (order may vary)
    assert '# TODO: install python' in content
    assert '# TODO: install ruby' in content
    # Ensure we didn't add extra blank lines incorrectly
    # The function ensures a newline before appending, so we expect each comment on its own line.
    # We can also check that the file ends with a newline (since each comment adds one).
    assert content.endswith('\n')