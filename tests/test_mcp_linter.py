"""Tests for the MCPConfig data model."""

from auto_mcp_server_config_linter_and_doctor.mcp_linter import MCPConfig


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