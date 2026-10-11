"""Tests for the MCPConfig data model and validation functions."""

import json
import os
import shutil
import sys

import requests

from mcpdoc.mcp_linter import (
    MCPConfig,
    check_bad_env_vars,
    check_duplicate_servers,
    check_missing_binaries,
    check_unreachable_endpoints,
    find_invalid_env_vars,
    find_missing_binary_paths,
    find_unreachable_endpoints,
    fix_duplicate_servers,
    get_missing_binaries,
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


def test_check_duplicate_servers_clean_config() -> None:
    config = MCPConfig(servers={"a": {}, "b": {}})
    assert check_duplicate_servers(config) == []


def test_check_duplicate_servers_reports_repeated_names(tmp_path) -> None:
    # JSON objects cannot hold two equal keys, so the duplicate is written
    # as a repeated key in the raw file, which json would otherwise drop.
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        '{"servers": {"fs": {"command": "node"}, "fs": {"command": "python"}},'
        ' "binaries": ["node", "python"]}',
        encoding="utf-8",
    )

    result = run_checks(str(config_file))

    assert len(result["duplicate_servers"]) == 1
    assert "Server 'fs' is defined more than once." in result["duplicate_servers"][0]


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


def test_find_missing_binary_paths_reports_missing(monkeypatch) -> None:
    present = {"/usr/bin/node"}
    monkeypatch.setattr(os.path, "isfile", lambda p: p in present)
    config = MCPConfig(binaries=["/usr/bin/node", "/opt/missing/python"])
    assert find_missing_binary_paths(config) == ["/opt/missing/python"]


def test_fix_duplicate_servers_renames_repeated_names(tmp_path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        '{"servers": {"fs": {"command": "node"}, "fs": {"command": "python"}},'
        ' "binaries": ["node", "python"]}',
        encoding="utf-8",
    )

    renamed = fix_duplicate_servers(str(config_file))

    assert renamed == [("fs", "fs-2")]
    fixed = json.loads(config_file.read_text(encoding="utf-8"))
    assert list(fixed["servers"]) == ["fs", "fs-2"]
    assert fixed["servers"]["fs-2"] == {"command": "python"}
    assert run_checks(str(config_file))["duplicate_servers"] == []


def test_fix_duplicate_servers_keeps_valid_json_structure(tmp_path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        '{"servers": {"fs": {"command": "node"}, "fs": {"command": "python"}},'
        ' "binaries": ["node", "python"], "env_vars": {"KEY": "value"}}',
        encoding="utf-8",
    )

    fix_duplicate_servers(str(config_file))

    fixed = json.loads(config_file.read_text(encoding="utf-8"))
    assert fixed == {
        "servers": {"fs": {"command": "node"}, "fs-2": {"command": "python"}},
        "binaries": ["node", "python"],
        "env_vars": {"KEY": "value"},
    }


def test_find_unreachable_endpoints_reports_only_failures(requests_mock) -> None:
    requests_mock.head("https://ok.example/mcp", status_code=200)
    # An error status still means the server answered, so it is reachable.
    requests_mock.head("https://method.example/mcp", status_code=405)
    requests_mock.head(
        "https://bad.example/mcp", exc=requests.exceptions.ConnectTimeout
    )
    config = MCPConfig(
        servers={
            "ok": {"url": "https://ok.example/mcp"},
            "method": {"url": "https://method.example/mcp"},
            "bad": {"url": "https://bad.example/mcp"},
            "local": {"command": "node"},
        }
    )
    assert find_unreachable_endpoints(config) == ["https://bad.example/mcp"]


def test_find_missing_binary_paths_all_present(monkeypatch) -> None:
    monkeypatch.setattr(os.path, "isfile", lambda p: True)
    config = MCPConfig(binaries=["/usr/bin/node", "/usr/bin/python"])
    assert find_missing_binary_paths(config) == []


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


def test_find_invalid_env_vars_returns_bad_keys() -> None:
    config = MCPConfig(
        env_vars={
            "GOOD": "value",
            "EMPTY": "",
            "BAD-NAME": "value",
            "NUL_BYTE": "abc\x00def",
            "NOT_STRING": 7,
        }
    )
    assert find_invalid_env_vars(config) == ["EMPTY", "BAD-NAME", "NUL_BYTE", "NOT_STRING"]


def test_find_invalid_env_vars_clean() -> None:
    config = MCPConfig(env_vars={"KEY_1": "val1", "_PRIVATE": "val2"})
    assert find_invalid_env_vars(config) == []


def test_check_bad_env_vars_clean() -> None:
    config = MCPConfig(env_vars={"KEY1": "val1", "KEY2": "val2"})
    assert check_bad_env_vars(config) == []


def test_check_unreachable_endpoints_empty_config() -> None:
    config = MCPConfig()
    assert check_unreachable_endpoints(config) == []


def test_check_unreachable_endpoints_reports_message(requests_mock) -> None:
    requests_mock.head("https://bad.example/mcp", exc=requests.exceptions.ConnectTimeout)
    config = MCPConfig(servers={"bad": {"url": "https://bad.example/mcp"}})
    errors = check_unreachable_endpoints(config)
    assert len(errors) == 1
    assert "https://bad.example/mcp" in errors[0]


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
    from mcpdoc.mcp_linter import add_fix_comments

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

def test_check_missing_binaries_resolves_bare_command_on_path(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/npx" if cmd == "npx" else None)
    config = MCPConfig(servers={"filesystem": {"command": "npx"}})

    assert check_missing_binaries(config) == []


def test_check_missing_binaries_reports_command_not_on_path(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    config = MCPConfig(servers={"git": {"command": "git-mcp"}})

    errors = check_missing_binaries(config)

    assert errors == ["Server 'git' command 'git-mcp' was not found on PATH."]


def test_check_missing_binaries_accepts_existing_absolute_path() -> None:
    config = MCPConfig(servers={"py": {"command": sys.executable}})

    assert check_missing_binaries(config) == []


def test_check_missing_binaries_reports_absent_absolute_path(tmp_path) -> None:
    absent = str(tmp_path / "bin" / "node")
    config = MCPConfig(servers={"node": {"command": absent}})

    errors = check_missing_binaries(config)

    assert errors == [f"Server 'node' command '{absent}' does not exist."]


def test_get_missing_binaries_resolves_commands(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/node" if cmd == "node" else None)
    config = MCPConfig(
        servers={"ok": {"command": "node"}, "bad": {"command": "nope-mcp"}},
    )

    assert get_missing_binaries(config) == {"nope-mcp"}


def test_binaries_allowlist_still_wins_when_present(monkeypatch) -> None:
    """A config that declares a binaries list keeps the old allowlist behaviour."""
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/" + cmd)
    config = MCPConfig(servers={"ok": {"command": "node"}}, binaries=["python"])

    errors = check_missing_binaries(config)

    assert len(errors) == 1
    assert "not in the binaries list" in errors[0]
    assert get_missing_binaries(config) == {"node"}
