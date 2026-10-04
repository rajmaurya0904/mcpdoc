"""Test that the CLI module can be imported and main runs."""

import sys

from src import cli


def test_cli_import() -> None:
    assert hasattr(cli, "main")


def test_cli_main_runs(monkeypatch) -> None:
    # Capture stdout
    out: list[str] = []

    class Dummy:
        def write(self, s: str) -> None:
            out.append(s)

    monkeypatch.setattr(sys, "stdout", Dummy())
    exit_code = cli.main(["--help"])
    assert exit_code == 0
    # The help text should contain the program name
    assert any("mcp-linter" in line for line in out)