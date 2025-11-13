"""
Tests for financial tools
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import financial
from src.kledo_client import KledoAPIClient


class TestFinancialTools:
    """Test suite for financial tools."""

    def test_get_tools(self):
        """Test get_tools returns correct tool definitions."""
        tools = financial.get_tools()

        assert len(tools) == 4
        assert all(isinstance(tool, Tool) for tool in tools)

        tool_names = [tool.name for tool in tools]
        assert "financial_activity_team_report" in tool_names
        assert "financial_sales_summary" in tool_names
        assert "financial_purchase_summary" in tool_names
        assert "financial_bank_balances" in tool_names

    def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = financial.get_tools()

        for tool in tools:
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_handle_tool_activity_team_report(self):
        """Test handle_tool routes activity_team_report correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_activity_team_report = AsyncMock(return_value={
            "data": {
                "data": [
                    {"user_name": "John Doe", "action": "Created Invoice", "count": 5},
                    {"user_name": "Jane Smith", "action": "Updated Order", "count": 3}
                ]
            }
        })

        result = await financial.handle_tool(
            "financial_activity_team_report",
            {"date_from": "2024-10", "date_to": "2024-10"},
            mock_client
        )

        assert isinstance(result, str)
        assert "Team Activity Report" in result
        assert "John Doe" in result
        mock_client.get_activity_team_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_sales_summary(self):
        """Test handle_tool routes sales_summary correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {"contact_name": "ABC Corp", "total": 100000, "count": 5},
                    {"contact_name": "XYZ Inc", "total": 75000, "count": 3}
                ]
            }
        })

        result = await financial.handle_tool(
            "financial_sales_summary",
            {"date_from": "2024-10-01", "date_to": "2024-10-31"},
            mock_client
        )

        assert isinstance(result, str)
        assert "Sales Summary by Customer" in result
        assert "ABC Corp" in result
        assert "175,000" in result or "175000" in result  # Total sales

    @pytest.mark.asyncio
    async def test_handle_tool_purchase_summary(self):
        """Test handle_tool routes purchase_summary correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {"contact_name": "Vendor A", "total": 50000, "count": 2},
                    {"contact_name": "Vendor B", "total": 30000, "count": 1}
                ]
            }
        })

        result = await financial.handle_tool(
            "financial_purchase_summary",
            {"date_from": "last_month"},
            mock_client
        )

        assert isinstance(result, str)
        assert "Purchase Summary by Vendor" in result
        assert "Vendor A" in result

    @pytest.mark.asyncio
    async def test_handle_tool_bank_balances(self):
        """Test handle_tool routes bank_balances correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {"name": "BCA - Main", "balance": 50000000, "currency": "IDR"},
                    {"name": "Mandiri - Operations", "balance": 25000000, "currency": "IDR"}
                ]
            }
        })

        result = await financial.handle_tool(
            "financial_bank_balances",
            {},
            mock_client
        )

        assert isinstance(result, str)
        assert "Bank Account Balances" in result
        assert "BCA - Main" in result
        assert "Total Balance" in result

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await financial.handle_tool(
            "financial_unknown_tool",
            {},
            mock_client
        )

        assert "Unknown financial tool" in result

    @pytest.mark.asyncio
    async def test_activity_team_report_no_data(self):
        """Test activity report with no data."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_activity_team_report = AsyncMock(return_value={
            "data": {"data": []}
        })

        result = await financial.handle_tool(
            "financial_activity_team_report",
            {},
            mock_client
        )

        assert "No activity data found" in result

    @pytest.mark.asyncio
    async def test_sales_summary_date_shortcuts(self):
        """Test sales summary with date shortcuts."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": [
                {"contact_name": "Test Customer", "total": 10000, "count": 1}
            ]}
        })

        result = await financial.handle_tool(
            "financial_sales_summary",
            {"date_from": "this_month"},
            mock_client
        )

        assert isinstance(result, str)
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_bank_balances_empty(self):
        """Test bank balances with no accounts."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": []}
        })

        result = await financial.handle_tool(
            "financial_bank_balances",
            {},
            mock_client
        )

        assert "No bank accounts found" in result

    @pytest.mark.asyncio
    async def test_sales_summary_error_handling(self):
        """Test error handling in sales summary."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API Error"))

        result = await financial.handle_tool(
            "financial_sales_summary",
            {"date_from": "2024-10-01"},
            mock_client
        )

        assert "Error fetching sales summary" in result
        assert "API Error" in result

    @pytest.mark.asyncio
    async def test_purchase_summary_with_contact_filter(self):
        """Test purchase summary filtered by contact."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": [
                {"contact_name": "Specific Vendor", "total": 25000, "count": 5}
            ]}
        })

        result = await financial.handle_tool(
            "financial_purchase_summary",
            {"date_from": "2024-10-01", "date_to": "2024-10-31", "contact_id": 123},
            mock_client
        )

        assert "Purchase Summary by Vendor" in result
        assert "Specific Vendor" in result

    @pytest.mark.asyncio
    async def test_activity_team_report_limits_display(self):
        """Test that activity report limits displayed items."""
        mock_data = [{"user_name": f"User {i}", "action": "Action", "count": i}
                     for i in range(30)]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_activity_team_report = AsyncMock(return_value={
            "data": {"data": mock_data}
        })

        result = await financial.handle_tool(
            "financial_activity_team_report",
            {},
            mock_client
        )

        assert "30 more activities" in result or "and 10 more" in result
