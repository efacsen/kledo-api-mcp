"""
Smoke tests for tool modules: analytics, commission, revenue, sales_analytics.
Post-migration: no get_tools/handle_tool — tests use private functions directly.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from src.tools import analytics, commission, revenue, sales_analytics
from src.tools.commission import calculate_tiered_commission
from src.kledo_client import KledoAPIClient

# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


class TestAnalyticsTools:
    """Smoke tests for analytics tool module."""

    def test_no_legacy_interface(self):
        assert not hasattr(analytics, "get_tools"), "analytics still exports get_tools()"
        assert not hasattr(analytics, "handle_tool"), "analytics still exports handle_tool()"

    def test_handler_functions_are_callable(self):
        assert callable(analytics._compare_revenue)
        assert asyncio.iscoroutinefunction(analytics._compare_revenue)
        assert callable(analytics._compare_outstanding)
        assert asyncio.iscoroutinefunction(analytics._compare_outstanding)
        assert callable(analytics._target_achievement)
        assert asyncio.iscoroutinefunction(analytics._target_achievement)
        assert callable(analytics._underperformers)
        assert asyncio.iscoroutinefunction(analytics._underperformers)
        assert callable(analytics._set_target)
        assert asyncio.iscoroutinefunction(analytics._set_target)

    def test_resolve_period_is_callable(self):
        assert callable(analytics._resolve_period)

    @pytest.mark.asyncio
    async def test_compare_revenue_missing_period(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await analytics._compare_revenue({}, mock_client)
        assert isinstance(result, str)
        assert "period" in result.lower() or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_compare_outstanding_missing_period(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await analytics._compare_outstanding({}, mock_client)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Commission
# ---------------------------------------------------------------------------


class TestCommissionTools:
    """Smoke tests for commission tool module."""

    def test_no_legacy_interface(self):
        assert not hasattr(commission, "get_tools"), "commission still exports get_tools()"
        assert not hasattr(commission, "handle_tool"), "commission still exports handle_tool()"

    def test_handler_functions_are_callable(self):
        assert callable(commission._commission_calculate)
        assert asyncio.iscoroutinefunction(commission._commission_calculate)
        assert callable(commission._commission_report)
        assert asyncio.iscoroutinefunction(commission._commission_report)

    def test_calculate_tiered_commission_still_public(self):
        assert callable(commission.calculate_tiered_commission)

    @pytest.mark.asyncio
    async def test_commission_report_missing_period(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await commission._commission_report({}, mock_client)
        assert isinstance(result, str)
        assert "period" in result.lower() or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_commission_calculate_missing_period(self):
        mock_client = Mock(spec=KledoAPIClient)
        result = await commission._commission_calculate({}, mock_client)
        assert isinstance(result, str)
        assert "period" in result.lower() or "error" in result.lower()


# ---------------------------------------------------------------------------
# Revenue
# ---------------------------------------------------------------------------


class TestRevenueTools:
    """Smoke tests for revenue tool module."""

    def test_no_legacy_interface(self):
        assert not hasattr(revenue, "get_tools"), "revenue still exports get_tools()"
        assert not hasattr(revenue, "handle_tool"), "revenue still exports handle_tool()"

    def test_handler_functions_are_callable(self):
        assert callable(revenue._revenue_summary)
        assert asyncio.iscoroutinefunction(revenue._revenue_summary)
        assert callable(revenue._outstanding_receivables)
        assert asyncio.iscoroutinefunction(revenue._outstanding_receivables)
        assert callable(revenue._customer_revenue_ranking)
        assert asyncio.iscoroutinefunction(revenue._customer_revenue_ranking)

    @pytest.mark.asyncio
    async def test_revenue_summary_error_handling(self):
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(side_effect=Exception("Network error"))
        result = await revenue._revenue_summary({"date_from": "2026-01-01"}, mock_client)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_outstanding_receivables_error_handling(self):
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(side_effect=Exception("Network error"))
        result = await revenue._outstanding_receivables({"view": "list"}, mock_client)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Sales Analytics
# ---------------------------------------------------------------------------


class TestSalesAnalyticsTools:
    """Smoke tests for sales_analytics tool module."""

    def test_no_legacy_interface(self):
        assert not hasattr(
            sales_analytics, "get_tools"
        ), "sales_analytics still exports get_tools()"
        assert not hasattr(
            sales_analytics, "handle_tool"
        ), "sales_analytics still exports handle_tool()"

    def test_handler_functions_are_callable(self):
        assert callable(sales_analytics._sales_rep_revenue_report)
        assert asyncio.iscoroutinefunction(sales_analytics._sales_rep_revenue_report)
        assert callable(sales_analytics._sales_rep_list)
        assert asyncio.iscoroutinefunction(sales_analytics._sales_rep_list)

    @pytest.mark.asyncio
    async def test_sales_rep_list_error_propagates(self):
        # _sales_rep_list does not swallow network errors — exceptions propagate
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
        with pytest.raises(Exception, match="Timeout"):
            await sales_analytics._sales_rep_list(mock_client, {})


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
