---
phase: 06-smart-mcp-server-onboarding
plan: 01
subsystem: onboarding
tags: [setup, configuration, dotenv, validation, first-run-detection]

# Dependency graph
requires:
  - phase: 05-domain-model-field-mapping
    provides: "Production-ready MCP server with 28 tools"
provides:
  - ConfigManager for .env validation and file operations
  - SetupWizard with interactive prompts and first-run detection
  - Comprehensive test suite for configuration management
affects: [06-02, 06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ANSI color codes for terminal UI (no external deps)"
    - "Injectable ConfigManager for testability"
    - "Validation with tuple[bool, str] pattern for errors"

key-files:
  created:
    - src/config_manager.py
    - src/setup.py
    - tests/test_setup_wizard.py
  modified: []

key-decisions:
  - "Use python-dotenv override=True for test isolation"
  - "HTTPS-only validation for base URLs (security requirement)"
  - "20+ char minimum for API keys, 30+ for kledo_pat_ prefix"
  - "ANSI color codes instead of external library (zero deps)"

patterns-established:
  - "Validation returns (bool, str) for is_valid and error_message"
  - "ConfigManager injectable for testing"
  - "Interactive prompts with validation loops and retry logic"

# Metrics
duration: 5min
completed: 2026-01-25
---

# Phase 6 Plan 1: Setup Wizard Foundation Summary

**Interactive setup wizard with validation, first-run detection, and .env management using python-dotenv**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-25T08:06:04Z
- **Completed:** 2026-01-25T08:11:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- ConfigManager handles .env validation and creation with comprehensive checks
- SetupWizard provides interactive prompts with ANSI color output
- First-run detection accurately identifies configuration state
- Connection testing validates credentials before saving
- 28 passing tests with 82% coverage on ConfigManager

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ConfigManager** - `204ad42` (feat)
2. **Task 2: Create SetupWizard** - `d92b464` (feat)
3. **Task 3: Add unit tests** - `14d70c8` (test)

## Files Created/Modified

**Created:**
- `src/config_manager.py` - Validation and .env file operations
- `src/setup.py` - Interactive setup wizard with first-run detection
- `tests/test_setup_wizard.py` - Comprehensive test suite (28 tests)

## Decisions Made

**1. HTTPS-only for base URLs**
- Rationale: Security requirement, prevent accidental plaintext API traffic
- Implementation: validate_base_url() rejects HTTP scheme
- Pattern: `parsed.scheme != "https"` → error

**2. API key length validation**
- Generic keys: 20+ characters minimum
- kledo_pat_ prefix: 30+ characters minimum
- Rationale: Ensure sufficient entropy for security

**3. Use python-dotenv with override=True**
- Rationale: Test isolation - prevent tests reading project .env
- Implementation: `load_dotenv(path, override=True)` in load_current_config()
- Impact: Tests properly isolated with tmp_path fixtures

**4. ANSI color codes (no external deps)**
- Rationale: Avoid adding dependencies for simple terminal colors
- Implementation: Colors class with GREEN/RED/YELLOW constants
- Pattern: `\033[92m✓\033[0m` for success checkmarks

**5. Injectable ConfigManager**
- Rationale: Testability - allow mocking and tmp_path usage
- Pattern: `SetupWizard(config_manager: Optional[ConfigManager] = None)`
- Impact: All tests use tmp_path for isolation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**1. Test isolation with dotenv**
- **Problem:** load_dotenv() searches parent directories, tests read project .env
- **Solution:** Added override=True parameter and monkeypatch.chdir(tmp_path)
- **Verification:** test_load_current_config_with_file now passes with tmp data

**2. httpx mocking complexity**
- **Problem:** Initial patch path "src.setup.httpx" failed (httpx imported in function)
- **Solution:** Patch "httpx.AsyncClient" directly, not module attribute
- **Verification:** All 3 connection test cases pass (success, 401, network error)

## Next Phase Readiness

**Ready:**
- ConfigManager validates and creates .env files
- SetupWizard orchestrates full setup flow
- First-run detection works
- Connection testing integrated with KledoAuthenticator

**For 06-02 (Validation commands):**
- Setup wizard can be invoked with run_setup_wizard()
- ConfigManager provides load_current_config() for --show-config
- Connection test pattern can be reused for --test command

**For 06-03 (README update):**
- Setup wizard provides clear success message with next steps
- Error messages are user-friendly with helpful guidance

---
*Phase: 06-smart-mcp-server-onboarding*
*Completed: 2026-01-25*
