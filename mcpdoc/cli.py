"""Command-line entry point for the MCP config linter and doctor."""

from __future__ import annotations

import argparse
import json
import sys

import colorama
from colorama import Fore, Style

from . import __version__
from .mcp_linter import (
    ConfigParseError,
    MCPConfig,
    check_bad_env_vars,
    check_duplicate_servers,
    check_missing_binaries,
    check_unreachable_endpoints,
    fix_duplicate_servers,
    get_missing_binaries,
    load_config,
)


def _collect_problems(config: MCPConfig) -> tuple[list[str], list[str]]:
    """Return the ``(errors, warnings)`` found in the config."""
    errors = (
        check_duplicate_servers(config)
        + check_missing_binaries(config)
        + check_bad_env_vars(config)
    )
    return errors, check_unreachable_endpoints(config)


def _print_problems(errors: list[str], warnings: list[str]) -> None:
    """Print each problem found in the config: errors in red, warnings in yellow."""
    if not errors and not warnings:
        print("No problems found.")
    for message in errors:
        print(f"{Fore.RED}error: {message}{Style.RESET_ALL}")
    for message in warnings:
        print(f"{Fore.YELLOW}warning: {message}{Style.RESET_ALL}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="mcpdoc",
        description="Lint MCP server configuration files and suggest fixes.",
    )
    parser.add_argument(
        "--config",
        default=".mcp.json",
        help="Path to the MCP config file (default: .mcp.json)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run in check mode (no changes will be made).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite the config to fix what can be fixed safely (duplicate names).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns a process exit code."""
    colorama.just_fix_windows_console()
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse exits on --help; return the exit code instead of raising
        return e.code
    try:
        config = load_config(args.config)
    except (FileNotFoundError, ConfigParseError) as e:
        print(f"{Fore.RED}error: {e}{Style.RESET_ALL}", file=sys.stderr)
        return 2
    missing = get_missing_binaries(config)

    renamed: list[tuple[str, str]] = []
    if args.fix and not args.check:
        # Only rewrite the file in ways that keep it valid JSON. A missing binary
        # cannot be fixed from here, so it is reported instead.
        renamed = fix_duplicate_servers(args.config)

    fix_applied = args.fix and not args.check and bool(renamed)
    if renamed:
        # The file was rewritten, so report problems against what it says now.
        config = load_config(args.config)
    errors, warnings = _collect_problems(config)

    if args.json:
        result = {
            "config_file": args.config,
            "missing_binaries": sorted(missing),
            "errors": errors,
            "warnings": warnings,
            "fix_applied": fix_applied,
            "lint_passed": not errors,
        }
        print(json.dumps(result))
    else:
        print(f"Linting {args.config}")
        _print_problems(errors, warnings)
        for old_name, new_name in renamed:
            print(
                f"{Fore.YELLOW}fixed: renamed duplicate server "
                f"'{old_name}' to '{new_name}'{Style.RESET_ALL}"
            )
        if args.fix and not args.check:
            for binary in sorted(missing):
                print(f"hint: install '{binary}' or point the command at a real path")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
