"""Test that the CLI module can be imported and main runs."""

import json
import sys
from pathlib import Path

from mcpdoc import cli


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
    assert any("mcpdoc" in line for line in out)


def test_cli_json_output_parses(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        json.dumps(
            {
                "servers": {"ok": {"command": "node"}, "missing": {"command": "python"}},
                "binaries": ["node"],
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(["--json", "--config", str(config_file)])

    # A config with at least one error exits 1 so CI fails on it.
    assert exit_code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["missing_binaries"] == ["python"]
    assert result["lint_passed"] is False
    assert result["fix_applied"] is False


def test_cli_colors_problems_with_ansi_codes(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        json.dumps({"servers": {"missing": {"command": "python"}}, "binaries": ["node"]}),
        encoding="utf-8",
    )

    cli.main(["--config", str(config_file)])

    out = capsys.readouterr().out
    assert "\x1b[31m" in out  # red for errors
    assert "error: Server 'missing' specifies binary 'python'" in out


def test_cli_malformed_config_reports_error(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text("{not json", encoding="utf-8")

    exit_code = cli.main(["--config", str(config_file)])

    assert exit_code == 2
    assert "not valid JSON" in capsys.readouterr().err


def test_cli_python_m_help_shows_options() -> None:
    import subprocess

    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "mcpdoc.cli", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--config" in result.stdout
    assert "--check" in result.stdout


def test_cli_fix_flag() -> None:
    # Test that the --fix flag is parsed and sets the attribute
    parser = cli.build_parser()
    args = parser.parse_args(["--fix"])
    assert args.fix is True
    # Test that without --fix, it defaults to False
    args = parser.parse_args([])
    assert args.fix is False


def test_cli_fix_leaves_the_config_valid_json(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        '{"mcpServers": {"fs": {"command": "node"}, "fs": {"command": "not-a-real-xyz"}}}',
        encoding="utf-8",
    )

    exit_code = cli.main(["--fix", "--config", str(config_file)])

    content = config_file.read_text(encoding="utf-8")
    assert "# TODO" not in content
    # The whole point: the file still parses as JSON after --fix.
    fixed = json.loads(content)
    assert list(fixed["mcpServers"]) == ["fs", "fs-2"]
    out = capsys.readouterr().out
    assert "fixed: renamed duplicate server 'fs' to 'fs-2'" in out
    assert "hint: install 'not-a-real-xyz'" in out
    assert exit_code == 1


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

def test_cli_exits_zero_on_clean_config(tmp_path: Path) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        json.dumps({"mcpServers": {"py": {"command": sys.executable}}}), encoding="utf-8"
    )

    assert cli.main(["--config", str(config_file)]) == 0


def test_cli_exits_one_on_real_mcp_servers_config(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".mcp.json"
    config_file.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "a": {"command": "not-a-real-binary-xyz"},
                    "b": {"command": sys.executable, "env": {"TOKEN": ""}},
                }
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(["--config", str(config_file)])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "command 'not-a-real-binary-xyz' was not found on PATH" in out
    assert "environment variable 'TOKEN'" in out
