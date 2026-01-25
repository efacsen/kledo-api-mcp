# Codebase Concerns

**Analysis Date:** 2026-01-21

## Tech Debt

**Bare Exception Handling:**
- Issue: Use of bare `except:` clause in `parse_date_range()` function masks all exceptions
- Files: `src/utils/helpers.py:96`
- Impact: Makes debugging difficult; non-parsing errors (disk errors, out-of-memory) silently fail without logging
- Fix approach: Replace bare `except:` with `except (ValueError, AttributeError)` and log unexpected exceptions separately

**Inconsistent Error Logging in Tool Handlers:**
- Issue: Tool handlers catch all exceptions with generic `except Exception as e` and convert to string responses
- Files: `src/tools/invoices.py`, `src/tools/orders.py`, `src/tools/products.py`, `src/tools/contacts.py`, `src/tools/deliveries.py`, `src/tools/financial.py`
- Impact: Stack traces lost; difficult to diagnose root causes in production; sensitive error details may leak through response messages
- Fix approach: Implement structured error handling with logging levels; separate user-facing messages from internal diagnostics

**Hardcoded Response Limits:**
- Issue: Tool handlers limit display to 20 items before truncation across multiple tools
- Files: `src/tools/invoices.py:175-191`, `src/tools/orders.py:140-154`, `src/tools/products.py:117`, `src/tools/deliveries.py:107-125`
- Impact: Users get incomplete data without clear indication of pagination; no offset mechanism to fetch remaining items
- Fix approach: Implement proper pagination interface; allow users to specify page/limit or request "all" with confirmation

**MD5 Hashing for Cache Keys:**
- Issue: Uses MD5 for cache key generation in `calculate_hash()`
- Files: `src/utils/helpers.py:11-23`
- Impact: While not a cryptographic use case, MD5 is considered broken; doesn't affect security but signals non-standard practice
- Fix approach: Replace with SHA256 for better collision resistance and future-proofing

**Manual Token Expiry Management:**
- Issue: Token expiry tracked with `datetime` comparison; no automatic refresh during active sessions
- Files: `src/auth.py:42`, `src/kledo_client.py:118`
- Impact: If token expires mid-request, request will fail; `ensure_authenticated()` is only called at start of `_request()`, not mid-request
- Fix approach: Implement automatic token refresh on 401 responses; retry failed requests after refresh

## Known Bugs

**Date Range Parser Missing Boundary Checks:**
- Symptoms: `parse_date_range()` may return invalid dates for edge cases
- Files: `src/utils/helpers.py:42-99`
- Trigger: Calling with malformed input like empty string, non-ISO format, invalid month numbers
- Workaround: None; ensure valid input format in calling code

**Safe Get Does Not Distinguish Between Missing and Null:**
- Symptoms: `safe_get(data, "key")` returns same default value for missing keys and explicit `None` values
- Files: `src/utils/helpers.py:102-125`
- Trigger: When API response contains `null` values (common in optional fields)
- Workaround: None; cannot differentiate intentional null from missing field

**Cache Configuration File Not Validated:**
- Symptoms: Malformed YAML in `cache_config.yaml` silently defaults to factory settings
- Files: `src/cache.py:78-104`, `src/kledo_client.py:42-58`
- Trigger: Invalid YAML syntax or missing required keys in config files
- Workaround: Manually restart with corrected config; no validation errors reported

## Security Considerations

**Plain Text Credential Storage:**
- Risk: Passwords stored in plaintext in environment variables and `.env` file
- Files: `.env.example`, `src/server.py:51-52`, `src/auth.py:14-26`
- Current mitigation: Documentation recommends storing `.env` in `.gitignore`; relies on OS file permissions
- Recommendations:
  1. Implement credential encryption using `cryptography` library
  2. Support cloud secret management (AWS Secrets Manager, Azure Key Vault)
  3. Add runtime validation that `.env` file permissions are 0600
  4. Document credential rotation procedures

**Credentials in Configuration Files:**
- Risk: Kledo credentials exposed if MCP config file is shared or committed to version control
- Files: `README.md:70-80` shows embedding credentials in Claude Desktop config
- Current mitigation: Documentation recommends environment variables
- Recommendations:
  1. Provide secure credential provisioning script
  2. Add pre-commit hook to detect `.env` and config files
  3. Document OAuth/token-based authentication if available in Kledo API

