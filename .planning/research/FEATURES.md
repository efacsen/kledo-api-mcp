# Feature Landscape: MCP Server API Mapping

**Domain:** MCP Server with comprehensive API mapping for AI agents
**Researched:** 2026-01-21
**Confidence:** MEDIUM-HIGH (based on current MCP ecosystem best practices)

## Executive Summary

This research identifies what features make MCP servers AI-friendly and what comprehensive API mapping solutions should include. The existing Kledo MCP server has solid foundational tools but lacks critical discoverability and documentation features that would help AI agents understand and navigate the available data effectively.

The key insight from 2025-2026 MCP ecosystem research: **AI agents don't just need tools - they need to understand WHEN to use each tool and HOW tools relate to each other.** The gap is not in API coverage, but in API discoverability and contextual guidance.

---

## Table Stakes

Features AI agents expect from MCP tools. Missing these = agents struggle to use the server effectively.

### 1. Clear, Actionable Tool Descriptions
| Aspect | Requirement | Current State | Gap |
|--------|-------------|---------------|-----|
| **What it does** | 1-2 sentences explaining the action | Partial - basic descriptions exist | Need "when to use" context |
| **When to use** | Conditions for selecting this tool | Missing | Critical gap |
| **What it returns** | Output format/structure | Missing | Should document return shape |

