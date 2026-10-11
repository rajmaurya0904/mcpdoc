# mcpdoc

**Lints MCP server config files (`.mcp.json`, `claude_desktop_config.json`) and tells you exactly why a server will not start.**

When an MCP server fails to load, the client usually says nothing useful: the tools
are just absent. The real cause is almost always boring -- the command is not on
your PATH, a token was left as `""`, the same server name appears twice so one
entry silently wins, or an HTTP endpoint is dead. `mcpdoc` reads the config the
same way the client does and names the broken line.

## Real terminal output

```text
$ mcpdoc --config .mcp.json
Linting .mcp.json
error: Server 'filesystem' is defined more than once.
error: Server 'github' command 'github-mcp-server' was not found on PATH.
error: Server 'github' environment variable 'GITHUB_PERSONAL_ACCESS_TOKEN' must be a non-empty string.
warning: Endpoint 'http://127.0.0.1:9/mcp' did not respond in time.

$ echo $?
1
```

Errors print in red, warnings in yellow. Any error means exit code 1, so it drops
straight into CI.

## Install

Not on PyPI. Clone it and install from the checkout:

```bash
pip install -e .
```

Needs Python 3.11 or newer.

## Usage

```bash
mcpdoc                                  # lint ./.mcp.json
mcpdoc --config ~/.claude.json          # lint a config somewhere else
mcpdoc --config .mcp.json --json        # one JSON object, for scripts
mcpdoc --config .mcp.json --fix         # rename duplicate server names in place
```

`--fix` rewrites the file as valid JSON and only changes what it can change
safely, which today means de-duplicating server names. Everything else is
reported, not guessed at:

```text
$ mcpdoc --config .mcp.json --fix
Linting .mcp.json
error: Server 'github' command 'github-mcp-server' was not found on PATH.
error: Server 'github' environment variable 'GITHUB_PERSONAL_ACCESS_TOKEN' must be a non-empty string.
warning: Endpoint 'http://127.0.0.1:9/mcp' did not respond in time.
fixed: renamed duplicate server 'filesystem' to 'filesystem-2'
hint: install 'github-mcp-server' or point the command at a real path
```

`--check` reports without touching the file, and `--version` prints the version.

## How it works

The config is parsed with a JSON hook that keeps repeated keys, so a duplicated
server name cannot vanish on the way in. Servers are read from `mcpServers`,
falling back to `servers` for hand-written files.

| Check | What it does | Severity |
| --- | --- | --- |
| Duplicate servers | Server names that appear more than once in the raw JSON | error |
| Missing binaries | `shutil.which()` for a bare command, `os.path.isfile()` for a path | error |
| Bad env vars | Non-string, empty or whitespace values in `env_vars` and in each server's `env` | error |
| Unreachable endpoints | One HEAD request per `url`, 3s timeout; any HTTP status counts as alive | warning |

If a config declares its own `binaries` allowlist, commands are checked against
that list instead of against the real system.

## Limitations

- It never starts a server, so a command that exists but crashes on launch looks fine.
- It does not validate `args`, transport fields, or anything MCP-protocol specific.
- Env values are only checked for being non-empty strings; a wrong token passes.
- `--fix` only de-duplicates names. Missing binaries and bad env values are yours to fix.
- The endpoint check is a single HEAD request, so a slow server on a bad network can be reported as unreachable.

## Development

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

MIT -- see [LICENSE](LICENSE).
