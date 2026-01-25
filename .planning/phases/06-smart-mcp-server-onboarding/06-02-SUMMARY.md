---
phase: 06-smart-mcp-server-onboarding
plan: 02
status: COMPLETE
type: execute
subsystem: cli-interface
tags: [cli, onboarding, user-experience, command-line, testing]
completed: 2026-01-25
duration: 6 minutes

# Dependency Graph
requires:
  - 06-01 (setup wizard and first-run detection)
provides:
  - CLI argument parser with 5 commands
  - Command handlers for setup, test, show-config, init, version
  - Entry point with CLI integration and first-run detection
  - Comprehensive test suite for CLI functionality
affects:
  - 06-03 (README documentation references CLI commands)
  - Future: User onboarding experience improved

# Tech Stack
tech-stack:
  added:
    - argparse for command-line parsing
  patterns:
    - Command handler pattern for routing
    - Async testing with monkeypatch and mocks
    - Idempotent command design

# Key Files
key-files:
  created:
    - src/cli.py (355 lines) - CLI parser and command handlers
    - tests/test_cli.py (476 lines) - Comprehensive test suite
  modified:
    - kledo_mcp.py - Entry point with CLI integration

# Commits
commits:
  - hash: 93764f7
    message: "feat(06-02): add CLI argument parser and command handlers"
    files: [src/cli.py]
  - hash: bd395c8
    message: "feat(06-02): update entry point with CLI integration and first-run detection"
    files: [kledo_mcp.py]
  - hash: c0a2865
    message: "test(06-02): add comprehensive CLI integration tests"
    files: [tests/test_cli.py]

# Decisions
decisions:
  - title: "5 CLI commands: --setup, --test, --show-config, --init, --version"
    rationale: "Cover all essential use cases (setup, validation, configuration, troubleshooting)"
    scope: cli-interface
  - title: "OS-specific paths for Claude Desktop config"
    rationale: "Better UX - users get exact path for their OS (macOS, Windows, Linux)"
    scope: show-config-command
  - title: "Idempotent command design"
    rationale: "Safe to run multiple times - reduces user confusion and support issues"
    scope: all-commands
  - title: "Mock all external dependencies in tests"
    rationale: "Fast tests, no real API calls, isolated unit testing"
    scope: testing
  - title: "--init as alias for --setup"
    rationale: "Common CLI convention - matches user expectations"
    scope: cli-interface
---

# Phase 6 Plan 02: CLI Integration and Validation Commands Summary

**One-liner:** CLI interface with --setup, --test, --show-config commands plus first-run detection

## Objective

Integrate setup wizard into entry point and add CLI commands for validation and configuration display, making first-run seamless and providing utility commands for troubleshooting.

## What Was Built

### 1. CLI Argument Parser (src/cli.py)

**parse_args(argv: list[str]) -> argparse.Namespace:**
- Parses 5 commands: --setup, --test, --show-config, --init, --version
- Clear help text with examples
- Links to documentation

**Command Handlers:**

1. **handle_setup()** - Run interactive setup wizard
   - Calls run_setup_wizard() from src.setup
   - Idempotent - safe to run multiple times
   - Returns 0 on success, 1 on failure

2. **handle_test()** - Test connection to Kledo API
   - Loads .env configuration
   - Creates KledoAuthenticator instance
   - Tests authentication + API access
   - Colored output (green for success, red for errors)
   - Returns 0 on success, 1 on failure

3. **handle_show_config()** - Display Claude Desktop configuration JSON
   - Generates valid mcpServers JSON
   - OS-specific installation paths (macOS, Windows, Linux)
   - Shows example if .env doesn't exist
   - Clear instructions for adding to Claude Desktop
   - Returns 0 always

4. **handle_version()** - Show version information
   - Reads version from pyproject.toml
   - Displays project links
   - Returns 0 always

5. **dispatch_command(args)** - Route to appropriate handler
   - Maps parsed args to command handlers
   - --init routes to handle_setup (alias)

### 2. Entry Point Integration (kledo_mcp.py)

**Updated main() function:**
- Parse command-line arguments first
- If command specified → dispatch it
- If no command → check first-run
- If first run → run setup wizard automatically
- After setup (or if already configured) → start server

**First-run detection flow:**
```python
wizard = SetupWizard()
if wizard.detect_first_run():
    print("Welcome to Kledo MCP Server!")
    success = asyncio.run(wizard.run())
    if success:
        print("Setup complete! Starting server...")
    else:
        return 1
```

