"""
Tests for order tools — post-migration (no get_tools/handle_tool).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from src.tools import orders
from src.kledo_client import KledoAPIClient


class TestOrderHandlerFunctions:
    """Verify private handler functions exist and are async."""

    def test_handler_functions_are_callable(self):
        assert callable(orders._list_orders)
        assert asyncio.iscoroutinefunction(orders._list_orders)
        assert callable(orders._get_order)
        assert asyncio.iscoroutinefunction(orders._get_order)

    def test_no_legacy_interface(self):
        assert not hasattr(orders, "get_tools"), "orders still exports get_tools()"
        assert not hasattr(orders, "handle_tool"), "orders still exports handle_tool()"


class TestOrderTools:
    """Test suite for order private functions."""

    @pytest.mark.asyncio
    async def test_list_sales_orders(self):
        """Test _list_orders with type=sales returns sales orders."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "ref_number": "SO-001",
                            "contact": {"name": "Customer A"},
                            "trans_date": "2024-10-15",
                            "amount_after_tax": 50000,
                            "status_id": 5,
                        },
                        {
                            "ref_number": "SO-002",
                            "contact": {"name": "Customer B"},
                            "trans_date": "2024-10-16",
                            "amount_after_tax": 75000,
                            "status_id": 7,
                        },
                    ]
                }
            }
        )

        result = await orders._list_orders({"type": "sales", "search": "test"}, mock_client)

        assert isinstance(result, str)
        assert "Sales Orders" in result
        assert "SO-001" in result
        assert "Customer A" in result

    @pytest.mark.asyncio
    async def test_get_order(self):
        """Test _get_order returns order detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": {
                        "ref_number": "SO-123",
                        "contact": {"name": "ABC Corp"},
                        "trans_date": "2024-10-20",
                        "status_id": 7,
                        "subtotal": 100000,
                        "amount_after_tax": 110000,
                        "detail": [
                            {"desc": "Product A", "qty": 5, "price": 20000, "amount": 100000}
                        ],
                    }
                }
            }
        )

        result = await orders._get_order({"order_id": 123}, mock_client)

        assert isinstance(result, str)
        assert "Sales Order Details" in result
        assert "SO-123" in result
        assert "Product A" in result

    @pytest.mark.asyncio
    async def test_list_purchase_orders(self):
        """Test _list_orders with type=purchase returns purchase orders."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "ref_number": "PO-001",
                            "contact": {"name": "Vendor X"},
                            "trans_date": "2024-10-10",
                            "amount_after_tax": 25000,
                            "status_id": 5,
                        }
                    ]
                }
            }
        )

        result = await orders._list_orders({"type": "purchase"}, mock_client)

        assert "Purchase Orders" in result
        assert "PO-001" in result

    @pytest.mark.asyncio
    async def test_list_orders_missing_type(self):
        """Test _list_orders requires type parameter."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await orders._list_orders({}, mock_client)

        assert "type parameter is required" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_no_results(self):
        """Test listing sales orders with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await orders._list_orders({"type": "sales"}, mock_client)

        assert "No sales orders found" in result

    @pytest.mark.asyncio
    async def test_get_order_missing_id(self):
        """Test getting order detail without order_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await orders._get_order({}, mock_client)

        assert "order_id is required" in result

    @pytest.mark.asyncio
    async def test_get_order_not_found(self):
        """Test getting order detail for non-existent order."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": None}})

        result = await orders._get_order({"order_id": 999}, mock_client)

        assert "Order #999 not found" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_with_date_range(self):
        """Test listing sales orders with date range."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "ref_number": "SO-100",
                            "contact": {"name": "Test"},
                            "trans_date": "2024-10-15",
                            "amount_after_tax": 10000,
                            "status_id": 5,
                        }
                    ]
                }
            }
        )

        result = await orders._list_orders(
            {"type": "sales", "date_from": "2024-10-01", "date_to": "2024-10-31"}, mock_client
        )

        assert "SO-100" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_calculates_total(self):
        """Test that list calculates total amount."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "ref_number": "SO-1",
                            "contact": {"name": "A"},
                            "trans_date": "2024-10-01",
                            "amount_after_tax": 50000,
                            "status_id": 5,
                        },
                        {
                            "ref_number": "SO-2",
                            "contact": {"name": "B"},
                            "trans_date": "2024-10-02",
                            "amount_after_tax": 75000,
                            "status_id": 7,
                        },
                    ]
                }
            }
        )

        result = await orders._list_orders({"type": "sales"}, mock_client)

        assert "125,000" in result or "125000" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_limits_display(self):
        """Test that listing limits display to 20 orders."""
        mock_orders = [
            {
                "ref_number": f"SO-{i:03d}",
                "contact": {"name": f"Customer {i}"},
                "trans_date": "2024-10-01",
                "amount_after_tax": 10000,
                "status_id": 5,
            }
            for i in range(25)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": mock_orders}})

        result = await orders._list_orders({"type": "sales"}, mock_client)

        assert "5 more orders" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_error_handling(self):
        """Test error handling in list sales orders."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await orders._list_orders({"type": "sales"}, mock_client)

        assert "Error fetching sales orders" in result

    @pytest.mark.asyncio
    async def test_get_order_error_handling(self):
        """Test error handling in get order detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await orders._get_order({"order_id": 123}, mock_client)

        assert "Error fetching order details" in result
