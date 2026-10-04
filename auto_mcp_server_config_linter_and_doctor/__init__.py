"""MCP server config linter and doctor

Checks .mcp.json and claude_desktop_config files for missing binaries, bad env vars,
duplicate server names and unreachable endpoints, then shows how to fix each one. For
anyone whose MCP servers silently fail to load.
"""

__version__ = "0.1.0"
