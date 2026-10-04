"""MCP linter functionality."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MCPConfig:
    """Represents an MCP configuration."""

    servers: dict[str, dict[str, object]] = field(default_factory=dict)
    env_vars: dict[str, str] = field(default_factory=dict)
    binaries: list[str] = field(default_factory=list)


def load_config(path: str = ".mcp.json") -> MCPConfig:
    """Load an MCP configuration from a JSON file.

    Parameters
    ----------
    path: str
        Path to the JSON configuration file. Defaults to ``.mcp.json``.

    Returns
    -------
    MCPConfig
        A populated configuration dataclass.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Extract known keys, defaulting to empty structures if missing.
    servers = data.get("servers", {})
    env_vars = data.get("env_vars", {})
    binaries = data.get("binaries", [])
    return MCPConfig(servers=servers, env_vars=env_vars, binaries=binaries)


def lint_config(path: str = ".mcp.json") -> list[str]:
    """Pretend to lint a config file and return a list of messages.

    This is a stub implementation that always returns an empty list, indicating
    no issues were found.
    """
    # In a real implementation, this would parse the file and return warnings.
    return []