**API Token Logging:**
- Risk: Bearer tokens logged in debug messages
- Files: `src/auth.py:85` (token expiry logged), potentially in request logging
- Current mitigation: Log level filtering (INFO by default hides debug logs)
- Recommendations:
  1. Implement token masking in all log output (log `"Bearer ***"` instead of full token)
  2. Add audit trail for token access
  3. Implement token expiry alerts

**No Input Validation on Tool Arguments:**
- Risk: Tool handlers pass untrusted input directly to API calls
- Files: All `src/tools/*.py` handler functions
- Current mitigation: API server presumably validates; YAML config acts as schema
- Recommendations:
  1. Implement Pydantic models for tool argument validation
  2. Sanitize string inputs (check for injection patterns)
  3. Validate numeric ranges before API calls

**Unencrypted Cache Storage:**
- Risk: In-memory cache may contain sensitive financial data
- Files: `src/cache.py`
- Current mitigation: Only GET requests cached; in-process memory isolation
- Recommendations:
  1. Add cache encryption for sensitive categories (invoices, financial data)
  2. Document cache security implications for production deployment
  3. Implement cache purge on shutdown

**No Rate Limiting:**
- Risk: MCP tools can hammer Kledo API without throttling
- Files: `src/kledo_client.py:91-171`
- Current mitigation: None
- Recommendations:
  1. Implement token bucket rate limiting per tool
  2. Add request deduplication for identical concurrent requests
  3. Implement exponential backoff for failed requests

## Performance Bottlenecks

**In-Memory Cache Unbounded Growth:**
- Problem: Cache eviction uses LRU but max_size is fixed at 1000 entries
- Files: `src/cache.py:60`, `src/cache.py:138-151`
- Cause: No configurable memory limits; large response objects not compressed
- Improvement path:
  1. Implement size-based eviction (max bytes) instead of just entry count
  2. Add response compression for cached data
  3. Make cache settings configurable per deployment

**Synchronous Nested API Calls:**
- Problem: Tool handlers make sequential API calls that could be parallelized
- Files: `src/tools/financial.py` (multiple report summaries), `src/tools/invoices.py` (list + calculate summaries)
- Cause: Current implementation calls `client.get()` once per query
- Improvement path:
  1. Batch related API calls using `asyncio.gather()`
  2. Cache intermediate results (e.g., cache sales summary, build from cached invoices)
  3. Implement request coalescing for identical concurrent requests

**Full Response Display in Tools:**
- Problem: Tools render full markdown output in memory before returning
- Files: All `src/tools/*.py` (lines accumulate in `result` lists)
- Cause: String concatenation approach; no streaming
- Improvement path:
  1. Implement streaming response generation
  2. Add response truncation with "next page" tokens
  3. Defer formatting until requested by client

**Endpoint Configuration Loaded at Startup:**
- Problem: Static YAML endpoints file; API changes require server restart
- Files: `src/kledo_client.py:37-38, 42-57`
- Cause: Single load on client initialization
- Improvement path:
  1. Implement periodic endpoint config refresh
  2. Add endpoint discovery from API metadata
  3. Cache endpoint config with TTL

## Fragile Areas

**Authentication State Management:**
- Files: `src/auth.py:28-29`, `src/kledo_client.py:118`
- Why fragile: Token expiry detection relies on client clock; no server-side validation of token freshness
- Safe modification:
  1. Add server time sync before expiry checks
  2. Implement exponential backoff with jitter on failed auth
  3. Add retry mechanism that refreshes token on 401
- Test coverage: Basic auth tests exist (`tests/test_auth.py`) but missing integration tests for token refresh during active requests

**Cache Key Generation:**
- Files: `src/kledo_client.py:75-89`, `src/utils/helpers.py:11-23`
- Why fragile: Parameter ordering in dict affects cache hits; nested params not sorted recursively
- Safe modification:
  1. Use stable JSON serialization with recursive sorting
  2. Add cache key versioning to invalidate old keys on schema changes
  3. Document cache key format requirements
- Test coverage: No tests for cache key collision or consistency

**Tool Handler Error Responses:**
- Files: All `src/tools/*.py` (exception handlers return string messages)
- Why fragile: MCP protocol expects structured TextContent; error strings may be misinterpreted by client
- Safe modification:
  1. Implement consistent error response format (JSON or structured text)
  2. Add error severity levels (warning vs. fatal)
  3. Add request ID tracking for debugging
