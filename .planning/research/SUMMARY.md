# Project Research Summary

**Project:** Kledo API MCP Server - Documentation Enhancement
**Domain:** API Documentation, Entity Mapping, and AI Agent Tools
**Researched:** 2026-01-21
**Confidence:** HIGH

## Executive Summary

This project enhances an existing Kledo MCP server (30+ tools for Indonesian accounting API) by adding comprehensive API documentation, entity relationship mapping, and smart tool routing. The current implementation is well-architected with clean separation of concerns (Transport -> Auth -> Client -> Cache -> Tools), and the research confirms that new capabilities should integrate at specific extension points rather than requiring rewrites.

The recommended approach builds three new layers on top of the existing foundation: (1) Entity Registry - a YAML-based catalog of API entities and their relationships, (2) Documentation Layer - enriched tool descriptions with business context and examples, and (3) Routing Layer - simple keyword-to-tool mapping for natural language queries. The technology stack leverages MkDocs for static documentation generation, erdantic for entity relationship diagrams, and standard library keyword matching for routing - avoiding over-engineered solutions like vector search for the 30-50 tool scale.

Key risks center on token bloat from verbose tool descriptions, tool selection confusion from overlapping descriptions, and accounting domain synonym coverage. These are mitigated by establishing strict token budgets (under 150 tokens per tool), building a domain synonym dictionary early, and creating explicit disambiguation in tool descriptions. The sequential build order (Entity Registry -> Documentation -> Routing) ensures each phase has proper foundations while avoiding tight coupling between layers.

## Key Findings

### Recommended Stack

The existing Python MCP stack (MCP SDK, Pydantic, httpx, PyYAML) is solid and requires no changes. New capabilities add focused libraries for documentation generation and diagram creation without architectural modifications.

**Core technologies:**
- **MkDocs + Material theme**: Static documentation generation - simpler than Sphinx, Markdown-native, excellent for AI-readable API docs
- **mkdocstrings[python]**: Auto-documentation from docstrings - generates API reference pages automatically from Python code
- **erdantic**: Entity relationship diagrams from Pydantic models - native Pydantic V2 support, outputs both Graphviz and Mermaid formats
- **Jinja2**: Template-based documentation generation - consistent formatting from YAML/Python definitions
- **Standard library (difflib)**: Keyword fuzzy matching - no dependencies, sufficient for 30-50 tools without vector search overhead

**Why NOT vector search:** The project has 30-50 tools with distinct purposes. Simple keyword matching with synonym expansion is transparent, maintainable, fast, and sufficient for this scale. Vector search adds embedding model dependencies, latency, and infrastructure complexity without proportional value.

### Expected Features

AI agents need more than just tools - they need to understand WHEN to use each tool and HOW tools relate to each other. The gap is not in API coverage (40 of 323 endpoints already mapped), but in API discoverability and contextual guidance.

**Must have (table stakes):**
- **Enhanced tool descriptions**: "When to use" context, not just "what it does" - LLMs select tools based on descriptions and may not read entire text
- **Complete parameter documentation**: Valid values, examples, defaults - reduces agent errors when schemas clearly document valid inputs
- **Structured error responses**: Consistent format with actionable messages - agents need to understand failures to recover
- **Consistent naming patterns**: Already present (`{domain}_{action}_{target}`) - predictable tool names reduce hallucination

**Should have (competitive differentiators):**
- **API Discovery Tool**: Meta-tool for finding relevant tools - reduces token usage while maintaining access to full library (Anthropic research: 85% token reduction, 79.5% -> 88.1% accuracy improvement)
- **Data Relationship Map**: MCP Resource exposing entity relationships - helps agents understand how data connects (e.g., "Contact has Invoices")
- **Workflow Suggestions**: MCP Prompts for common multi-step tasks - pre-defined sequences reduce agent planning overhead
- **Semantic tool grouping**: Metadata categorizing tools by business domain - reduces cognitive load for tool selection
- **llms.txt documentation**: Machine-readable documentation index - emerging standard adopted by Anthropic, Cloudflare, Vercel

**Defer (v2+):**
- Write operations (require confirmation flows and safety validation)
- Comprehensive API coverage (all 323 endpoints - current 40 endpoints prioritize high-value use cases)
- Real-time API documentation sync (Kledo API changes infrequently, manual review is sufficient)

### Architecture Approach

The enhancement adds three new layers that integrate with existing architecture at specific extension points. The current data flow (Agent -> Server -> Tools -> Client -> Auth -> API) gains: Entity Registry (standalone data files consumed by tools), Documentation Layer (enriches tool definitions at server level), and Routing Layer (pre-processes requests before tool dispatch).

**Major components:**
1. **Entity Registry** (Phase 1) - YAML-based entity definitions, relationship mapping, field catalog with types/enums - provides single source of truth for all Kledo API entities
2. **Documentation Layer** (Phase 2) - Tool enrichment system, business context provider, example generator - wraps tools at server level in `list_tools()` to return enhanced metadata
3. **Routing Layer** (Phase 3) - Keyword extraction, intent resolution, tool suggestion - hooks into server at `call_tool()` level for natural language query mapping

