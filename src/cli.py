"""Command-line entry point for the MCP config linter and doctor."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="mcp-linter",
        description="Lint MCP server configuration files and suggest fixes.",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=".mcp.json",
        help="Path to the MCP config file (default: .mcp.json)",
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
    print(f"Linting {args.config}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())