- Test coverage: Tests mock successful paths; error cases minimally tested

**Date Range Parsing:**
- Files: `src/utils/helpers.py:42-99`
- Why fragile: Multiple hardcoded date formats; bare except clause; calendar arithmetic complex
- Safe modification:
  1. Use dateutil.parser for robust parsing
  2. Add comprehensive test cases for edge cases (leap years, DST transitions)
  3. Replace bare except with specific exception handling
- Test coverage: No unit tests for `parse_date_range()` function

## Scaling Limits

**Cache Per-Instance Only:**
- Current capacity: 1000 entries in memory
- Limit: Single process memory; no distributed cache
- Scaling path:
  1. Add Redis support for multi-instance deployments
  2. Implement consistent hashing for cache across instances
  3. Add cache invalidation broadcast mechanism

**Sequential Tool Invocation:**
- Current capacity: One tool call at a time via MCP protocol
- Limit: Cannot batch multiple tool calls in single request
- Scaling path:
  1. Implement tool composition/pipeline system
  2. Add batch operation support to MCP interface
  3. Optimize common query patterns (e.g., "get all invoices and summarize")

**Synchronous API Client:**
- Current capacity: Bounded by single thread execution
- Limit: Cannot handle concurrent requests from multiple MCP clients
- Scaling path:
  1. Use asyncio thread pool for concurrent tool handling
  2. Implement connection pooling in httpx client
  3. Add per-client request queuing

## Dependencies at Risk

**Custom Cache Implementation:**
- Risk: No TTL enforcement mechanism; expiration checked on access (lazy deletion)
- Impact: Failed reads won't trigger cleanup; stale data accumulates if entries never accessed again
- Migration plan:
  1. Evaluate Redis for production deployments
  2. Implement eager cleanup background task
  3. Add memory monitoring with alerts

**Tight Coupling to Kledo API Schema:**
- Risk: API response structure changes break multiple tools
- Impact: Safe `get()` calls mask schema mismatches; tools fail silently with empty results
- Migration plan:
  1. Implement API response schema validation with Pydantic
  2. Add schema version detection
  3. Create adapter layer for API version compatibility

## Missing Critical Features

**No Audit Trail:**
- Problem: No logging of what data was accessed, when, and by whom
- Blocks: Cannot track data access for compliance; no forensics for security incidents
- Recommendation: Implement structured audit logging with timestamps and user identification

**No Result Caching Control:**
- Problem: Users cannot force fresh data or disable cache for specific queries
- Blocks: Stale data issues cannot be diagnosed by users; no cache debugging
- Recommendation: Add `force_refresh` parameter to all tool handlers (already present in some)

**No Request Rate Metrics:**
- Problem: Cannot monitor API usage or detect anomalies
- Blocks: Cannot optimize based on actual usage patterns; no alerting on unusual activity
- Recommendation: Implement request counter metrics per tool and time window

**No Graceful Degradation:**
- Problem: Single API failure causes tool to error; no fallback data sources
- Blocks: Cannot provide cached stale data when API unavailable; binary success/failure
- Recommendation: Implement circuit breaker pattern with stale-cache fallback

## Test Coverage Gaps

**Missing Integration Tests:**
- What's not tested: Full request lifecycle with actual API (mocked currently); token refresh during active requests
- Files: `tests/` directory shows unit tests only; no integration or end-to-end tests
- Risk: Integration bugs remain undetected; authentication refresh rarely tested
- Priority: High

**Missing Error Path Tests:**
- What's not tested: Tool handlers with malformed API responses; cache failures; network timeouts
- Files: `src/tools/*.py` exception handlers untested
- Risk: Error handling logic bugs remain undetected; incorrect error messages in production
- Priority: High

**Missing Performance Tests:**
- What's not tested: Cache hit rate under load; response time with large datasets; memory usage growth
- Files: No performance benchmarks present
- Risk: Performance regressions ship undetected; scaling limits unknown
- Priority: Medium

**Missing Edge Case Tests:**
- What's not tested: Date boundaries (Dec 31 - Jan 1), DST transitions, leap years; empty result sets; very large numbers
- Files: `src/utils/helpers.py:42-99` has no test coverage
- Risk: Date calculations fail on transitions; formatting breaks with extreme values
- Priority: Medium

---

*Concerns audit: 2026-01-21*
