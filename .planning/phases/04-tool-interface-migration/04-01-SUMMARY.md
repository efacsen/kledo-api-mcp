---
phase: 04-tool-interface-migration
plan: 01
subsystem: tests
tags: [testing, contract-tests, tdd, interface-migration, mcp]
dependency_graph:
  requires: []
  provides: [contract-test-suite-04]
  affects: [04-02-PLAN.md, 04-03-PLAN.md]
tech_stack:
  added: []
  patterns: [contract-testing, red-green-tdd, pytest-parametrize]
key_files:
  created:
    - tests/test_tools_interface.py
  modified: []
key_decisions:
  - "TestProgressReporting uses mcp._tool_manager.tools dict to introspect registered handler fn signatures — no live API calls"
  - "asyncio_mode=auto from pyproject.toml covers async test methods; no @pytest.mark.asyncio needed"
  - "27 failures in the new file are intentional RED state; full suite still exits 0 at 45.08% coverage"
metrics:
  duration_minutes: 8
  completed_date: "2026-04-10"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
---

# Phase 04 Plan 01: Contract Test Scaffold for Interface Migration Summary

Contract test suite written for Phase 4 @mcp.tool() decorator migration — 4 test classes covering interface removal, registration count regression guard, annotation presence, and progress-ctx injection.

## What Was Built

`tests/test_tools_interface.py` with four test classes:

| Class | Tests | Current State | Turns GREEN When |
|-------|-------|---------------|-----------------|
| TestModuleInterfaceContracts | 22 | RED (expected) | All 11 modules migrated (Plan 04-02) |
| TestToolRegistrationCount | 2 | GREEN | Must stay GREEN after every plan |
| TestToolAnnotations | 2 | RED (expected) | Plan 04-03 adds ToolAnnotations |
| TestProgressReporting | 3 | RED (expected) | Plan 04-02 adds ctx: Context to 3 handlers |

## Test Results

```
27 failed, 309 passed, 10 skipped
Required test coverage of 45% reached. Total coverage: 45.08%
```

All 27 failures are in the new file and are the correct pre-migration RED state. The 309 previously-passing tests remain passing. Coverage floor of 45% is met.

## RED/GREEN Breakdown

**GREEN (2 tests — pass now and must remain passing):**
- `TestToolRegistrationCount::test_mcp_has_exactly_24_tools`
- `TestToolRegistrationCount::test_all_category_prefixes_present`

**RED (22 — TestModuleInterfaceContracts):**
- 11 × `test_module_has_no_get_tools` — all 11 modules still export `get_tools()`
- 11 × `test_module_has_no_handle_tool` — all 11 modules still export `handle_tool()`

**RED (2 — TestToolAnnotations):**
- `test_all_tools_have_read_only_hint` — bridge adds tools without annotations
- `test_all_tools_have_open_world_hint` — bridge adds tools without annotations

**RED (3 — TestProgressReporting):**
- `test_progress_tool_has_ctx_parameter[commission_report]` — bridge wrapper has no ctx
- `test_progress_tool_has_ctx_parameter[analytics_compare]` — bridge wrapper has no ctx
- `test_progress_tool_has_ctx_parameter[revenue_summary]` — bridge wrapper has no ctx

## Implementation Notes

The `_get_handler` helper in TestProgressReporting accesses `mcp._tool_manager.tools[name].fn` to retrieve the registered callable without invoking the live API. This is an internal FastMCP attribute — if the SDK changes the internal structure, this helper will need updating.

## Deviations from Plan

None — plan executed exactly as written. ruff auto-fixed one unused `import os` statement.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. Test file only imports modules and inspects their attributes.

## Self-Check: PASSED

| Item | Result |
|------|--------|
| tests/test_tools_interface.py exists | FOUND |
| Commit d178bfd exists | FOUND |
| Full suite exits 0 at >=45% coverage | 45.08% — PASS |
