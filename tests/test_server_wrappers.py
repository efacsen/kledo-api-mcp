"""
Smoke tests for the 24 @mcp.tool() wrapper functions in server.py.

Each test calls the underlying tool function (tool.fn) directly with a mock
Context and AppContext, verifying that the dispatch logic routes to the
correct private implementation and returns a string result.

Pattern:
    ctx.request_context.lifespan_context = AppContext(client=mock_client)
    tool = mcp._tool_manager.get_tool("tool_name")
    result = await tool.fn(ctx=ctx, **kwargs)
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.kledo_client import KledoAPIClient
from src.server import AppContext, mcp

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    """A KledoAPIClient mock with common methods pre-configured."""
    client = Mock(spec=KledoAPIClient)
    client.get = AsyncMock(return_value={"data": {"data": []}})
    client.list_invoices = AsyncMock(return_value={"data": {"data": []}})
    client.list_products = AsyncMock(return_value={"data": {"data": []}})
    client.list_contacts = AsyncMock(return_value={"data": {"data": []}})
    return client


@pytest.fixture
def ctx(mock_client):
    """A minimal FastMCP Context mock wired to an AppContext."""
    app_ctx = AppContext(client=mock_client)
    c = MagicMock()
    c.request_context.lifespan_context = app_ctx
    c.report_progress = AsyncMock()
    return c


def get_tool_fn(tool_name: str):
    """Retrieve the underlying handler function for a registered tool."""
    tool = mcp._tool_manager.get_tool(tool_name)
    assert tool is not None, f"Tool {tool_name!r} not registered"
    return tool.fn


# ---------------------------------------------------------------------------
# Financial wrappers (3)
# ---------------------------------------------------------------------------


class TestFinancialWrappers:
    @pytest.mark.asyncio
    async def test_financial_activity_returns_str(self, ctx):
        fn = get_tool_fn("financial_activity")
        with patch("src.tools.financial._activity_team_report", AsyncMock(return_value="ok")):
            result = await fn(ctx=ctx)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_financial_summary_sales_default(self, ctx):
        fn = get_tool_fn("financial_summary")
        with patch("src.tools.financial._sales_summary", AsyncMock(return_value="sales")) as m:
            result = await fn(type="sales", group_by="customer", ctx=ctx)
        assert result == "sales"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_financial_summary_purchase(self, ctx):
        fn = get_tool_fn("financial_summary")
        with patch(
            "src.tools.financial._purchase_summary", AsyncMock(return_value="purchases")
        ) as m:
            result = await fn(type="purchase", ctx=ctx)
        assert result == "purchases"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_financial_summary_sales_rep(self, ctx):
        fn = get_tool_fn("financial_summary")
        with patch("src.tools.financial._sales_by_person", AsyncMock(return_value="by_rep")) as m:
            result = await fn(type="sales", group_by="sales_rep", ctx=ctx)
        assert result == "by_rep"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_financial_balances_returns_str(self, ctx):
        fn = get_tool_fn("financial_balances")
        with patch("src.tools.financial._bank_balances", AsyncMock(return_value="balances")):
            result = await fn(ctx=ctx)
        assert result == "balances"


# ---------------------------------------------------------------------------
# Invoice wrappers (3)
# ---------------------------------------------------------------------------


class TestInvoiceWrappers:
    @pytest.mark.asyncio
    async def test_invoice_list_sales(self, ctx):
        fn = get_tool_fn("invoice_list")
        with patch("src.tools.invoices._list_sales_invoices", AsyncMock(return_value="sales")) as m:
            result = await fn(type="sales", ctx=ctx)
        assert result == "sales"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invoice_list_purchase(self, ctx):
        fn = get_tool_fn("invoice_list")
        with patch(
            "src.tools.invoices._list_purchase_invoices", AsyncMock(return_value="purchases")
        ) as m:
            result = await fn(type="purchase", ctx=ctx)
        assert result == "purchases"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invoice_get(self, ctx):
        fn = get_tool_fn("invoice_get")
        with patch("src.tools.invoices._get_invoice_detail", AsyncMock(return_value="detail")) as m:
            result = await fn(invoice_id=42, ctx=ctx)
        assert result == "detail"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invoice_summarize_totals(self, ctx):
        fn = get_tool_fn("invoice_summarize")
        with patch("src.tools.invoices._get_invoice_totals", AsyncMock(return_value="totals")) as m:
            result = await fn(view="totals", ctx=ctx)
        assert result == "totals"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invoice_summarize_by_customer(self, ctx):
        fn = get_tool_fn("invoice_summarize")
        with patch(
            "src.tools.invoices._outstanding_by_customer", AsyncMock(return_value="by_cust")
        ) as m:
            result = await fn(view="by_customer", ctx=ctx)
        assert result == "by_cust"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invoice_summarize_by_vendor(self, ctx):
        fn = get_tool_fn("invoice_summarize")
        with patch(
            "src.tools.invoices._outstanding_by_vendor", AsyncMock(return_value="by_vendor")
        ) as m:
            result = await fn(view="by_vendor", ctx=ctx)
        assert result == "by_vendor"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Order wrappers (2)
# ---------------------------------------------------------------------------


class TestOrderWrappers:
    @pytest.mark.asyncio
    async def test_order_list_sales(self, ctx):
        fn = get_tool_fn("order_list")
        with patch("src.tools.orders._list_sales_orders", AsyncMock(return_value="orders")) as m:
            result = await fn(type="sales", ctx=ctx)
        assert result == "orders"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_order_list_purchase(self, ctx):
        fn = get_tool_fn("order_list")
        with patch("src.tools.orders._list_purchase_orders", AsyncMock(return_value="po")) as m:
            result = await fn(type="purchase", ctx=ctx)
        assert result == "po"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_order_get(self, ctx):
        fn = get_tool_fn("order_get")
        with patch("src.tools.orders._get_order", AsyncMock(return_value="order_detail")) as m:
            result = await fn(order_id=7, ctx=ctx)
        assert result == "order_detail"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Product wrappers (2)
# ---------------------------------------------------------------------------


class TestProductWrappers:
    @pytest.mark.asyncio
    async def test_product_list(self, ctx):
        fn = get_tool_fn("product_list")
        with patch("src.tools.products._list_products", AsyncMock(return_value="prods")) as m:
            result = await fn(ctx=ctx)
        assert result == "prods"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_product_get_by_id(self, ctx):
        fn = get_tool_fn("product_get")
        with patch(
            "src.tools.products._get_product_detail", AsyncMock(return_value="prod_detail")
        ) as m:
            result = await fn(product_id=5, ctx=ctx)
        assert result == "prod_detail"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_product_get_by_sku(self, ctx):
        fn = get_tool_fn("product_get")
        with patch("src.tools.products._search_by_sku", AsyncMock(return_value="sku_result")) as m:
            result = await fn(sku="CAT-001", ctx=ctx)
        assert result == "sku_result"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Contact wrappers (2)
# ---------------------------------------------------------------------------


class TestContactWrappers:
    @pytest.mark.asyncio
    async def test_contact_list(self, ctx):
        fn = get_tool_fn("contact_list")
        with patch("src.tools.contacts._list_contacts", AsyncMock(return_value="contacts")) as m:
            result = await fn(ctx=ctx)
        assert result == "contacts"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_contact_get_detail(self, ctx):
        fn = get_tool_fn("contact_get")
        with patch(
            "src.tools.contacts._get_contact_detail", AsyncMock(return_value="contact_detail")
        ) as m:
            result = await fn(contact_id=3, ctx=ctx)
        assert result == "contact_detail"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_contact_get_with_transactions(self, ctx):
        fn = get_tool_fn("contact_get")
        with patch(
            "src.tools.contacts._get_contact_transactions", AsyncMock(return_value="txns")
        ) as m:
            result = await fn(contact_id=3, include_transactions=True, ctx=ctx)
        assert result == "txns"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Delivery wrappers (2)
# ---------------------------------------------------------------------------


class TestDeliveryWrappers:
    @pytest.mark.asyncio
    async def test_delivery_list(self, ctx):
        fn = get_tool_fn("delivery_list")
        with patch(
            "src.tools.deliveries._list_deliveries", AsyncMock(return_value="deliveries")
        ) as m:
            result = await fn(ctx=ctx)
        assert result == "deliveries"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delivery_list_pending(self, ctx):
        fn = get_tool_fn("delivery_list")
        with patch(
            "src.tools.deliveries._get_pending_deliveries", AsyncMock(return_value="pending")
        ) as m:
            result = await fn(status="pending", ctx=ctx)
        assert result == "pending"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delivery_get(self, ctx):
        fn = get_tool_fn("delivery_get")
        with patch(
            "src.tools.deliveries._get_delivery_detail", AsyncMock(return_value="delivery_detail")
        ) as m:
            result = await fn(delivery_id=9, ctx=ctx)
        assert result == "delivery_detail"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Utility wrappers (2)
# ---------------------------------------------------------------------------


class TestUtilityWrappers:
    @pytest.mark.asyncio
    async def test_utility_cache_stats(self, ctx):
        fn = get_tool_fn("utility_cache")
        with patch("src.tools.utilities._get_cache_stats", AsyncMock(return_value="stats")) as m:
            result = await fn(action="stats", ctx=ctx)
        assert result == "stats"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_utility_cache_clear(self, ctx):
        fn = get_tool_fn("utility_cache")
        with patch("src.tools.utilities._clear_cache", AsyncMock(return_value="cleared")) as m:
            result = await fn(action="clear", ctx=ctx)
        assert result == "cleared"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_utility_test_connection(self, ctx):
        fn = get_tool_fn("utility_test_connection")
        with patch(
            "src.tools.utilities._test_connection", AsyncMock(return_value="connected")
        ) as m:
            result = await fn(ctx=ctx)
        assert result == "connected"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Sales analytics wrappers (2) — note reversed (client, args) parameter order
# ---------------------------------------------------------------------------


class TestSalesAnalyticsWrappers:
    @pytest.mark.asyncio
    async def test_sales_rep_report(self, ctx):
        fn = get_tool_fn("sales_rep_report")
        with patch(
            "src.tools.sales_analytics._sales_rep_revenue_report",
            AsyncMock(return_value="rep_report"),
        ) as m:
            result = await fn(period="2026-01", ctx=ctx)
        assert result == "rep_report"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sales_rep_list(self, ctx):
        fn = get_tool_fn("sales_rep_list")
        with patch(
            "src.tools.sales_analytics._sales_rep_list", AsyncMock(return_value="rep_list")
        ) as m:
            result = await fn(ctx=ctx)
        assert result == "rep_list"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Revenue wrappers (3)
# ---------------------------------------------------------------------------


class TestRevenueWrappers:
    @pytest.mark.asyncio
    async def test_revenue_summary_reports_progress(self, ctx):
        fn = get_tool_fn("revenue_summary")
        with patch("src.tools.revenue._revenue_summary", AsyncMock(return_value="rev_summary")):
            result = await fn(ctx=ctx)
        assert result == "rev_summary"
        # progress must be reported (0/3 start, 3/3 end)
        assert ctx.report_progress.await_count >= 2

    @pytest.mark.asyncio
    async def test_revenue_receivables_list(self, ctx):
        fn = get_tool_fn("revenue_receivables")
        with patch(
            "src.tools.revenue._outstanding_receivables", AsyncMock(return_value="receivables")
        ) as m:
            result = await fn(view="list", ctx=ctx)
        assert result == "receivables"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revenue_receivables_aging(self, ctx):
        fn = get_tool_fn("revenue_receivables")
        with patch(
            "src.tools.revenue._outstanding_aging_report", AsyncMock(return_value="aging")
        ) as m:
            result = await fn(view="aging", ctx=ctx)
        assert result == "aging"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revenue_receivables_concentration(self, ctx):
        fn = get_tool_fn("revenue_receivables")
        with patch(
            "src.tools.revenue._customer_concentration_report",
            AsyncMock(return_value="concentration"),
        ) as m:
            result = await fn(view="concentration", ctx=ctx)
        assert result == "concentration"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revenue_ranking_by_customer(self, ctx):
        fn = get_tool_fn("revenue_ranking")
        with patch(
            "src.tools.revenue._customer_revenue_ranking", AsyncMock(return_value="ranking")
        ) as m:
            result = await fn(group_by="customer", ctx=ctx)
        assert result == "ranking"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revenue_ranking_by_day(self, ctx):
        fn = get_tool_fn("revenue_ranking")
        with patch(
            "src.tools.revenue._revenue_daily_breakdown", AsyncMock(return_value="daily")
        ) as m:
            result = await fn(group_by="day", ctx=ctx)
        assert result == "daily"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Analytics wrappers (2)
# ---------------------------------------------------------------------------


class TestAnalyticsWrappers:
    @pytest.mark.asyncio
    async def test_analytics_compare_revenue_reports_progress(self, ctx):
        fn = get_tool_fn("analytics_compare")
        with patch(
            "src.tools.analytics._compare_revenue", AsyncMock(return_value="compared_revenue")
        ):
            result = await fn(metric="revenue", ctx=ctx)
        assert result == "compared_revenue"
        assert ctx.report_progress.await_count >= 2

    @pytest.mark.asyncio
    async def test_analytics_compare_outstanding(self, ctx):
        fn = get_tool_fn("analytics_compare")
        with patch(
            "src.tools.analytics._compare_outstanding",
            AsyncMock(return_value="compared_outstanding"),
        ) as m:
            result = await fn(metric="outstanding", ctx=ctx)
        assert result == "compared_outstanding"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analytics_targets_report(self, ctx):
        fn = get_tool_fn("analytics_targets")
        with patch(
            "src.tools.analytics._target_achievement", AsyncMock(return_value="achievement")
        ) as m:
            result = await fn(action="report", ctx=ctx)
        assert result == "achievement"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analytics_targets_underperformers(self, ctx):
        fn = get_tool_fn("analytics_targets")
        with patch(
            "src.tools.analytics._underperformers", AsyncMock(return_value="underperformers")
        ) as m:
            result = await fn(action="underperformers", ctx=ctx)
        assert result == "underperformers"
        m.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analytics_targets_set(self, ctx):
        fn = get_tool_fn("analytics_targets")
        with patch("src.tools.analytics._set_target", AsyncMock(return_value="set_ok")) as m:
            result = await fn(action="set", ctx=ctx)
        assert result == "set_ok"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Commission wrappers (1)
# ---------------------------------------------------------------------------


class TestCommissionWrappers:
    @pytest.mark.asyncio
    async def test_commission_report_all_reps_reports_progress(self, ctx):
        fn = get_tool_fn("commission_report")
        with patch("src.tools.commission._commission_report", AsyncMock(return_value="all_reps")):
            result = await fn(period="2026-01", ctx=ctx)
        assert result == "all_reps"
        assert ctx.report_progress.await_count >= 2

    @pytest.mark.asyncio
    async def test_commission_report_single_person(self, ctx):
        fn = get_tool_fn("commission_report")
        with patch(
            "src.tools.commission._commission_calculate", AsyncMock(return_value="single_rep")
        ) as m:
            result = await fn(period="2026-01", sales_person_name="Budi", ctx=ctx)
        assert result == "single_rep"
        m.assert_awaited_once()


# ---------------------------------------------------------------------------
# Error handling: ToolError is raised on exception
# ---------------------------------------------------------------------------


class TestWrapperErrorHandling:
    @pytest.mark.asyncio
    async def test_tool_error_raised_on_impl_exception(self, ctx):
        """Wrapper must convert implementation exceptions into ToolError."""
        from mcp.server.fastmcp.exceptions import ToolError

        fn = get_tool_fn("financial_balances")
        with patch(
            "src.tools.financial._bank_balances",
            AsyncMock(side_effect=RuntimeError("DB down")),
        ):
            with pytest.raises(ToolError):
                await fn(ctx=ctx)

    @pytest.mark.asyncio
    async def test_scrub_secrets_applied_in_tool_error(self, ctx):
        """ToolError message must not contain raw API key value."""
        import os
        from unittest.mock import patch as mpatch

        from mcp.server.fastmcp.exceptions import ToolError

        fn = get_tool_fn("financial_balances")
        with mpatch.dict(os.environ, {"KLEDO_API_KEY": "sk_supersecret_key_12345678"}):
            with patch(
                "src.tools.financial._bank_balances",
                AsyncMock(side_effect=RuntimeError("failed with sk_supersecret_key_12345678")),
            ):
                with pytest.raises(ToolError) as exc_info:
                    await fn(ctx=ctx)
                assert "sk_supersecret_key_12345678" not in str(exc_info.value)
