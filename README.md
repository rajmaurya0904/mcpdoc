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

TODO: fill in as the build loop lands the core feature.

## Example

TODO.

## FAQ

TODO.

## License

MIT -- see [LICENSE](LICENSE).