**Build order rationale:** Entity Registry first (all other components depend on entity definitions), Documentation second (uses Entity Registry to enrich existing tools), Routing third (uses both Entity Registry and Documentation for full context).

### Critical Pitfalls

1. **Tool Description Token Bloat** - Verbose descriptions waste 10,000-20,000 tokens before conversation starts. Keep each tool under 150 tokens. Use self-documenting parameter names. Put examples in separate docs, not inline. Review with token counter during development.

2. **Overlapping Tool Functionality** - Multiple tools with similar descriptions cause 15-30% incorrect selection rate. Audit all descriptions for keyword overlap. Each tool needs unique trigger phrases. Use explicit disambiguation: "Use this for X, NOT for Y." Create tool selection matrix during design.

3. **Keyword Routing Fails on Domain Synonyms** - Accounting has many synonyms (invoice/bill, customer/client, revenue/sales). Build synonym map during design. Include common synonyms in descriptions concisely. Test routing with synonym variations. Document trigger phrases including synonyms.

4. **Parameter Validation Trusts LLM Input** - LLMs may hallucinate IDs, use wrong formats, pass incorrect types. Validate all inputs before API calls. Provide clear error messages for invalid inputs. Use enums where possible. Never assume LLM follows parameter instructions.

5. **Over-Engineering for 30 Tools** - Vector search, dynamic tool loading, custom query languages are overkill. Keep all tools loaded. Focus on token-efficient descriptions. Trust LLM for natural language to parameter translation. Prioritize high-value endpoints, not completeness.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation - Entity Registry & Enhanced Descriptions
**Rationale:** Establish single source of truth for entities and set quality bar for tool descriptions before expanding coverage. All subsequent phases depend on entity definitions and need consistent description patterns.

**Delivers:**
- Entity schema format and loader utility
- Core entity definitions (Invoice, Contact, Product, Order, Account)
- Relationship mapping between entities
- Enhanced tool descriptions with "when to use" context
- Complete parameter documentation with examples
- Domain synonym dictionary

**Addresses:** Table stakes features (enhanced descriptions, parameter docs) and establishes anti-token-bloat patterns

**Avoids:** Token bloat pitfall by setting 150-token budget upfront, overlapping functionality pitfall by creating tool disambiguation matrix, synonym coverage gaps by building synonym dictionary early

**Research Flag:** Standard patterns - entity definition formats are well-documented in Pydantic ecosystem, no deep research needed

### Phase 2: Discovery - Documentation Layer & Tool Grouping
**Rationale:** With entity definitions in place, add discoverability features that help agents understand tool relationships and make better selection decisions.

**Delivers:**
- Documentation enrichment system using Entity Registry
- Business context annotations for accounting domain
- Tool categorization by business domain (AR, AP, inventory, etc.)
- MkDocs-based static documentation site
- ERD diagrams from Pydantic models using erdantic

**Addresses:** Competitive differentiators (semantic grouping, relationship map) and documentation generation

**Uses:** MkDocs, mkdocstrings, erdantic, Jinja2 from stack recommendations

**Implements:** Documentation Layer component from architecture

**Avoids:** API wrapping mistakes by establishing "user-first" description style, missing negative guidance by documenting scope boundaries

**Research Flag:** Standard patterns - MkDocs and erdantic are well-documented with clear examples, no deep research needed

### Phase 3: Routing - Smart Tool Discovery
**Rationale:** Final layer adds intelligent routing using both Entity Registry and enriched documentation to map natural language queries to appropriate tools.

**Delivers:**
- Keyword extraction and matching system
- Intent resolver with fuzzy matching
- Tool suggestion with confidence scoring
- Parameter inference from queries
- Optional API Discovery Tool (meta-tool for finding tools)

**Addresses:** Competitive differentiators (API Discovery Tool) and smart routing capabilities

**Implements:** Routing Layer component from architecture

**Avoids:** Over-engineering pitfall by using stdlib keyword matching instead of vector search, inconsistent handling by standardizing on established patterns

**Research Flag:** Standard patterns - keyword matching and fuzzy string matching are well-understood, no deep research needed

### Phase 4 (Optional): Guidance - Workflows & AI-Optimized Docs
**Rationale:** After core capabilities are stable, add workflow suggestions for common multi-step tasks and finalize AI-optimized documentation.

**Delivers:**
- MCP Prompts for common workflows (e.g., monthly financial review)
- llms.txt documentation file
- Context-aware pagination metadata
- Workflow documentation and examples

**Addresses:** Remaining competitive differentiators (workflow suggestions, llms.txt)

**Avoids:** Over-complication by keeping workflow definitions simple YAML configurations

**Research Flag:** Standard patterns - MCP Prompts are part of official specification with clear examples

### Phase Ordering Rationale

- **Sequential dependencies:** Entity Registry has no dependencies. Documentation Layer needs Entity Registry for entity metadata. Routing Layer needs both Entity Registry (for entity context) and Documentation Layer (for enriched descriptions).

- **Risk mitigation:** Addressing token bloat and tool overlap in Phase 1 prevents compounding problems as more features are added. Synonym dictionary in Phase 1 ensures routing in Phase 3 has proper coverage from the start.

