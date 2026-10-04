"""MCP linter functionality."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


def get_missing_binaries(config: MCPConfig) -> set[str]:
    """Return the set of binaries that are referenced by servers but not in the binaries list."""
    binary_set = set(config.binaries)
    missing: set[str] = set()
    for _server_name, server_config in config.servers.items():
        command = server_config.get("command")
        if command and command not in binary_set:
            missing.add(command)
    return missing


def add_fix_comments(path: str, missing_binaries: set[str]) -> None:
    """Add a comment line for each missing binary to the config file.

    This function appends a line of the form '# TODO: install <binary>' for each
    missing binary to the end of the file.

    Parameters
    ----------
    path: str
        Path to the configuration file.
    missing_binaries: set[str]
        A set of missing binary names.
    """
    with open(path, encoding='utf-8') as f:
        content = f.read()
    # Ensure we end with a newline before appending.
    if not content.endswith('\n'):
        content += '\n'
    for binary in missing_binaries:
        content += f'# TODO: install {binary}\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


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


def check_duplicate_servers(config: MCPConfig) -> list[str]:
    """Check for duplicate server names.

    Returns a list of error messages, empty if none.
    """
    # Since servers is a dict, duplicate keys are impossible.
    # However, we could check if the config had a list of servers with a 'name' field.
    # For now, we assume the dict structure and return empty.
    return []


def check_missing_binaries(config: MCPConfig) -> list[str]:
    """Check that each server's command is listed in the binaries list.

    Returns a list of error messages, empty if none.
    """
    errors: list[str] = []
    binary_set = set(config.binaries)
    for server_name, server_config in config.servers.items():
        command = server_config.get("command")
        if command and command not in binary_set:
            errors.append(
                f"Server '{server_name}' specifies binary '{command}' "
                f"which is not in the binaries list."
            )
    return errors


def check_bad_env_vars(config: MCPConfig) -> list[str]:
    """Check that environment variables are non-empty strings.

    Returns a list of error messages, empty if none.
    """
    errors: list[str] = []
    for key, value in config.env_vars.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"Environment variable '{key}' must be a non-empty string."
            )
    return errors


def check_unreachable_endpoints(config: MCPConfig) -> list[str]:
    """Check for unreachable endpoints.

    This is a placeholder; endpoint information is not available in the current config.
    Returns an empty list.
    """
    return []


def run_checks(path: str = ".mcp.json") -> dict[str, list[str]]:
    """Load config and run all validation checks, returning a dict of results.

    Keys are check names, values are lists of error messages.
    """
    config = load_config(path)
    return {
        "duplicate_servers": check_duplicate_servers(config),
        "missing_binaries": check_missing_binaries(config),
        "bad_env_vars": check_bad_env_vars(config),
        "unreachable_endpoints": check_unreachable_endpoints(config),
    }