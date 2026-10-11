"""MCP linter functionality."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import requests

_ENV_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Real MCP config files (.mcp.json, claude_desktop_config.json, ~/.claude.json) all use
# "mcpServers". "servers" is accepted as a fallback for hand-written configs.
SERVER_KEYS = ("mcpServers", "servers")


def _server_key(data: dict) -> str:
    """Return the key holding the server table in ``data``, preferring ``mcpServers``."""
    for key in SERVER_KEYS:
        if key in data:
            return key
    return SERVER_KEYS[0]


def get_missing_binaries(config: MCPConfig) -> set[str]:
    """Return the set of binaries that are referenced by servers but not in the binaries list."""
    binary_set = set(config.binaries)
    missing: set[str] = set()
    for _server_name, server_config in config.servers.items():
        command = server_config.get("command")
        if command and command not in binary_set:
            missing.add(command)
    return missing


def fix_duplicate_servers(path: str) -> list[tuple[str, str]]:
    """Rename repeated server names in the config file so every name is unique.

    The second and later occurrences of a name get an incrementing suffix, such as
    ``fs-2``, and the file is rewritten as JSON. Returns the ``(old, new)`` name pairs
    that were changed, empty when the file had no duplicates.
    """
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text, object_pairs_hook=_object_hook)
    servers_key = _server_key(data)
    servers = data.get(servers_key)
    if not isinstance(servers, _JSONObject) or not servers.duplicate_keys:
        return []

    used = {key for key, _value in servers.pairs}
    seen: set[str] = set()
    renamed: list[tuple[str, str]] = []
    new_pairs: list[tuple[str, object]] = []
    for key, value in servers.pairs:
        if key not in seen:
            seen.add(key)
            new_pairs.append((key, value))
            continue
        suffix = 2
        while f"{key}-{suffix}" in used:
            suffix += 1
        new_key = f"{key}-{suffix}"
        used.add(new_key)
        renamed.append((key, new_key))
        new_pairs.append((new_key, value))

    data[servers_key] = dict(new_pairs)
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return renamed


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


class ConfigParseError(Exception):
    """Raised when a configuration file exists but is not valid JSON."""


class _JSONObject(dict):
    """A dict parsed from a JSON object that remembers which keys were repeated."""

    pairs: tuple[tuple[str, object], ...] = ()
    duplicate_keys: tuple[str, ...] = ()


def _object_hook(pairs: list[tuple[str, object]]) -> _JSONObject:
    """Build a dict from JSON pairs, recording keys that appear more than once.

    ``json`` silently keeps the last value for a repeated key, so without this
    hook a duplicated server name would vanish without a trace.
    """
    obj = _JSONObject(pairs)
    seen: set[str] = set()
    duplicates: list[str] = []
    for key, _value in pairs:
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    obj.pairs = tuple(pairs)
    obj.duplicate_keys = tuple(duplicates)
    return obj


@dataclass
class MCPConfig:
    """Represents an MCP configuration."""

    servers: dict[str, dict[str, object]] = field(default_factory=dict)
    env_vars: dict[str, str] = field(default_factory=dict)
    binaries: list[str] = field(default_factory=list)
    duplicate_servers: list[str] = field(default_factory=list)


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
    ConfigParseError
        If the configuration file is not valid JSON.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f, object_pairs_hook=_object_hook)
        except json.JSONDecodeError as e:
            raise ConfigParseError(
                f"{path} is not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})."
            ) from e
    # Extract known keys, defaulting to empty structures if missing.
    servers = data.get(_server_key(data), {})
    env_vars = data.get("env_vars", {})
    binaries = data.get("binaries", [])
    duplicate_servers = list(getattr(servers, "duplicate_keys", ()))
    return MCPConfig(
        servers=servers,
        env_vars=env_vars,
        binaries=binaries,
        duplicate_servers=duplicate_servers,
    )


def lint_config(path: str = ".mcp.json") -> list[str]:
    """Pretend to lint a config file and return a list of messages.

    This is a stub implementation that always returns an empty list, indicating
    no issues were found.
    """
    # In a real implementation, this would parse the file and return warnings.
    return []


def check_duplicate_servers(config: MCPConfig) -> list[str]:
    """Check for server names that are defined more than once in the config.

    Returns a list of error messages, empty if none.
    """
    return [
        f"Server '{name}' is defined more than once."
        for name in config.duplicate_servers
    ]


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


def find_missing_binary_paths(config: MCPConfig) -> list[str]:
    """Return the binary paths listed in the config that do not exist as files.

    An empty list means every listed binary was found on the filesystem.
    """
    return [path for path in config.binaries if not os.path.isfile(path)]


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


def find_invalid_env_vars(config: MCPConfig) -> list[str]:
    """Return the keys of env vars that are malformed.

    A key is returned when its name is not a valid environment variable name, or
    its value is not a string, is empty or whitespace, or contains a NUL character.
    """
    invalid: list[str] = []
    for key, value in config.env_vars.items():
        if (
            not _ENV_NAME_PATTERN.fullmatch(key)
            or not isinstance(value, str)
            or not value.strip()
            or "\x00" in value
        ):
            invalid.append(key)
    return invalid


def find_unreachable_endpoints(config: MCPConfig, timeout: float = 3.0) -> list[str]:
    """Return the server URLs that do not answer a HEAD request within ``timeout``.

    Any HTTP response counts as reachable, even an error status. Servers without a
    ``url`` entry are skipped.
    """
    unreachable: list[str] = []
    for server_config in config.servers.values():
        if not isinstance(server_config, dict):
            continue
        url = server_config.get("url")
        if not isinstance(url, str) or not url:
            continue
        try:
            requests.head(url, timeout=timeout, allow_redirects=True)
        except requests.RequestException:
            unreachable.append(url)
    return unreachable


def check_unreachable_endpoints(config: MCPConfig) -> list[str]:
    """Check that each server endpoint answers a HEAD request.

    Returns a list of warning messages, empty if none.
    """
    return [
        f"Endpoint '{url}' did not respond in time."
        for url in find_unreachable_endpoints(config)
    ]


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