"""
Tests for invoice tools — post-migration (no get_tools/handle_tool).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from src.tools import invoices
from src.kledo_client import KledoAPIClient


class TestInvoiceHandlerFunctions:
    """Verify private handler functions exist and are async."""

    def test_handler_functions_are_callable(self):
        assert callable(invoices._list_sales_invoices)
        assert asyncio.iscoroutinefunction(invoices._list_sales_invoices)
        assert callable(invoices._get_invoice_detail)
        assert asyncio.iscoroutinefunction(invoices._get_invoice_detail)
        assert callable(invoices._get_invoice_totals)
        assert asyncio.iscoroutinefunction(invoices._get_invoice_totals)
        assert callable(invoices._list_purchase_invoices)
        assert asyncio.iscoroutinefunction(invoices._list_purchase_invoices)

    def test_no_legacy_interface(self):
        assert not hasattr(invoices, "get_tools"), "invoices still exports get_tools()"
        assert not hasattr(invoices, "handle_tool"), "invoices still exports handle_tool()"


class TestInvoiceTools:
    """Test suite for invoice private functions."""

    @pytest.mark.asyncio
    async def test_list_sales_invoices(self, mock_invoice_list_response):
        """Test _list_sales_invoices returns formatted list."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices._list_sales_invoices({"per_page": 50}, mock_client)

        assert isinstance(result, str)
        assert "Sales Invoices" in result
        assert "INV/" in result
        assert "Name" in result
        mock_client.list_invoices.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_invoice_detail(self, mock_invoice_detail_response):
        """Test _get_invoice_detail returns formatted detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(return_value=mock_invoice_detail_response)

        result = await invoices._get_invoice_detail({"invoice_id": 1}, mock_client)

        assert isinstance(result, str)
        assert "Invoice Details" in result
        assert "INV/" in result
        assert "Name" in result
        mock_client.get_invoice_detail.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_invoice_totals(self):
        """Test _get_invoice_totals returns summary totals."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_response = {"data": {"amount_after_tax": 10000, "due": 3000, "paid": 7000}}
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await invoices._get_invoice_totals({}, mock_client)

        assert isinstance(result, str)
        assert "Invoice Totals Summary" in result
        assert "10,000" in result or "10000" in result
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_purchase_invoices(self):
        """Test _list_purchase_invoices returns purchase list."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_response = {
            "data": {
                "data": [
                    {
                        "ref_number": "BILL-001",
                        "contact": {"name": "Vendor A"},
                        "trans_date": "2024-01-15",
                        "amount_after_tax": 5000,
                        "due": 0.0,
                        "status_id": 3,
                    }
                ]
            }
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await invoices._list_purchase_invoices({}, mock_client)

        assert isinstance(result, str)
        assert "Purchase Invoices" in result
        assert "BILL-001" in result
        assert "Vendor A" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_no_results(self):
        """Test listing sales invoices with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value={"data": {"data": []}})

        result = await invoices._list_sales_invoices({}, mock_client)

        assert "No invoices found" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_with_date_range(self, mock_invoice_list_response):
        """Test listing sales invoices with date range."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices._list_sales_invoices(
            {"date_from": "2024-01-01", "date_to": "2024-01-31"}, mock_client
        )

        assert isinstance(result, str)
        mock_client.list_invoices.assert_called_once()
        call_kwargs = mock_client.list_invoices.call_args.kwargs
        assert call_kwargs["date_from"] == "2024-01-01"
        assert call_kwargs["date_to"] == "2024-01-31"

    @pytest.mark.asyncio
    async def test_list_sales_invoices_calculates_totals(self, mock_invoice_list_response):
        """Test that _list_sales_invoices calculates correct totals."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices._list_sales_invoices({}, mock_client)

        assert "Penjualan Neto" in result or "Net Sales" in result
        assert "Rp" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_missing_id(self):
        """Test _get_invoice_detail without invoice_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await invoices._get_invoice_detail({}, mock_client)

        assert "invoice_id is required" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_not_found(self):
        """Test _get_invoice_detail with non-existent invoice."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(return_value={"data": {}})

        result = await invoices._get_invoice_detail({"invoice_id": 999}, mock_client)

        assert "not found" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_with_line_items(self, mock_invoice_detail_response):
        """Test _get_invoice_detail displays line items."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(return_value=mock_invoice_detail_response)

        result = await invoices._get_invoice_detail({"invoice_id": 1}, mock_client)

        assert "Line Items" in result
        assert "Qty" in result
        assert "Name" in result or "Qty" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_error_handling(self):
        """Test error handling in _list_sales_invoices."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(side_effect=Exception("API Error"))

        result = await invoices._list_sales_invoices({}, mock_client)

        assert "Error fetching sales invoices" in result
        assert "API Error" in result

    @pytest.mark.asyncio
    async def test_get_invoice_detail_error_handling(self):
        """Test error handling in _get_invoice_detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get_invoice_detail = AsyncMock(side_effect=Exception("Network Error"))

        result = await invoices._get_invoice_detail({"invoice_id": 1}, mock_client)

        assert "Error fetching invoice details" in result
        assert "Network Error" in result

    @pytest.mark.asyncio
    async def test_list_sales_invoices_with_filters(self, mock_invoice_list_response):
        """Test listing with multiple filters passes them to API."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_invoices = AsyncMock(return_value=mock_invoice_list_response)

        result = await invoices._list_sales_invoices(
            {"search": "INV-001", "contact_id": 5, "status_id": 2, "per_page": 20}, mock_client
        )

        assert isinstance(result, str)
        mock_client.list_invoices.assert_called()
        call_kwargs = mock_client.list_invoices.call_args.kwargs
        assert call_kwargs["contact_id"] == 5
        assert call_kwargs["status_id"] == 2

    @pytest.mark.asyncio
    async def test_list_sales_invoices_limits_display(self):
        """Test that _list_sales_invoices limits display to 20 items."""
        mock_client = Mock(spec=KledoAPIClient)

        invoices_data = [
            {
                "ref_number": f"INV/24/JAN/{i:05d}",
                "contact": {"name": f"Customer {i}"},
                "trans_date": "2024-01-15",
                "amount_after_tax": 1000,
                "due": 500,
                "status_id": 2,
            }
            for i in range(1, 26)
        ]

        mock_client.list_invoices = AsyncMock(return_value={"data": {"data": invoices_data}})

        result = await invoices._list_sales_invoices({}, mock_client)

        assert "and 5 more invoices" in result
