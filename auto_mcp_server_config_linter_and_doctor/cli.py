"""Command-line entry point for the MCP config linter and doctor."""

from __future__ import annotations

import argparse
import json

from .mcp_linter import add_fix_comments, get_missing_binaries, load_config


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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns a process exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse exits on --help; return the exit code instead of raising
        return e.code
    config = load_config(args.config)
    missing = get_missing_binaries(config)

    if args.fix and not args.check:
        if missing:
            add_fix_comments(args.config, missing)

    fix_applied = args.fix and not args.check and bool(missing)
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
    return 0