- **Value delivery:** Each phase delivers user-visible improvements. Phase 1 makes existing tools more usable. Phase 2 adds discoverability. Phase 3 adds intelligence. Phase 4 adds convenience.

- **Testing feedback loops:** Building sequentially allows testing and refinement of each layer before adding complexity. Entity definitions can be validated before documentation depends on them. Documentation quality can be assessed before routing uses it.

### Research Flags

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Entity definitions follow established Pydantic patterns, tool description best practices well-documented by Anthropic
- **Phase 2:** MkDocs and erdantic have extensive documentation and examples, straightforward integration
- **Phase 3:** Keyword matching is standard library functionality, no novel patterns needed
- **Phase 4:** MCP Prompts are part of official MCP specification with clear guidance

**No phases need deep research.** All components use well-established patterns with official documentation. The project avoids novel techniques that would require experimentation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via PyPI (Dec 2025 releases). MkDocs, erdantic, MCP SDK are mature, well-documented. Standard library approach for routing is proven. |
| Features | HIGH | MCP specification, Anthropic engineering research, and multiple authoritative sources align on best practices. Table stakes based on official MCP spec. Differentiators validated by Anthropic tool use research. |
| Architecture | HIGH | Integration points verified from existing codebase analysis. Build order follows clear dependency chain. No architectural rewrites needed. |
| Pitfalls | HIGH | Token bloat, overlapping tools, parameter validation documented by Anthropic. Synonym coverage specific to accounting domain. Over-engineering risks validated by scale analysis (30 tools << 100 threshold for advanced techniques). |

**Overall confidence:** HIGH

The research converges on clear recommendations across all dimensions. Technology choices are mature and well-supported. Feature priorities align with MCP ecosystem best practices. Architecture preserves existing structure while adding focused capabilities. Pitfalls are well-documented with clear prevention strategies.

### Gaps to Address

**Indonesian accounting terminology coverage:** Research focused on general accounting synonyms. May need validation of specific Indonesian business terms beyond the examples found (faktur, tagihan, piutang, saldo, kas). Address by: consulting with Indonesian accounting domain experts during Phase 1 synonym dictionary creation.

**Kledo API versioning:** Current tool implementations don't explicitly track Kledo API version compatibility. Address by: documenting supported API version in configuration and checking for breaking changes when Kledo updates.

**Error response standardization:** Research identified need for structured errors but existing codebase has mix of formats. Address by: auditing current error handling in Phase 1 and establishing consistent error schema.

**Tool coverage priorities:** 40 of 323 endpoints are mapped but rationale for selection not documented. Address by: creating endpoint priority matrix in Phase 1 based on usage patterns and user feedback.

## Sources

### Primary (HIGH confidence)

**Official specifications:**
- [MCP Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25) - Official MCP protocol and tool definitions
- [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture) - Official MCP documentation
- [Pydantic Fields Documentation](https://docs.pydantic.dev/latest/concepts/fields/) - Field metadata best practices

**Anthropic engineering:**
- [Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents) - Tool description best practices and token optimization
- [Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use) - Tool Search Tool research showing 85% token reduction, 79.5% -> 88.1% accuracy improvement

**Python packages:**
- [MkDocs Material PyPI](https://pypi.org/project/mkdocs-material/) - Version 9.7.1 verified (Dec 2025)
- [mkdocstrings PyPI](https://pypi.org/project/mkdocstrings-python/) - Version 2.0.1 verified (Dec 2025)
- [erdantic GitHub](https://github.com/drivendataorg/erdantic) - Version 1.2.0 verified (Sep 2025), Pydantic V2 support confirmed
- [mermaid-py PyPI](https://pypi.org/project/mermaid-py/) - Version 0.8.1 verified (Dec 2025)

### Secondary (MEDIUM confidence)

**Best practices guides:**
- [MCP Tool Descriptions - Merge.dev](https://www.merge.dev/blog/mcp-tool-description) - Tool description patterns and pitfalls
- [A Deep Dive into MCP - a16z](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/) - Documentation as critical infrastructure
- [FastMCP Tools Documentation](https://gofastmcp.com/servers/tools) - Schema design patterns and naming conventions
- [llms.txt Specification](https://llmstxt.org/) - Emerging standard for AI-optimized documentation

**Industry analysis:**
- [MCP Protocol - Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/mcp) - Token consumption patterns (50,000+ tokens before request)
- [Tool Function Calling Best Practices](https://medium.com/@laurentkubaski/tool-or-function-calling-best-practices-a5165a33d5f1) - Parameter validation patterns
- [Reducing MCP token usage by 100x](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2) - Dynamic toolset patterns and when they're needed

**Codebase analysis:**
- kledo-api-mcp existing implementation - server.py, kledo_client.py, tool modules verified

### Tertiary (LOW confidence)

**Context requiring validation:**
- Indonesian accounting terminology - limited research sources, needs domain expert review
- Kledo API stability assumptions - based on inference, not official documentation
- Tool selection accuracy improvements - extrapolated from Anthropic research on different tool counts

---
*Research completed: 2026-01-21*
*Ready for roadmap: yes*