**Backward compatible:**
- Keeps existing subprocess pattern for server start
- PYTHONPATH setup preserved
- Module isolation maintained

### 3. Comprehensive Test Suite (tests/test_cli.py)

**26 tests organized in 6 classes:**

1. **TestParseArgs** (6 tests)
   - Verify each command flag parsed correctly
   - Test no-args case

2. **TestHandleSetup** (2 tests)
   - Mock run_setup_wizard for success/failure
   - Verify exit codes

3. **TestHandleTest** (4 tests)
   - No config file
   - Missing API key
   - Successful connection
   - Failed connection
   - All using mocks - no real API calls

4. **TestHandleShowConfig** (3 tests)
   - With existing config
   - Without config (example mode)
   - OS-specific paths (macOS, Windows, Linux)

5. **TestHandleVersion** (2 tests)
   - Version output format
   - Reading from pyproject.toml

6. **TestDispatchCommand** (6 tests)
   - Each command routes correctly
   - No command handling

7. **TestCommandIdempotency** (3 tests)
   - Setup can run multiple times
   - Test can run multiple times
   - Show-config can run multiple times

**All tests use mocking:**
- monkeypatch fixture for import mocking
- capsys fixture for output capture
- Mock/AsyncMock for external dependencies
- No actual API calls made

## Testing & Verification

**Manual Testing:**
```bash
# All commands work
kledo-mcp --version       # Shows version
kledo-mcp --help          # Shows help
kledo-mcp --setup         # Runs wizard
kledo-mcp --test          # Tests connection
kledo-mcp --show-config   # Shows JSON
```

**Unit Tests:**
```bash
pytest tests/test_cli.py -v
# Result: 26 passed, all using mocks
```

**Import Tests:**
```bash
python -c "from src.cli import parse_args; print('OK')"
# Result: OK
```

## Deviations from Plan

None - plan executed exactly as written.

## Key Technical Details

**ANSI Color Codes:**
- Reuse Colors class from src.setup
- No external dependencies
- Green (✓), Red (✗), Yellow (⚠), Cyan (info)

**Error Handling:**
- Clear error messages for missing config
- Guidance on how to fix (run --setup)
- Graceful degradation (show example config if .env missing)

**OS Detection:**
```python
import platform
os_name = platform.system()  # "Darwin", "Windows", "Linux"
```

**Path Logic:**
- macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
- Windows: ~/AppData/Roaming/Claude/claude_desktop_config.json
- Linux: ~/.config/Claude/claude_desktop_config.json

## Success Criteria

All criteria met:

- [x] All 5 CLI commands implemented (--setup, --test, --show-config, --init, --version)
- [x] Entry point detects first-run and triggers setup wizard
- [x] --show-config outputs valid Claude Desktop JSON
- [x] --test validates connection without starting server
- [x] Commands are idempotent (safe to run multiple times)
- [x] Unit tests pass with comprehensive coverage
- [x] Backward compatible with python -m src.server
- [x] SUMMARY.md created in phase directory

## Impact

**User Experience Improvements:**

1. **First-run is seamless** - Users see welcome message, wizard runs automatically
2. **Validation without server start** - Can test connection with --test
3. **Easy configuration** - --show-config shows exact JSON and paths
4. **Troubleshooting** - Clear error messages with fix guidance
5. **Idempotent operations** - Safe to run commands multiple times

**Developer Experience:**

1. **CLI testing framework** - Pattern for testing command handlers
2. **Mocking best practices** - No real API calls in tests
3. **OS-specific handling** - Template for cross-platform features

## Next Phase Readiness

**Phase 6 Plan 03 (README Quick Start):**
- Ready - Can document all CLI commands
- --setup, --test, --show-config all working
- OS-specific paths available from --show-config

**Future Enhancements:**
- Could add --doctor command for troubleshooting
- Could add --logs command to show recent logs
- Could add --config-path to show .env location

## Files Changed Summary

**Created:**
- src/cli.py (355 lines) - Complete CLI implementation
- tests/test_cli.py (476 lines) - Comprehensive test suite

**Modified:**
- kledo_mcp.py (82 lines) - Entry point with CLI integration

**Total:** 3 files, 913 lines of code

## Metrics

- **Tasks:** 3/3 completed
- **Tests:** 26 tests, all passing
- **Commits:** 3 atomic commits
- **Duration:** 6 minutes
- **Lines of code:** 913 (831 new, 82 modified)
