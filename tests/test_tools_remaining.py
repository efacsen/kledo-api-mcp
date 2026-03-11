"""
Smoke tests for tool modules that lack full test coverage:
analytics, commission, revenue, sales_analytics.

These tests verify tool registration (get_tools) and basic error handling
without requiring live API calls.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import analytics, commission, revenue, sales_analytics
from src.tools.commission import calculate_tiered_commission
from src.kledo_client import KledoAPIClient


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class TestAnalyticsTools:
    """Smoke tests for analytics tool module."""

    def test_get_tools_returns_tools(self):
        tools = analytics.get_tools()
        assert len(tools) == 2
        assert all(isinstance(t, Tool) for t in tools)

    def test_tool_names(self):
        names = {t.name for t in analytics.get_tools()}
        assert "analytics_compare" in names
        assert "analytics_targets" in names

    def test_tool_schemas(self):
        for tool in analytics.get_tools():
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await analytics.handle_tool("analytics_unknown", {}, mock_client)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_handle_tool_error_handling(self):
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))
        # Call any analytics tool — should return an error string, not raise
        result = await analytics.handle_tool("sales_by_product", {}, mock_client)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Commission
# ---------------------------------------------------------------------------

class TestCommissionTools:
    """Smoke tests for commission tool module."""

    def test_get_tools_returns_tools(self):
        tools = commission.get_tools()
        assert len(tools) == 1
        assert all(isinstance(t, Tool) for t in tools)

    def test_tool_schemas(self):
        for tool in commission.get_tools():
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await commission.handle_tool("commission_unknown", {}, mock_client)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_handle_tool_error_handling(self):
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(side_effect=Exception("API error"))
        tool_name = commission.get_tools()[0].name
        result = await commission.handle_tool(tool_name, {}, mock_client)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Revenue
# ---------------------------------------------------------------------------

class TestRevenueTools:
    """Smoke tests for revenue tool module."""

    def test_get_tools_returns_tools(self):
        tools = revenue.get_tools()
        assert len(tools) == 3
        assert all(isinstance(t, Tool) for t in tools)

    def test_tool_names(self):
        names = {t.name for t in revenue.get_tools()}
        assert "revenue_summary" in names
        assert "revenue_ranking" in names

    def test_tool_schemas(self):
        for tool in revenue.get_tools():
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await revenue.handle_tool("revenue_unknown", {}, mock_client)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_handle_tool_error_handling(self):
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(side_effect=Exception("Network error"))
        result = await revenue.handle_tool("revenue_summary", {}, mock_client)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Sales Analytics
# ---------------------------------------------------------------------------

class TestSalesAnalyticsTools:
    """Smoke tests for sales_analytics tool module."""

    def test_get_tools_returns_tools(self):
        tools = sales_analytics.get_tools()
        assert len(tools) == 2
        assert all(isinstance(t, Tool) for t in tools)

    def test_tool_schemas(self):
        for tool in sales_analytics.get_tools():
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await sales_analytics.handle_tool("sales_analytics_unknown", {}, mock_client)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_handle_tool_error_handling(self):
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
        tool_name = sales_analytics.get_tools()[0].name
        result = await sales_analytics.handle_tool(tool_name, {}, mock_client)
        assert isinstance(result, str)

# ---------------------------------------------------------------------------
# Commission pure function
# ---------------------------------------------------------------------------

class TestCalculateTieredCommission:
    """Unit tests for the pure calculate_tiered_commission function."""

    def test_flat_rate_override(self):
        result = calculate_tiered_commission(200_000_000, flat_rate=0.03)
        assert result["total_commission"] == pytest.approx(6_000_000)
        assert result["effective_rate"] == pytest.approx(0.03)
        assert len(result["breakdown"]) == 1
        assert result["breakdown"][0]["range"] == "Flat rate"

    def test_tiered_first_bracket_only(self):
        # 50M — all in tier 1 (1%)
        result = calculate_tiered_commission(50_000_000)
        assert result["total_commission"] == pytest.approx(500_000)
        assert result["effective_rate"] == pytest.approx(0.01)

    def test_tiered_spans_two_brackets(self):
        # 150M: 100M@1% + 50M@2% = 1M + 1M = 2M
        result = calculate_tiered_commission(150_000_000)
        assert result["total_commission"] == pytest.approx(2_000_000)
        assert len(result["breakdown"]) == 2

    def test_tiered_spans_all_brackets(self):
        # 400M: 100M@1% + 200M@2% + 100M@3% = 1M + 4M + 3M = 8M
        result = calculate_tiered_commission(400_000_000)
        assert result["total_commission"] == pytest.approx(8_000_000)
        assert len(result["breakdown"]) == 3

    def test_zero_revenue(self):
        result = calculate_tiered_commission(0)
        assert result["total_commission"] == 0
        assert result["effective_rate"] == 0.0

    def test_custom_tiers(self):
        custom = [{"threshold": 0, "rate": 0.05}]
        result = calculate_tiered_commission(100_000, tiers=custom)
        assert result["total_commission"] == pytest.approx(5_000)
        assert result["effective_rate"] == pytest.approx(0.05)
