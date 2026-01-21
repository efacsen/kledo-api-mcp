# Pitfalls Research: MCP Server API Mapping

**Domain:** API mapping for Kledo accounting software MCP server
**Researched:** 2026-01-21
**Project context:** 30+ existing tools, adding comprehensive API mapping with embedded descriptions and simple keyword routing

---

## Critical Pitfalls

Mistakes that would seriously harm the project or require rewrites.

### Pitfall 1: Tool Description Token Bloat

**What goes wrong:** Tool descriptions become verbose and consume excessive context tokens. Even with only 30 tools, poorly written descriptions can waste 10,000-20,000 tokens before a conversation starts.

**Why it happens:** Developers copy API documentation verbatim into tool descriptions, include every parameter detail, add extensive examples, or use nested JSON schemas with verbose property descriptions.

**Consequences:**
- 5-10% of Claude's context window consumed by tool definitions alone
- Slower response times and higher API costs
- LLM may truncate or ignore later tools in the list
- Reduced space for actual conversation and results

**Warning signs:**
- Tool definitions individually exceed 200 tokens
- Parameter descriptions repeat information from the name
- Descriptions include usage examples inline
- Nested schemas have redundant type annotations

**Prevention:**
- Keep each tool description under 150 tokens
- Use parameter names that are self-documenting (`invoice_id` not `id`)
- Put examples in separate documentation, not in tool schema
- Review token count during development with a token counter

**Phase to address:** Phase 1 - Establish description guidelines before writing any new tool descriptions.

**Sources:** [Anthropic Engineering - Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents), [MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/)

---

### Pitfall 2: Overlapping Tool Functionality Creates Selection Confusion

**What goes wrong:** Multiple tools with similar descriptions cause the LLM to choose incorrectly or inconsistently between them.

**Why it happens:** Organic growth of tool coverage without reviewing how tools relate. Example: `invoice_list_sales` and `financial_sales_summary` both mention "sales" without clear differentiation.

**Consequences:**
- LLM selects wrong tool 15-30% of the time
- Users get unexpected results
- Agent makes multiple tool calls when one would suffice
- Debugging becomes difficult ("why did it pick that tool?")

**Warning signs:**
- Two tools share more than 3 keywords in descriptions
- Users report inconsistent results for similar queries
- Testing shows different tool selection for semantically equivalent prompts
- Tool descriptions use hedging language ("can also be used for...")

**Prevention:**
- Audit all tool descriptions for keyword overlap
- Each tool must have unique "trigger phrases" in its description
- Use explicit disambiguation: "Use this for X, NOT for Y"
- Create a tool selection matrix during design

**Phase to address:** Phase 1 - Create tool disambiguation matrix before expanding API coverage.

