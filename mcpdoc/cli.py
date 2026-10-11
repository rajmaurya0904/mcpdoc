"""Command-line entry point for the MCP config linter and doctor."""

from __future__ import annotations

import argparse
import json

import colorama
from colorama import Fore, Style

from . import __version__
from .mcp_linter import (
    MCPConfig,
    add_fix_comments,
    check_bad_env_vars,
    check_duplicate_servers,
    check_missing_binaries,
    check_unreachable_endpoints,
    fix_duplicate_servers,
    get_missing_binaries,
    load_config,
)


def _print_problems(config: MCPConfig) -> None:
    """Print each problem found in the config: errors in red, warnings in yellow."""
    errors = (
        check_duplicate_servers(config)
        + check_missing_binaries(config)
        + check_bad_env_vars(config)
    )
    warnings = check_unreachable_endpoints(config)
    if not errors and not warnings:
        print("No problems found.")
    for message in errors:
        print(f"{Fore.RED}error: {message}{Style.RESET_ALL}")
    for message in warnings:
        print(f"{Fore.YELLOW}warning: {message}{Style.RESET_ALL}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="mcp-linter",
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
        help="Attempt to automatically fix detected problems.",
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
    config = load_config(args.config)
    missing = get_missing_binaries(config)

    renamed: list[tuple[str, str]] = []
    if args.fix and not args.check:
        renamed = fix_duplicate_servers(args.config)
        if missing:
            add_fix_comments(args.config, missing)

    fix_applied = args.fix and not args.check and bool(missing or renamed)
    lint_passed = not missing

    if args.json:
        result = {
            "config_file": args.config,
            "missing_binaries": sorted(list(missing)),
            "fix_applied": fix_applied,
            "lint_passed": lint_passed,
        }
        print(json.dumps(result))
    else:
        print(f"Linting {args.config}")
        _print_problems(config)
        for old, new in renamed:
            print(
                f"{Fore.YELLOW}fixed: renamed duplicate server "
                f"'{old}' to '{new}'{Style.RESET_ALL}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
