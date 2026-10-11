# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Fixed
- Read servers from the `mcpServers` key that real MCP configs use (`servers` is
  still accepted), so the linter no longer passes every file silently.
- Check that a server's command actually resolves with `shutil.which()` or
  `os.path.isfile()` instead of looking it up in an invented `binaries` list.
- Report empty values inside each server's own `env` block.
- Exit with code 1 when any error is found, so CI can fail on it.
- `--fix` no longer appends `# TODO` lines that made the config invalid JSON; it
  renames duplicate server names and rewrites valid JSON.

### Changed
- Distribution and console script renamed to `mcpdoc`, matching the package.

### Removed
- The `lint_config()` stub, which always returned no problems.

## [0.1.0] - 2024-06-15
### Added
- Lint MCP server configuration files (.mcp.json and claude_desktop_config) for:
  - Missing binaries
  - Bad environment variables
  - Duplicate server names
  - Unreachable endpoints
- Command-line interface with:
  - `--config` to specify the config file (default: .mcp.json)
  - `--check` to run in check mode (no changes)
  - `--fix` to attempt automatic fixes