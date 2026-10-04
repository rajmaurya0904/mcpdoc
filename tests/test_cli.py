"""Test that the CLI module can be imported and main runs."""

import sys

from auto_mcp_server_config_linter_and_doctor import cli


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


def test_cli_fix_flag() -> None:
    # Test that the --fix flag is parsed and sets the attribute
    parser = cli.build_parser()
    args = parser.parse_args(["--fix"])
    assert args.fix is True
    # Test that without --fix, it defaults to False
    args = parser.parse_args([])
    assert args.fix is False