"""Tests for the JSON config loader."""

import json
import pathlib

import pytest

from mcpdoc.mcp_linter import ConfigParseError, MCPConfig, load_config


def test_load_config_returns_correct_data(tmp_path: pathlib.Path) -> None:
    config_data = {
        "servers": {
            "my-server": {"command": "node", "args": ["server.js"]},
            "other-server": {"command": "python", "args": ["-m", "mcp_server"]},
        },
        "env_vars": {"API_KEY": "secret", "LOG_LEVEL": "debug"},
        "binaries": ["node", "python"],
    }
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    config = load_config(str(config_file))

    assert isinstance(config, MCPConfig)
    assert config.servers == config_data["servers"]
    assert config.env_vars == config_data["env_vars"]
    assert config.binaries == config_data["binaries"]


def test_load_config_missing_file_raises(tmp_path: pathlib.Path) -> None:
    missing = tmp_path / ".mcp.json"
    with pytest.raises(FileNotFoundError):
        load_config(str(missing))


def test_load_config_malformed_json_raises_config_parse_error(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text('{"servers": {"a": {"command": "node"}', encoding="utf-8")

    with pytest.raises(ConfigParseError, match="not valid JSON"):
        load_config(str(config_file))


def test_load_config_empty_file(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text("{}", encoding="utf-8")

    config = load_config(str(config_file))

    assert config.servers == {}
    assert config.env_vars == {}
    assert config.binaries == []


REALISTIC_MCP_JSON = """{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/raj/projects"]
    },
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_example"}
    },
    "sentry": {
      "url": "https://mcp.sentry.dev/mcp"
    }
  }
}
"""


def test_load_config_reads_mcp_servers_key(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(REALISTIC_MCP_JSON, encoding="utf-8")

    config = load_config(str(config_file))

    assert list(config.servers) == ["filesystem", "github", "sentry"]
    assert config.servers["filesystem"]["command"] == "npx"
    assert config.servers["sentry"]["url"] == "https://mcp.sentry.dev/mcp"


def test_load_config_still_accepts_servers_key(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        json.dumps({"servers": {"legacy": {"command": "node"}}}), encoding="utf-8"
    )

    assert list(load_config(str(config_file)).servers) == ["legacy"]


def test_load_config_prefers_mcp_servers_over_servers(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        json.dumps(
            {
                "mcpServers": {"real": {"command": "node"}},
                "servers": {"legacy": {"command": "node"}},
            }
        ),
        encoding="utf-8",
    )

    assert list(load_config(str(config_file)).servers) == ["real"]
