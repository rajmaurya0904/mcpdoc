"""Tests for the JSON config loader."""

import json
import pathlib

import pytest

from auto_mcp_server_config_linter_and_doctor.mcp_linter import MCPConfig, load_config


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


def test_load_config_empty_file(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text("{}", encoding="utf-8")

    config = load_config(str(config_file))

    assert config.servers == {}
    assert config.env_vars == {}
    assert config.binaries == []
