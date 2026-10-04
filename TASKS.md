# Tasks

## 1. Initialize project structure (simple)

Create src directory with __init__.py, add a basic CLI entry point file (cli.py) and a placeholder linter module (mcp_linter.py).

**Acceptance:** Directory structure exists with the three files and they import without errors.

## 2. Add basic CLI argument parsing (simple)

Implement argparse in cli.py to accept a '--config' option defaulting to '.mcp.json' and a '--check' flag.

**Acceptance:** Running `python -m src.cli --help` displays the two options and exits with code 0.

## 3. Create data model for MCP config (simple)

Define a dataclass in mcp_linter.py representing the MCP configuration with fields for servers, env_vars, and binaries.

**Acceptance:** Importing the dataclass works and its __repr__ shows all fields.

## 4. Implement JSON config loader (simple)

Add a function to read the JSON file specified by '--config' and populate the dataclass, handling file-not-found with a clear exception.

**Acceptance:** Calling the loader with a valid test JSON returns a populated dataclass; missing file raises FileNotFoundError.

## 5. Write test for JSON config loader (simple)

Create a pytest file that supplies a temporary .mcp.json and asserts the loader returns correct data.

**Acceptance:** Running `pytest -q` passes the new test.

## 6. Detect duplicate server names (simple)

Add a validation function that scans the servers list for duplicate 'name' entries and returns a list of duplicates.

**Acceptance:** Function returns non‑empty list when duplicates are present and empty list otherwise.

## 7. Write test for duplicate server detection (simple)

Add a pytest case with a config containing duplicate server names and assert the validator reports them.

**Acceptance:** Test passes confirming duplicate detection works.

## 8. Validate required binaries existence (simple)

Implement a check that verifies each binary path listed in the config exists on the filesystem, returning missing paths.

**Acceptance:** Function returns missing binary paths when they do not exist and empty list when all are present.

## 9. Test binary existence validation (simple)

Create a test that mocks os.path.isfile to simulate missing binaries and asserts the validator reports them.

**Acceptance:** Test passes with mocked missing binaries.

## 10. Validate environment variable values (simple)

Add a function that checks env var entries for empty strings or invalid characters and returns problematic keys.

**Acceptance:** Function returns a list of invalid env var keys for a given bad config.

## 11. Test environment variable validation (simple)

Write a pytest case with malformed env var entries and verify the validator returns the correct keys.

**Acceptance:** Test passes confirming detection of bad env vars.

## 12. Check endpoint reachability (complex)

Implement a network check that attempts a HEAD request to each server endpoint with a short timeout and records unreachable URLs.

**Acceptance:** Function returns a list of URLs that did not respond within the timeout.

## 13. Test endpoint reachability with mocking (complex)

Use requests-mock to simulate reachable and unreachable endpoints and assert the validator reports only the unreachable ones.

**Acceptance:** Test passes with mocked HTTP responses.

## 14. Integrate all validators into a single run function (simple)

Create a `run_checks` function that loads config, runs duplicate, binary, env var, and endpoint checks, and aggregates results.

**Acceptance:** Calling `run_checks` returns a dict with keys for each check and empty lists when config is clean.

## 15. Write end‑to‑end test for run_checks (simple)

Provide a full config file with known issues and assert `run_checks` returns the expected problem lists.

**Acceptance:** E2E test passes confirming aggregation works.

## 16. Add '--fix' flag to CLI (simple)

Extend argparse to include a '--fix' option that, when present, attempts automatic remediation of detected problems.

**Acceptance:** Running `python -m src.cli --fix` parses without error and sets a flag in the namespace.

## 17. Implement automatic fixing of duplicate server names (complex)

When '--fix' is used, rename duplicate servers by appending an incrementing suffix and write back the updated config.

**Acceptance:** After running with '--fix', the config file contains unique server names.

## 18. Test automatic fixing of duplicate names (complex)

Create a test that runs the fix function on a config with duplicates and asserts the file is rewritten with unique names.

**Acceptance:** Test passes confirming duplicate names are resolved.

## 19. Implement automatic fixing of missing binaries (simple)