**Sources:** [Anthropic Engineering - Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

### Pitfall 3: Keyword Routing Fails on Domain Synonyms

**What goes wrong:** Simple keyword routing misses queries using accounting synonyms that your keywords don't cover.

**Why it happens:** Accounting domain has many synonyms: "invoice" vs "bill", "customer" vs "client" vs "contact", "revenue" vs "sales" vs "income", "vendor" vs "supplier".

**Consequences:**
- Users get "no matching tool" or wrong tool selection
- Domain expertise required to phrase queries correctly
- Reduced adoption by users unfamiliar with Kledo's terminology

**Warning signs:**
- Users rephrase queries multiple times to get results
- Support tickets about "obvious" queries not working
- Tool routing tests fail on synonym variations
- Kledo documentation uses different terms than your tool descriptions

**Prevention:**
- Build synonym map for accounting domain during design
- Include common synonyms in tool descriptions (but keep concise)
- Test routing with domain synonym variations
- Document "trigger phrases" for each tool that include synonyms

**Phase to address:** Phase 1 - Build synonym dictionary before finalizing tool descriptions.

---

### Pitfall 4: Parameter Validation Trusts LLM Input

**What goes wrong:** Tools assume LLM will provide correct parameter types and values, leading to API errors or incorrect data retrieval.

**Why it happens:** Descriptions say "use existing invoice_id" but LLM may hallucinate IDs, use wrong formats, or pass strings instead of integers.

**Consequences:**
- API errors returned to users
- Silent wrong results (querying non-existent record returns empty)
- Security issues if IDs are user-controllable

**Warning signs:**
- API errors with "invalid parameter" messages
- Empty results when data should exist
- Type coercion errors in logs
- Successful queries returning unexpected empty sets

**Prevention:**
- Validate all inputs before API calls
- Provide clear error messages for invalid inputs
- Use enums where possible (status codes, contact types)
- Never assume LLM follows parameter instructions

**Phase to address:** Phase 2 - Add validation layer during tool handler implementation.

**Sources:** [Tool (aka Function Calling) Best Practices](https://medium.com/@laurentkubaski/tool-or-function-calling-best-practices-a5165a33d5f1)

---

## Common Mistakes

Frequent errors in similar projects that cause delays or technical debt.

### Mistake 1: Wrapping API Verbatim Instead of Designing for Agents

**What goes wrong:** Tool descriptions mirror API documentation rather than describing agent-friendly use cases.

**Why it happens:** Fastest path from API docs to MCP tool is copy-paste. Developer thinks "accuracy" means matching API docs exactly.

**Consequences:**
- Descriptions use API jargon users don't know
- Agent struggles to map natural language to technical parameters
- Tool coverage complete but usability poor

**Prevention:**
- Write descriptions as if explaining to a non-technical user
- Start with "Use this to..." not "Calls the /api/v1/..."
- Test descriptions with natural language queries before shipping

**Phase to address:** Phase 1 - Establish description style guide.

**Sources:** [Anthropic Engineering - Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

### Mistake 2: Returning Raw API Responses

**What goes wrong:** Tools return full API responses including irrelevant metadata, nested structures, and technical fields.

**Why it happens:** Easier to return raw JSON than format for readability. Developer assumes agent will parse what it needs.

**Consequences:**
- Agent wastes tokens processing irrelevant data
- Context window filled with JSON boilerplate
- Users see technical output instead of answers

**Warning signs:**
- Tool responses exceed 5,000 tokens for simple queries
- Responses include `meta`, `pagination`, `debug` fields
- Users ask follow-up questions to interpret raw output

**Prevention:**
- Format responses as markdown summaries (current codebase does this well)
- Return only fields relevant to typical queries
- Summarize lists instead of returning full arrays
- Limit list displays (current 20-item limit is good)

**Phase to address:** Already addressed in current codebase - maintain this pattern.

---

### Mistake 3: Missing Negative Guidance in Descriptions

**What goes wrong:** Descriptions say what tools CAN do but not what they CANNOT do, leading to misuse.

**Why it happens:** Positive framing feels more helpful. Edge cases discovered only in production.

**Consequences:**
- Users expect functionality that doesn't exist
- Agent calls tool for unsupported use cases
- Error messages don't explain why request failed

**Prevention:**
- Add "This tool does NOT..." where ambiguity exists
- Document parameter limitations explicitly
- Include scope boundaries (e.g., "read-only, cannot modify invoices")

**Phase to address:** Phase 1 - Add negative guidance to ambiguous tools.

---

### Mistake 4: Inconsistent Naming Conventions

**What goes wrong:** Tools follow multiple naming patterns, making it hard for LLM to predict tool names.

**Why it happens:** Different developers, different phases, or copying from different sources.

**Consequences:**
- LLM may hallucinate tool names based on patterns
- Users can't predict tool availability
- Maintenance burden increases

**Warning signs:**
- Mix of `verb_noun` and `noun_verb` patterns
- Inconsistent prefixes (`financial_` vs `finance_`)
- Some tools use abbreviations, others don't

**Prevention:**
- Establish naming convention: `{category}_{action}_{target}` (current pattern is good)
- Audit existing tools for consistency
- Document convention for future additions

**Phase to address:** Already addressed - current `financial_`, `invoice_`, `product_` prefixes are consistent.

---

### Mistake 5: Date Format Ambiguity

**What goes wrong:** Date parameters accept multiple formats inconsistently, causing silent failures or wrong date ranges.

**Why it happens:** Different API endpoints expect different formats. Helpers try to be "flexible" without proper validation.

**Consequences:**
- `2024-10` might be interpreted as October or invalid
- "last month" could mean different things
- Reports return unexpected date ranges

**Warning signs:**
- Date range queries return unexpected results
- Same date string works in some tools but not others
- No error when date format is wrong (silent failure)

**Prevention:**
- Standardize date format documentation in ALL tool descriptions
- Parse and validate dates at tool handler level
- Return explicit date range in response ("Showing: 2024-10-01 to 2024-10-31")
- Test date parsing with variations

**Phase to address:** Already partially addressed with `parse_date_range` helper - ensure consistency across all tools.

---

## Over-Engineering Risks

What NOT to over-complicate for this project scope.

### Risk 1: Full Vector Search for 30 Tools

**What it is:** Implementing semantic/vector search to route queries to tools.

**Why it's overkill:**
- 30-40 tools is well within keyword matching capability
- Vector search adds embedding model dependency
- Latency increases for minimal accuracy gain
- Operational complexity for hosting embeddings

**When you WOULD need it:**
- 100+ tools with significant overlap
- Multi-language query support
- Tools have very similar descriptions that keywords can't distinguish

**What to do instead:**
- Keyword routing with synonym expansion
- Category-based filtering (user specifies domain: "invoices", "reports")
- Clear, distinct tool descriptions that don't need semantic matching

**Sources:** [Why Top Engineers Are Ditching MCP Servers](https://www.flowhunt.io/blog/why-top-engineers-are-ditching-mcp-servers/)

---

### Risk 2: Dynamic Tool Loading Based on Context

**What it is:** Loading/unloading tools dynamically based on conversation context to save tokens.

**Why it's overkill for this project:**
- 30 tools at ~100 tokens each = ~3,000 tokens
- Claude's context window easily handles this
- Dynamic loading adds complexity and latency
- Tool selection becomes unpredictable

**When you WOULD need it:**
- 50+ MCP servers connected simultaneously
- Tool definitions consuming 50,000+ tokens
- Enterprise multi-domain scenarios

**What to do instead:**
- Keep all 30 tools loaded
- Focus on making each description token-efficient
- Let the LLM see all available tools for better selection

**Sources:** [Reducing MCP token usage by 100x](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2), [MCP and the "too many tools" problem](https://demiliani.com/2025/09/04/model-context-protocol-and-the-too-many-tools-problem/)

---

### Risk 3: Building a Custom Query Language

**What it is:** Creating a mini-DSL for users to specify exact filters and parameters.

**Why it's overkill:**
- Users want natural language, not new syntax
- DSL requires documentation and learning
- LLM can translate natural language to parameters

**What to do instead:**
- Trust LLM to extract parameters from natural language
- Provide clear parameter documentation
- Handle ambiguity by asking clarifying questions

---

### Risk 4: Comprehensive API Coverage (All 323 Endpoints)

**What it is:** Mapping every Kledo API endpoint to an MCP tool.

**Why it's overkill:**
- Many endpoints are administrative or rarely used
- More tools = more token overhead and selection confusion
- Maintenance burden scales with endpoint count

**What to do instead:**
- Prioritize high-value endpoints (current 40 of 323 is appropriate)
- Group related operations into single tools where possible
- Add endpoints based on user demand, not completeness

---

### Risk 5: Real-Time API Documentation Sync

**What it is:** Automatically updating tool descriptions when Kledo API docs change.

**Why it's overkill:**
- Kledo API changes infrequently
- Tool descriptions are curated, not auto-generated
- Adds deployment complexity

**What to do instead:**
- Manual review when Kledo releases updates
- Version-pin API compatibility
- Document which Kledo API version is supported

---

## Prevention Strategies

Actionable approaches to avoid the pitfalls above.

### Strategy 1: Tool Description Style Guide

Create a mandatory checklist for every tool description:

1. **Length check:** Under 150 tokens
2. **Trigger phrase:** Clear natural language that would invoke this tool
3. **Disambiguation:** How is this different from similar tools?
4. **Parameters:** Self-documenting names, explicit formats
5. **Scope:** What this tool does NOT do
6. **Synonyms:** Domain terms that map to this tool

### Strategy 2: Tool Selection Testing

Before release, test each tool with:

1. Direct query ("list my invoices")
2. Synonym query ("show my bills")
3. Ambiguous query ("sales data") - verify correct tool selected
4. Edge case query (empty results, invalid params)
5. Multi-tool query ("compare invoices to orders")

### Strategy 3: Token Budget Audit

Measure and limit:

- Total tool definition overhead: Target under 5,000 tokens
- Per-tool definition: Target under 150 tokens
- Tool response size: Target under 2,000 tokens for list operations

### Strategy 4: Domain Synonym Dictionary

Build and maintain mapping:

```
invoice: bill, sales invoice, customer invoice
vendor: supplier, provider
customer: client, buyer, contact (when type=1)
revenue: sales, income, receipts
expense: cost, purchase, spending
```

### Strategy 5: Naming Convention Enforcement

Pattern: `{category}_{action}_{target}`

Categories: `financial`, `invoice`, `order`, `product`, `contact`, `delivery`, `utility`
Actions: `list`, `get`, `search`, `summarize`
Targets: `sales`, `purchase`, `detail`, `totals`

Examples:
- `invoice_list_sales` (good)
- `get_sales_invoice` (bad - wrong order)
- `listInvoices` (bad - wrong format)

---

## Warning Signs

How to detect problems early during development and after deployment.

### During Development

| Signal | Indicates | Action |
|--------|-----------|--------|
| Tool description exceeds 200 tokens | Token bloat | Rewrite more concisely |
| Two tools share 3+ keywords | Overlap risk | Add disambiguation |
| Parameter named just `id` | Ambiguity | Rename to `{entity}_id` |
| Description starts with endpoint path | API wrapping | Rewrite for users |
| No `"required": []` for optional tools | Schema issue | Verify intentional |

### During Testing

| Signal | Indicates | Action |
|--------|-----------|--------|
| Same query selects different tools | Description ambiguity | Add negative guidance |
| Synonym query fails | Missing terms | Add to description |
| Parameter type error | Validation gap | Add input validation |
| Empty results when data exists | Query construction issue | Debug parameter mapping |

### In Production

| Signal | Indicates | Action |
|--------|-----------|--------|
| Users rephrase same query 3+ times | Routing failure | Expand trigger phrases |
| High rate of "no results" | Too narrow matching | Review keywords |
| Tool X never called | Overlap with similar tool | Consider merging |
| API errors in logs | Input validation gaps | Add parameter checking |

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Tool description rewrite | Token bloat, losing clarity | Set token budget, test with queries |
| Synonym expansion | Over-expansion causing false matches | Test disambiguation |
| Keyword routing | Missing domain terms | Build from user feedback |
| Adding write operations (future) | No confirmation flow | Require explicit approval |
| Multi-company support (future) | Context confusion | Scope tools per session |

---

## Sources

### MCP and Tool Design
- [Anthropic Engineering - Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/)
- [Tool (aka Function Calling) Best Practices](https://medium.com/@laurentkubaski/tool-or-function-calling-best-practices-a5165a33d5f1)
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)

### Token and Performance
- [MCP and the "too many tools" problem](https://demiliani.com/2025/09/04/model-context-protocol-and-the-too-many-tools-problem/)
- [Why Top Engineers Are Ditching MCP Servers](https://www.flowhunt.io/blog/why-top-engineers-are-ditching-mcp-servers/)
- [Reducing MCP token usage by 100x](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2)

### API Integration
- [Google Cloud - API Design Best Practices](https://cloud.google.com/blog/products/api-management/api-design-best-practices-common-pitfalls)
- [Accounting API Integration Guide 2025](https://www.openledger.com/fintech-saas-monetization-with-accounting-apis/accounting-api-for-developers-complete-integration-guide-2025)
- [API Integration Challenges and Solutions](https://www.connectpointz.com/blog/api-challenges-and-solutions)
