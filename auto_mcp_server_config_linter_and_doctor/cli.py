"""Command-line entry point for the MCP config linter and doctor."""

from __future__ import annotations

import argparse


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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns a process exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse exits on --help; return the exit code instead of raising
        return e.code
    print(f"Linting {args.config}")
    return 0