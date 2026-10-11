# MCP server config linter and doctor

Checks .mcp.json and claude_desktop_config files for missing binaries, bad env vars, duplicate server names and unreachable endpoints, then shows how to fix each one. For anyone whose MCP servers silently fail to load.

## Validation Rules

This tool performs four validation checks on your MCP server configuration:

1. **Duplicate server detection**: Ensures that each server has a unique name in the configuration.
2. **Binary existence**: Checks that the binary specified for each server exists in the system PATH or is an absolute path.
3. **Env var validation**: Validates that environment variables are defined and have appropriate values (if required).
4. **Endpoint reachability**: For servers that specify an endpoint (e.g., HTTP), checks that the endpoint is reachable.

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python >=3.11

## Usage

Lint a config file (defaults to `.mcp.json` in the current directory):

```bash
mcpdoc --config .mcp.json
```

Options:

- `--config PATH`: the config file to check (default `.mcp.json`).
- `--check`: report only, do not change the file.
- `--fix`: rename duplicate server names (`filesystem` becomes `filesystem-2`) and rewrite the file. If binaries are missing, it also appends `# TODO: install <binary>` lines, which makes the file invalid JSON.
- `--json`: print one JSON object instead of text.
- `--version`: print the version and exit.

Text output prints errors in red and warnings in yellow. For a config with a duplicate server, a missing binary and an empty env var:

```text
Linting .mcp.json
error: Server 'filesystem' is defined more than once.
error: Server 'git' specifies binary 'git-mcp' which is not in the binaries list.
error: Environment variable 'API_KEY' must be a non-empty string.
```

Fix only the duplicate server names:

```bash
mcpdoc --config .mcp.json --fix
```

```text
fixed: renamed duplicate server 'filesystem' to 'filesystem-2'
```

Machine-readable output for scripts:

```bash
mcpdoc --config .mcp.json --json
```

```json
{"config_file": ".mcp.json", "missing_binaries": ["git-mcp"], "fix_applied": false, "lint_passed": false}
```

A missing or malformed config file is reported on stderr with exit code 2.

## Example

TODO.

## FAQ

**What if a binary is optional?**
If a binary is optional, you can mark it as such in the configuration by setting `"optional": true` for that server. The linter will skip the binary existence check for optional servers.

**How to ignore a server?**
To ignore a server during validation, add `"ignore": true` to the server's configuration. The linter will skip all checks for that server.

## License

MIT -- see [LICENSE](LICENSE).