**Complexity:** Low
**Why Table Stakes:** LLMs select tools based on descriptions. Per [Merge.dev research](https://www.merge.dev/blog/mcp-tool-description), "AI agents may not read the entire tool description, especially if it's several sentences" - descriptions must front-load critical selection criteria.

### 2. Consistent Parameter Documentation
| Aspect | Requirement | Current State | Gap |
|--------|-------------|---------------|-----|
| **Type annotations** | Clear types for all parameters | Present | Adequate |
| **Valid values** | Enum values, ranges documented | Partial | Status IDs, type IDs need docs |
| **Examples** | Sample valid inputs | Missing | Need example values |
| **Defaults** | What happens if omitted | Partial | Some documented, some not |

**Complexity:** Low
**Why Table Stakes:** Per [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25), input schemas are mandatory and should guide proper tool usage. Agents generate fewer errors when schemas clearly document valid inputs.

### 3. Structured Error Responses
| Aspect | Requirement | Current State | Gap |
|--------|-------------|---------------|-----|
| **Error format** | Consistent error structure | Partial | Mix of formats |
| **Actionable messages** | What went wrong AND how to fix | Missing | Just "Error: X" |
| **Error codes** | Machine-parseable error types | Missing | No classification |

**Complexity:** Low-Medium
**Why Table Stakes:** Per MCP spec, "Tool errors should be reported within the result object, not as MCP protocol-level errors. This allows the LLM to see and potentially handle the error." Agents need to understand failures to recover.

### 4. Tool Naming Conventions
| Aspect | Requirement | Current State | Gap |
|--------|-------------|---------------|-----|
| **Predictable patterns** | `{domain}_{action}_{target}` | Present | Good pattern exists |
| **Verb-first actions** | `list`, `get`, `create`, etc. | Present | Adequate |
| **Consistent casing** | snake_case throughout | Present | Good |

**Complexity:** Low (already met)
**Why Table Stakes:** Per [MCP best practices](https://gofastmcp.com/servers/tools), "Best practices suggest using snake_case or camelCase strings that clearly categorize the action."

### 5. Flat, Simple Schemas
| Aspect | Requirement | Current State | Gap |
|--------|-------------|---------------|-----|
| **Minimal nesting** | Avoid deep object hierarchies | Present | Good |
| **Standard types** | string, integer, boolean, array | Present | Good |
| **No complex validation** | Avoid oneOf/allOf complexity | Present | Good |

**Complexity:** Low (already met)
**Why Table Stakes:** Per [FastMCP docs](https://gofastmcp.com/servers/tools), "Deeply nested structures increase the token count and cognitive load for the LLM, which can lead to higher latency or parsing errors."

---

## Differentiators

Features that would make this MCP server stand out. Not expected, but significantly improve AI agent effectiveness.

### 1. API Discovery Tool (Tool Search)
**What:** A meta-tool that helps agents find the right tool for their task.
**Value Proposition:** Agents don't need to load all tool definitions upfront; they can discover relevant tools on-demand.

**Example Implementation:**
```
tool: discover_tools
input: { "query": "how to find customer payment history" }
output: [
  { "tool": "contact_get_transactions", "relevance": "high", "reason": "Shows payment history for a contact" },
  { "tool": "invoice_list_sales", "relevance": "medium", "reason": "Can filter by customer" }
]
```

**Complexity:** Medium
**Why Differentiating:** Per [Anthropic engineering](https://www.anthropic.com/engineering/advanced-tool-use), Tool Search Tool showed "85% reduction in token usage while maintaining access to your full tool library" and improved Opus 4.5 accuracy from 79.5% to 88.1%.

### 2. Data Relationship Map (MCP Resource)
**What:** An MCP Resource exposing the entity relationship model.
**Value Proposition:** Agents understand how data connects - "a Contact has Invoices, Invoices have Line Items with Products."

**Example Implementation:**
```
resource: kledo://schema/relationships
content: {
  "contact": {
    "has_many": ["invoices", "orders", "transactions"],
    "description": "Customer or vendor in the system"
  },
  "invoice": {
    "belongs_to": ["contact"],
    "has_many": ["line_items", "payments"],
    "related_to": ["products via line_items"]
  }
}
```

**Complexity:** Medium
**Why Differentiating:** Per [a16z deep dive on MCP](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/), "documentation will become a critical piece of MCP infrastructure" as agents must understand tool capabilities and data relationships to chain operations effectively.

### 3. Workflow Suggestions (Prompt Templates)
**What:** MCP Prompts that guide multi-step workflows.
**Value Proposition:** Agents get pre-defined sequences for common tasks instead of figuring out tool chains.

**Example Implementation:**
```
prompt: monthly_financial_review
description: "Generate a monthly financial review report"
steps:
  1. Call financial_bank_balances for current cash position
  2. Call financial_sales_summary for revenue
  3. Call financial_purchase_summary for expenses
  4. Call invoice_get_totals for AR status
  5. Synthesize into report
```

**Complexity:** Low-Medium
**Why Differentiating:** Per [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25), Prompts are "predefined templates or instructions that help shape the AI's behavior for specific tasks."

### 4. Semantic Tool Grouping
**What:** Metadata categorizing tools by business domain and use case.
**Value Proposition:** Agents understand tool organization without reading all descriptions.

**Example Implementation:**
```
categories:
  "accounts_receivable": [invoice_list_sales, invoice_get_detail, invoice_get_totals]
  "accounts_payable": [invoice_list_purchase]
  "cash_management": [financial_bank_balances]
  "customer_management": [contact_list, contact_get_detail, contact_get_transactions]
  "inventory": [product_list, product_get_detail, product_get_stock]
```

**Complexity:** Low
**Why Differentiating:** Reduces cognitive load for agents choosing tools. Per [Pragmatic Engineer on MCP](https://newsletter.pragmaticengineer.com/p/mcp), "Tool definitions and results can sometimes consume 50,000+ tokens before an agent reads a request."

### 5. llms.txt Documentation File
**What:** Machine-readable documentation index at `/llms.txt` or embedded in server.
**Value Proposition:** Standard format for AI systems to understand API capabilities.

**Example Implementation:**
```markdown
# Kledo MCP Server

> Financial management API for Indonesian businesses. Provides access to invoices, contacts, products, orders, and financial reports.

## Core Capabilities
- [Tools Reference](/docs/tools.md): Complete tool documentation
- [Data Model](/docs/schema.md): Entity relationships
- [Workflows](/docs/workflows.md): Common task sequences

## Quick Start
- Get customer list: `contact_list`
- Get sales data: `invoice_list_sales`
- Get financial summary: `financial_sales_summary`
```

**Complexity:** Low
**Why Differentiating:** Per [llmstxt.org](https://llmstxt.org/), this is the emerging standard for AI-optimized documentation. Adopted by Anthropic, Cloudflare, Vercel, and thousands of documentation sites via Mintlify.

### 6. Context-Aware Pagination
**What:** Tools that return pagination metadata with navigation hints.
**Value Proposition:** Agents know when there's more data and how to get it without guessing.

**Example Implementation:**
```
output: {
  "data": [...],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 234,
    "has_more": true,
    "next_action": "Call with page=2 to get next results"
  }
}
```

**Complexity:** Low
**Why Differentiating:** Per [Merge.dev](https://www.merge.dev/blog/mcp-tool-description), authentication, pagination, and filtering details "should be addressed in the tool's schema" to guide agent behavior.

### 7. Business Context Annotations
**What:** Descriptions that include domain-specific context.
**Value Proposition:** Agents understand business meaning, not just technical function.

**Example:**
```
Current: "List sales invoices with optional filtering"
Enhanced: "List sales invoices (customer bills). Use this to find what customers owe you.
          For vendor bills you've received, use invoice_list_purchase instead."
```

**Complexity:** Low
**Why Differentiating:** Helps agents make correct tool selections in domain-specific contexts. Especially valuable for accounting/financial terminology that may confuse general-purpose LLMs.

---

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

### 1. One Tool Per API Endpoint
**What:** Creating a separate MCP tool for every REST endpoint.
**Why Avoid:** Creates tool sprawl. Per [MarkTechPost best practices](https://www.marktechpost.com/2025/07/23/7-mcp-server-best-practices-for-scalable-ai-integrations-in-2025/), "Avoid mapping every API endpoint to a new MCP tool. Instead, group related tasks and design higher-level functions."
**What to Do Instead:** Create higher-level tools that combine related operations. The current pattern of `invoice_list_sales` + `invoice_get_detail` is appropriate.

### 2. Write Operations Without Confirmation
**What:** Tools that create/update/delete data without explicit acknowledgment.
**Why Avoid:** Per [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25), "Hosts MUST obtain explicit user consent before invoking any tool." Write operations should have extra safeguards.
**What to Do Instead:** If adding write tools, require confirmation parameters or implement as two-step (preview + commit).

### 3. Overly Verbose Tool Descriptions
**What:** Multi-paragraph descriptions explaining every edge case.
**Why Avoid:** Per [Merge.dev](https://www.merge.dev/blog/mcp-tool-description), "AI agents may not read the entire tool description." Long descriptions waste tokens and may be truncated.
**What to Do Instead:** Keep descriptions to 1-2 sentences. Move detailed documentation to separate resources or schema descriptions.

### 4. Complex Nested Input Schemas
**What:** Deeply nested JSON objects as tool inputs.
**Why Avoid:** Per [FastMCP docs](https://gofastmcp.com/servers/tools), "Deeply nested structures increase the token count and cognitive load for the LLM."
**What to Do Instead:** Keep schemas flat. If complex input is needed, split into multiple tools.

### 5. Raw API Passthrough
**What:** Tools that just forward raw API responses without formatting.
**Why Avoid:** Raw JSON responses require agents to parse and interpret domain-specific structures. Increases token usage and error potential.
**What to Do Instead:** Format responses as human-readable summaries (the current approach with markdown formatting is good).

### 6. Inconsistent Date/Time Handling
**What:** Different date formats across different tools.
**Why Avoid:** Agents will pass wrong formats, causing errors.
**What to Do Instead:** Standardize on ISO 8601 (YYYY-MM-DD) and document clearly. The current `parse_date_range` helper with shortcuts is good.

### 7. Tool Names Without Domain Prefix
**What:** Generic tool names like `list`, `get_detail`, `search`.
**Why Avoid:** Collisions when agents use multiple MCP servers. Unclear which domain a tool belongs to.
**What to Do Instead:** Always prefix with domain: `contact_list`, `invoice_get_detail` (current pattern is correct).

---

## Feature Dependencies

Which features depend on others.

```
Core (existing, adequate):
  - Tool naming conventions
  - Flat schemas
  - Basic descriptions

Foundation (build first):
  Enhanced tool descriptions
      |
      v
  Structured error responses
      |
      v
  Parameter documentation (valid values, examples)

Discovery Layer (build second, depends on Foundation):
  Semantic tool grouping
      |
      +---> API Discovery Tool (search_tools)
      |
      +---> Data Relationship Map (MCP Resource)

Guidance Layer (build third, depends on Discovery):
  Workflow Suggestions (MCP Prompts)
      |
      v
  llms.txt Documentation File

Enhancement Layer (independent, can build anytime):
  - Context-aware pagination
  - Business context annotations
```

**Recommended Build Order:**
1. **Phase 1:** Enhanced descriptions, parameter docs, error handling (Foundation)
2. **Phase 2:** Tool grouping, discovery tool, relationship map (Discovery)
3. **Phase 3:** Workflow prompts, llms.txt (Guidance)
4. **Parallel:** Pagination, business context annotations (can be done anytime)

---

## Complexity Assessment

| Feature | Complexity | Effort Estimate | Value |
|---------|------------|-----------------|-------|
| Enhanced tool descriptions | Low | 1-2 days | High |
| Parameter documentation | Low | 1 day | High |
| Structured error responses | Low-Medium | 1-2 days | Medium |
| API Discovery Tool | Medium | 3-5 days | Very High |
| Data Relationship Map | Medium | 2-3 days | High |
| Workflow Suggestions | Low-Medium | 2-3 days | High |
| Semantic tool grouping | Low | 1 day | Medium |
| llms.txt file | Low | 0.5 days | Medium |
| Context-aware pagination | Low | 1 day | Medium |
| Business context annotations | Low | 1 day | Medium |

**Total Estimated Effort:** 15-22 days for full implementation

**Recommended MVP (5-7 days):**
1. Enhanced tool descriptions with "when to use"
2. Complete parameter documentation
3. Semantic tool grouping metadata
4. Basic llms.txt file

---

## Sources

### Official Specifications
- [MCP Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [llms.txt Specification](https://llmstxt.org/)
- [FastMCP Tools Documentation](https://gofastmcp.com/servers/tools)

### Best Practices Guides
- [MCP Tool Descriptions Best Practices - Merge.dev](https://www.merge.dev/blog/mcp-tool-description)
- [A Deep Dive into MCP - a16z](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/)
- [How to Optimize Docs for LLMs - Redocly](https://redocly.com/blog/optimizations-to-make-to-your-docs-for-llms)

### Anthropic Engineering
- [Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)
- [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

### Industry Analysis
- [MCP Protocol: A New AI Dev Tools Building Block - Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/mcp)
- [AI Documentation Trends 2025 - Mintlify](https://www.mintlify.com/blog/ai-documentation-trends-whats-changing-in-2025)
- [Top LLM Frameworks for AI Agents 2026 - Second Talent](https://www.secondtalent.com/resources/top-llm-frameworks-for-building-ai-agents/)

---

## Confidence Notes

| Finding | Confidence | Basis |
|---------|------------|-------|
| Tool description best practices | HIGH | MCP spec + multiple authoritative sources |
| Schema design patterns | HIGH | Official FastMCP documentation |
| Discovery tool value | HIGH | Anthropic engineering data (85% token reduction) |
| llms.txt adoption | MEDIUM-HIGH | Growing standard, not yet universal |
| Workflow prompts value | MEDIUM | Logical extension of MCP primitives, less proven |
| Complexity estimates | MEDIUM | Based on codebase review, may vary |