When '--fix' is used, prompt (or log) suggestions for installing missing binaries; for now, just add a placeholder comment in the config.

**Acceptance:** Running fix adds a '# TODO: install <binary>' comment line for each missing binary.

## 20. Test fixing of missing binaries placeholder (simple)

Verify that after invoking the fix routine, the config file contains the expected placeholder comments.

**Acceptance:** Test confirms placeholder lines are present.

## 21. Add colored output for CLI results (simple)

Integrate the 'colorama' library to print warnings in yellow and errors in red.

**Acceptance:** Running the CLI with problems displays colored text (verify via presence of ANSI codes).

## 22. Write test for colored output detection (simple)

Capture CLI stdout and assert that ANSI color codes appear when problems are reported.

**Acceptance:** Test passes confirming color codes are emitted.

## 23. Create README installation section (simple)

Add a markdown section describing pip installation and required Python version.

**Acceptance:** README contains an 'Installation' heading with pip command.

## 24. Add usage examples to README (simple)

Provide example CLI invocations for checking and fixing configurations.

**Acceptance:** README includes a 'Usage' heading with example commands and expected output snippets.

## 25. Document each validation rule in README (simple)

Explain duplicate server detection, binary existence, env var validation, and endpoint reachability.

**Acceptance:** README has a 'Validation Rules' section listing all four checks.

## 26. Add FAQ section to README (simple)

Answer common questions such as 'What if a binary is optional?' and 'How to ignore a server?'

**Acceptance:** README contains an 'FAQ' heading with at least two Q&A entries.

## 27. Configure flake8 linting in project (simple)

Add a .flake8 config file enforcing max line length 88 and ignore E203, and ensure CI runs flake8.

**Acceptance:** Running `flake8 src` passes with no violations in existing code.

## 28. Add GitHub Actions CI workflow (simple)

Create .github/workflows/ci.yml that installs dependencies, runs flake8, and executes pytest.

**Acceptance:** Workflow file exists and validates against GitHub Action schema.

## 29. Create CHANGELOG entry for initial release (simple)

Add a CHANGELOG.md file with a v0.1.0 entry summarizing features implemented.

**Acceptance:** CHANGELOG contains a heading '## [0.1.0] - YYYY-MM-DD' with bullet points.

## 30. Publish package metadata in pyproject.toml (simple)

Add project name, version, description, authors, and required dependencies (requests, colorama).

**Acceptance:** Running `pip install .` succeeds and metadata is visible via `pip show mcp-linter`.

## 31. Add unit test for config saving after fixes (simple)

Ensure that after invoking the fix routine, the updated config file is valid JSON and matches expected structure.

**Acceptance:** Test loads the rewritten file and asserts JSON schema compliance.

## 32. Implement graceful handling of malformed JSON (simple)

Modify the loader to catch JSONDecodeError and raise a custom ConfigParseError with a helpful message.

**Acceptance:** Loading a broken JSON file raises ConfigParseError, not a generic exception.

## 33. Test malformed JSON error handling (simple)

Provide an invalid JSON file to the loader and assert ConfigParseError is raised.

**Acceptance:** Test passes confirming proper exception type.

## 34. Add command‑line option to output results as JSON (simple)

Introduce '--json' flag that prints the aggregated check results in JSON format instead of colored text.

**Acceptance:** Running CLI with '--json' outputs valid JSON to stdout.

## 35. Test '--json' output format (simple)

Capture stdout of the CLI with '--json' and parse it with json.loads to ensure it is valid.

**Acceptance:** Test succeeds without JSON parsing errors.

## 36. Add version command to CLI (simple)

Implement '--version' flag that prints the package version from pyproject.toml.

**Acceptance:** Running CLI with '--version' prints a semantic version string and exits 0.

## 37. Write test for '--version' output (simple)

Assert that the version flag output matches the version defined in pyproject.toml.

**Acceptance:** Test passes confirming version consistency.

## 38. Finalize packaging with entry point (simple)

Configure [project.scripts] in pyproject.toml to expose `mcp-lint` command pointing to src.cli:main.

**Acceptance:** After `pip install .`, executing `mcp-lint --help` works.
