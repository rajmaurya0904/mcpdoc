# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2024-06-15
### Added
- Lint MCP server configuration files (.mcp.json and claude_desktop_config) for:
  - Missing binaries
  - Bad environment variables
  - Duplicate server names
  - Unreachable endpoints
- Automatic fix for missing binaries by adding fix comments
- Command-line interface with:
  - `--config` to specify the config file (default: .mcp.json)
  - `--check` to run in check mode (no changes)
  - `--fix` to attempt automatic fixes