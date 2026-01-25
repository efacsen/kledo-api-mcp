---
status: testing
phase: 04-smart-routing
source: 04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md
started: 2026-01-22T19:44:00Z
updated: 2026-01-22T19:44:00Z
---

## Current Test

number: 1
name: Bilingual Synonym Dictionary
expected: |
  The routing module provides a SYNONYM_MAP with at least 50 terms covering English and Indonesian business vocabulary. Key terms like "invoice", "customer", "revenue", "vendor", "bill" map to tool names.
awaiting: user response

## Tests

### 1. Bilingual Synonym Dictionary
expected: The routing module provides a SYNONYM_MAP with at least 50 terms covering English and Indonesian business vocabulary. Key terms like "invoice", "customer", "revenue", "vendor", "bill" map to tool names.
result: [pending]

### 2. Fuzzy Typo Correction
expected: Misspelled terms like "invoise" or "custmer" return the closest matching tool with a similarity score. RapidFuzz fuzzy matching with 80% threshold is working.
result: [pending]

### 3. Extended Date Parser
expected: The date parser recognizes patterns like "last week", "this month", "Q1", "2025" and distinguishes calendar-based dates (ISO weeks) from rolling windows (last 7 days).
result: [pending]

### 4. Pattern Matching for Idiomatic Expressions
expected: Queries like "who owes me money", "show outstanding invoices", or "revenue by sales rep" are recognized as specific patterns and route to the correct tools immediately.
result: [pending]

### 5. Keyword Extraction and Scoring
expected: Query keywords are normalized to canonical forms (e.g., "invoices" -> "invoice") and matched against tool keywords. Tools are scored based on relevance with action verb boost.
result: [pending]

### 6. Main Router Integration
expected: Calling route_query() with a business question returns a RoutingResult with matched tools, confidence score, and suggested parameters. Router handles vague queries by requesting clarification.
result: [pending]

### 7. Multi-Language Query Support
expected: Queries in both English and Indonesian (e.g., "tampilkan faktur", "daftar vendor") are correctly parsed and routed to the appropriate tools.
result: [pending]

## Summary

total: 7
passed: 0
issues: 0
pending: 7
skipped: 0

## Gaps

[none yet]
