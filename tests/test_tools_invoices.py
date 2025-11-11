"""
Tests for invoice tools
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import invoices
from src.kledo_client import KledoAPIClient


class TestInvoiceTools:
    """Test suite for invoice tools."""

    def test_get_tools(self):
        """Test get_tools returns correct tool definitions."""
        tools = invoices.get_tools()

        assert len(tools) == 4
        assert all(isinstance(tool, Tool) for tool in tools)

        tool_names = [tool.name for tool in tools]
        assert "invoice_list_sales" in tool_names
        assert "invoice_get_detail" in tool_names
        assert "invoice_get_totals" in tool_names
        assert "invoice_list_purchase" in tool_names

    def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = invoices.get_tools()

        for tool in tools:
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_handle_tool_invoice_list_sales(self, mock_invoice_list_response):
        """Test handle_tool routes invoice_list_sales correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices.handle_tool(
            "invoice_list_sales",
            {"per_page": 50},
            mock_client
        )

        assert isinstance(result, str)
        assert "Sales Invoices" in result
        assert "INV-001" in result
        assert "Customer A" in result
        mock_client.list_invoices.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_invoice_get_detail(self, mock_invoice_detail_response):
        """Test handle_tool routes invoice_get_detail correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(return_value=mock_invoice_detail_response)

        result = await invoices.handle_tool(
            "invoice_get_detail",
            {"invoice_id": 1},
            mock_client
        )

        assert isinstance(result, str)
        assert "Invoice Details" in result
        assert "INV-001" in result
        assert "Product A" in result
        mock_client.get_invoice_detail.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_handle_tool_invoice_get_totals(self):
        """Test handle_tool routes invoice_get_totals correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_response = {
            "data": {
                "data": {
                    "total_count": 10,
                    "total_amount": 10000,
                    "paid_amount": 7000,
                    "outstanding_amount": 3000,
                    "overdue_amount": 500
                }
            }
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await invoices.handle_tool(
            "invoice_get_totals",
            {},
            mock_client
        )

        assert isinstance(result, str)
        assert "Invoice Totals Summary" in result
        assert "10" in result  # total_count
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_invoice_list_purchase(self):
        """Test handle_tool routes invoice_list_purchase correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_response = {
            "data": {
                "data": [
                    {
                        "trans_number": "BILL-001",
                        "contact_name": "Vendor A",
                        "trans_date": "2024-01-15",
                        "grand_total": 5000,
                        "status_name": "Paid"
                    }
                ]
            }
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await invoices.handle_tool(
            "invoice_list_purchase",
            {},
            mock_client
        )

        assert isinstance(result, str)
        assert "Purchase Invoices" in result
        assert "BILL-001" in result
        assert "Vendor A" in result

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await invoices.handle_tool(
            "unknown_tool",
            {},
            mock_client
        )

        assert "Unknown invoice tool" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_no_results(self):
        """Test listing sales invoices with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value={"data": {"data": []}})

        result = await invoices.handle_tool(
            "invoice_list_sales",
            {},
            mock_client
        )

        assert "No invoices found" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_with_date_range(self, mock_invoice_list_response):
        """Test listing sales invoices with date range."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices.handle_tool(
            "invoice_list_sales",
            {
                "date_from": "2024-01-01",
                "date_to": "2024-01-31"
            },
            mock_client
        )

        assert isinstance(result, str)
        mock_client.list_invoices.assert_called_once()
        call_kwargs = mock_client.list_invoices.call_args.kwargs
        assert call_kwargs["date_from"] == "2024-01-01"
        assert call_kwargs["date_to"] == "2024-01-31"

    @pytest.mark.asyncio
    async def test_list_sales_invoices_calculates_totals(self, mock_invoice_list_response):
        """Test that list_sales_invoices calculates correct totals."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices.handle_tool(
            "invoice_list_sales",
            {},
            mock_client
        )

        # Total amount should be 1000 + 2000 = 3000
        # Total paid should be 500 + 2000 = 2500
        # Outstanding should be 500
        assert "3,000" in result or "3000" in result
        assert "2,500" in result or "2500" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_missing_id(self):
        """Test get_invoice_detail without invoice_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await invoices.handle_tool(
            "invoice_get_detail",
            {},
            mock_client
        )

        assert "invoice_id is required" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_not_found(self):
        """Test get_invoice_detail with non-existent invoice."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(return_value={"data": {}})

        result = await invoices.handle_tool(
            "invoice_get_detail",
            {"invoice_id": 999},
            mock_client
        )

        assert "not found" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_with_line_items(self, mock_invoice_detail_response):
        """Test get_invoice_detail displays line items."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(return_value=mock_invoice_detail_response)

        result = await invoices.handle_tool(
            "invoice_get_detail",
            {"invoice_id": 1},
            mock_client
        )

        assert "Line Items" in result
        assert "Product A" in result
        assert "Product B" in result
        assert "Qty" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_error_handling(self):
        """Test error handling in list_sales_invoices."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(side_effect=Exception("API Error"))

        result = await invoices.handle_tool(
            "invoice_list_sales",
            {},
            mock_client
        )

        assert "Error fetching sales invoices" in result
        assert "API Error" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_error_handling(self):
        """Test error handling in get_invoice_detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(side_effect=Exception("Network Error"))

        result = await invoices.handle_tool(
            "invoice_get_detail",
            {"invoice_id": 1},
            mock_client
        )

        assert "Error fetching invoice details" in result
        assert "Network Error" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_with_filters(self, mock_invoice_list_response):
        """Test listing sales invoices with multiple filters."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices.handle_tool(
            "invoice_list_sales",
            {
                "search": "INV-001",
                "contact_id": 5,
                "status_id": 2,
                "per_page": 20
            },
            mock_client
        )

        assert isinstance(result, str)
        mock_client.list_invoices.assert_called_once()
        call_kwargs = mock_client.list_invoices.call_args.kwargs
        assert call_kwargs["search"] == "INV-001"
        assert call_kwargs["contact_id"] == 5
        assert call_kwargs["status_id"] == 2
        assert call_kwargs["per_page"] == 20

    @pytest.mark.asyncio
    async def test_list_sales_invoices_limits_display(self):
        """Test that list_sales_invoices limits display to 20 items."""
        mock_client = Mock(spec=KledoAPIClient)

        # Create response with 25 invoices
        invoices_data = [
            {
                "trans_number": f"INV-{i:03d}",
                "contact_name": f"Customer {i}",
                "trans_date": "2024-01-15",
                "grand_total": 1000,
                "amount_paid": 500,
                "status_name": "Pending"
            }
            for i in range(1, 26)
        ]

        mock_client.list_invoices = AsyncMock(
            return_value={"data": {"data": invoices_data}}
        )

        result = await invoices.handle_tool(
            "invoice_list_sales",
            {},
            mock_client
        )

        # Should show message about additional invoices
        assert "and 5 more invoices" in result
