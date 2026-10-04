"""Test that the CLI module can be imported and main runs."""

import json
import sys
from pathlib import Path

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


def test_cli_fix_adds_todo_comments(tmp_path: Path) -> None:
    # Create a temporary config file with a missing binary
    config = {
        "servers": {
            "test_server": {
                "command": "missing_binary"
            }
        },
        "binaries": ["existing_binary"]
    }
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")

    # Run the CLI with --fix on the temporary config
    # We need to change the current working directory to tmp_path for relative path to work
    # Alternatively, we can pass the absolute path via --config
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = cli.main(["--fix", "--config", str(config_file)])
        assert exit_code == 0
    finally:
        os.chdir(old_cwd)

    # Check that the file now contains the TODO comment
    content = config_file.read_text(encoding="utf-8")
    assert "# TODO: install missing_binary" in content


def test_cli_version_output_matches_pyproject() -> None:
    # Read the version from pyproject.toml
    PROJECT_ROOT = Path(__file__).parent.parent
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    version = None
    for line in content.splitlines():
        if line.strip().startswith("version ="):
            version = line.split("=")[1].strip().strip('"')
            break
    assert version is not None, "Could not find version in pyproject.toml"

    # Run the CLI with --version and capture output
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        cli.main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    finally:
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
    # The output should be exactly: f"mcp-linter {version}\n"
    expected = f"mcp-linter {version}\n"
    assert output == expected