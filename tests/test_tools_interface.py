"""
Contract tests for Phase 4 Tool Interface Migration.

These tests define the target state. Tests in TestModuleInterfaceContracts
are RED against the current codebase (get_tools/handle_tool still exist)
and turn GREEN as modules are migrated.

Tests in TestToolAnnotations are RED until Plan 04-03 adds ToolAnnotations.

Tests in TestProgressReporting are RED until Plan 04-02 wires ctx: Context
into the three progress-reporting handlers.

Run during migration: pytest tests/test_tools_interface.py --no-cov -v
"""

import inspect

import pytest
from mcp.server.fastmcp import Context

from src.server import mcp
from src.tools import (
    analytics,
    commission,
    contacts,
    deliveries,
    financial,
    invoices,
    orders,
    products,
    revenue,
    sales_analytics,
    utilities,
)

EXPECTED_PREFIXES = [
    "financial_",
    "invoice_",
    "order_",
    "product_",
    "contact_",
    "delivery_",
    "utility_",
    "sales_rep_",
    "revenue_",
    "analytics_",
    "commission_",
]


class TestModuleInterfaceContracts:
    """IFACE-01: Verifies old interface is gone from all 11 modules.

    These tests are RED against the current codebase — every module still
    exports get_tools() and handle_tool(). They turn GREEN module-by-module
    as Phase 4 Wave 1 migrates each file to @mcp.tool() decorators.
    """

    @pytest.mark.parametrize(
        "module",
        [
            analytics,
            commission,
            contacts,
            deliveries,
            financial,
            invoices,
            orders,
            products,
            revenue,
            sales_analytics,
            utilities,
        ],
    )
    def test_module_has_no_get_tools(self, module):
        assert not hasattr(
            module, "get_tools"
        ), f"{module.__name__} still exports get_tools() — migration incomplete"

    @pytest.mark.parametrize(
        "module",
        [
            analytics,
            commission,
            contacts,
            deliveries,
            financial,
            invoices,
            orders,
            products,
            revenue,
            sales_analytics,
            utilities,
        ],
    )
    def test_module_has_no_handle_tool(self, module):
        assert not hasattr(
            module, "handle_tool"
        ), f"{module.__name__} still exports handle_tool() — migration incomplete"


class TestToolRegistrationCount:
    """IFACE-01: All 24 tools remain registered after removing the bridge.

    These tests pass NOW (bridge registers 24 tools) and must continue to
    pass after migration — they act as a regression guard.
    """

    async def test_mcp_has_exactly_24_tools(self):
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert len(names) == 24, f"Expected 24 tools, got {len(names)}: {sorted(names)}"

    async def test_all_category_prefixes_present(self):
        tools = await mcp.list_tools()
        names = [t.name for t in tools]
        for prefix in EXPECTED_PREFIXES:
            assert any(
                n.startswith(prefix) for n in names
            ), f"No tool found for prefix {prefix!r}. Present: {sorted(names)}"


class TestToolAnnotations:
    """IFACE-02: All tools carry readOnlyHint=True and openWorldHint=True.

    These tests are RED until Plan 04-03 adds ToolAnnotations to every
    @mcp.tool() registration. The bridge (current) uses mcp.add_tool without
    annotations, so both tests fail now.
    """

    async def test_all_tools_have_read_only_hint(self):
        tools = await mcp.list_tools()
        failures = [
            t.name for t in tools if not (t.annotations and t.annotations.readOnlyHint is True)
        ]
        assert not failures, f"Tools missing readOnlyHint=True: {failures}"

    async def test_all_tools_have_open_world_hint(self):
        tools = await mcp.list_tools()
        failures = [
            t.name for t in tools if not (t.annotations and t.annotations.openWorldHint is True)
        ]
        assert not failures, f"Tools missing openWorldHint=True: {failures}"


class TestProgressReporting:
    """IFACE-03: Three tools accept ctx: Context for progress reporting.

    These tests are RED until Plan 04-02 migrates commission_report,
    analytics_compare, and revenue_summary to @mcp.tool() with a
    ctx: Context parameter. The bridge wrappers do not expose ctx.
    """

    def _get_handler(self, tool_name: str):
        """Find the registered tool handler by name from mcp._tool_manager."""
        tool_manager = mcp._tool_manager
        if hasattr(tool_manager, "tools"):
            tool = tool_manager.tools.get(tool_name)
            if tool and hasattr(tool, "fn"):
                return tool.fn
        return None

    @pytest.mark.parametrize(
        "tool_name",
        [
            "commission_report",
            "analytics_compare",
            "revenue_summary",
        ],
    )
    def test_progress_tool_has_ctx_parameter(self, tool_name: str):
        """Handler for {tool_name} must have a parameter annotated as Context."""
        handler = self._get_handler(tool_name)
        assert handler is not None, f"Tool {tool_name!r} not found in mcp — is it registered?"
        sig = inspect.signature(handler)
        ctx_params = [(name, p) for name, p in sig.parameters.items() if p.annotation is Context]
        assert ctx_params, (
            f"Handler for {tool_name!r} has no parameter annotated as Context. "
            f"Parameters: {dict(sig.parameters)}"
        )
