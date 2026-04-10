"""
Tests for financial tools — post-migration (no get_tools/handle_tool).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from src.tools import financial
from src.kledo_client import KledoAPIClient


class TestFinancialHandlerFunctions:
    """Verify private handler functions exist and are async."""

    def test_handler_functions_are_callable(self):
        assert callable(financial._activity_team_report)
        assert asyncio.iscoroutinefunction(financial._activity_team_report)
        assert callable(financial._sales_summary)
        assert asyncio.iscoroutinefunction(financial._sales_summary)
        assert callable(financial._purchase_summary)
        assert asyncio.iscoroutinefunction(financial._purchase_summary)
        assert callable(financial._bank_balances)
        assert asyncio.iscoroutinefunction(financial._bank_balances)
        assert callable(financial._fetch_all_invoices)
        assert asyncio.iscoroutinefunction(financial._fetch_all_invoices)

    def test_no_legacy_interface(self):
        assert not hasattr(financial, "get_tools"), "financial still exports get_tools()"
        assert not hasattr(financial, "handle_tool"), "financial still exports handle_tool()"


class TestFinancialTools:
    """Test suite for financial private functions."""

    @pytest.mark.asyncio
    async def test_activity_team_report(self):
        """Test _activity_team_report returns formatted report."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_activity_team_report = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {"user_name": "John Doe", "action": "Created Invoice", "count": 5},
                        {"user_name": "Jane Smith", "action": "Updated Order", "count": 3},
                    ]
                }
            }
        )

        result = await financial._activity_team_report(
            {"date_from": "2024-10", "date_to": "2024-10"}, mock_client
        )

        assert isinstance(result, str)
        assert "Team Activity Report" in result
        assert "John Doe" in result
        mock_client.get_activity_team_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_sales_summary(self):
        """Test _sales_summary returns customer-grouped sales."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "contact": {"name": "ABC Corp"},
                            "amount_after_tax": 100000,
                            "status_id": 3,
                        },
                        {"contact": {"name": "XYZ Inc"}, "amount_after_tax": 75000, "status_id": 3},
                    ],
                    "current_page": 1,
                    "last_page": 1,
                }
            }
        )

        result = await financial._sales_summary(
            {"date_from": "2024-10-01", "date_to": "2024-10-31"}, mock_client
        )

        assert isinstance(result, str)
        assert "Sales Summary by Customer" in result
        assert "ABC Corp" in result

    @pytest.mark.asyncio
    async def test_purchase_summary(self):
        """Test _purchase_summary returns vendor-grouped purchases."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "contact": {"name": "Vendor A"},
                            "amount_after_tax": 50000,
                            "status_id": 3,
                        },
                        {
                            "contact": {"name": "Vendor B"},
                            "amount_after_tax": 30000,
                            "status_id": 1,
                        },
                    ],
                    "current_page": 1,
                    "last_page": 1,
                }
            }
        )

        result = await financial._purchase_summary({"date_from": "2024-10-01"}, mock_client)

        assert isinstance(result, str)
        assert "Purchase Summary by Vendor" in result
        assert "Vendor A" in result

    @pytest.mark.asyncio
    async def test_bank_balances(self):
        """Test _bank_balances returns account balances."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {"name": "BCA - Main", "balance": 50000000, "currency": "IDR"},
                        {"name": "Mandiri - Operations", "balance": 25000000, "currency": "IDR"},
                    ]
                }
            }
        )

        result = await financial._bank_balances({}, mock_client)

        assert isinstance(result, str)
        assert "Bank Account Balances" in result
        assert "BCA - Main" in result
        assert "Total Balance" in result

    @pytest.mark.asyncio
    async def test_activity_team_report_no_data(self):
        """Test activity report with no data."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_activity_team_report = AsyncMock(return_value={"data": {"data": []}})

        result = await financial._activity_team_report({}, mock_client)

        assert "No activity data found" in result

    @pytest.mark.asyncio
    async def test_bank_balances_empty(self):
        """Test bank balances with no accounts."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await financial._bank_balances({}, mock_client)

        assert "No bank accounts found" in result

    @pytest.mark.asyncio
    async def test_sales_summary_error_handling(self):
        """Test error handling in sales summary."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API Error"))

        result = await financial._sales_summary({"date_from": "2024-10-01"}, mock_client)

        assert "Error fetching sales summary" in result
        assert "API Error" in result

    @pytest.mark.asyncio
    async def test_purchase_summary_with_contact_filter(self):
        """Test purchase summary returns vendor data."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "contact": {"name": "Specific Vendor"},
                            "amount_after_tax": 25000,
                            "status_id": 3,
                        }
                    ],
                    "current_page": 1,
                    "last_page": 1,
                }
            }
        )

        result = await financial._purchase_summary(
            {"date_from": "2024-10-01", "date_to": "2024-10-31"}, mock_client
        )

        assert "Purchase Summary by Vendor" in result
        assert "Specific Vendor" in result

    @pytest.mark.asyncio
    async def test_activity_team_report_limits_display(self):
        """Test that activity report limits displayed items."""
        mock_data = [{"user_name": f"User {i}", "action": "Action", "count": i} for i in range(30)]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_activity_team_report = AsyncMock(return_value={"data": {"data": mock_data}})

        result = await financial._activity_team_report({}, mock_client)

        assert "more activities" in result
