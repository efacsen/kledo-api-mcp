"""
Tests for order tools
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import orders
from src.kledo_client import KledoAPIClient


class TestOrderTools:
    """Test suite for order tools."""

    def test_get_tools(self):
        """Test get_tools returns correct tool definitions."""
        tools = orders.get_tools()

        assert len(tools) == 3
        assert all(isinstance(tool, Tool) for tool in tools)

        tool_names = [tool.name for tool in tools]
        assert "order_list_sales" in tool_names
        assert "order_get_detail" in tool_names
        assert "order_list_purchase" in tool_names

    def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = orders.get_tools()

        for tool in tools:
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_handle_tool_list_sales_orders(self):
        """Test handle_tool routes order_list_sales correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "trans_number": "SO-001",
                        "contact_name": "Customer A",
                        "trans_date": "2024-10-15",
                        "grand_total": 50000,
                        "status_name": "Pending"
                    },
                    {
                        "trans_number": "SO-002",
                        "contact_name": "Customer B",
                        "trans_date": "2024-10-16",
                        "grand_total": 75000,
                        "status_name": "Approved"
                    }
                ]
            }
        })

        result = await orders.handle_tool(
            "order_list_sales",
            {"search": "test"},
            mock_client
        )

        assert isinstance(result, str)
        assert "Sales Orders" in result
        assert "SO-001" in result
        assert "Customer A" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_order_detail(self):
        """Test handle_tool routes order_get_detail correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": {
                    "trans_number": "SO-123",
                    "contact_name": "ABC Corp",
                    "trans_date": "2024-10-20",
                    "status_name": "Approved",
                    "subtotal": 100000,
                    "grand_total": 110000,
                    "detail": [
                        {
                            "desc": "Product A",
                            "qty": 5,
                            "price": 20000,
                            "amount": 100000
                        }
                    ]
                }
            }
        })

        result = await orders.handle_tool(
            "order_get_detail",
            {"order_id": 123},
            mock_client
        )

        assert isinstance(result, str)
        assert "Sales Order Details" in result
        assert "SO-123" in result
        assert "Product A" in result

    @pytest.mark.asyncio
    async def test_handle_tool_list_purchase_orders(self):
        """Test handle_tool routes order_list_purchase correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "trans_number": "PO-001",
                        "contact_name": "Vendor X",
                        "trans_date": "2024-10-10",
                        "grand_total": 25000
                    }
                ]
            }
        })

        result = await orders.handle_tool(
            "order_list_purchase",
            {},
            mock_client
        )

        assert "Purchase Orders" in result
        assert "PO-001" in result

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await orders.handle_tool(
            "order_unknown_tool",
            {},
            mock_client
        )

        assert "Unknown order tool" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_no_results(self):
        """Test listing sales orders with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await orders.handle_tool(
            "order_list_sales",
            {},
            mock_client
        )

        assert "No sales orders found" in result

    @pytest.mark.asyncio
    async def test_get_order_detail_missing_id(self):
        """Test getting order detail without order_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await orders.handle_tool(
            "order_get_detail",
            {},
            mock_client
        )

        assert "order_id is required" in result

    @pytest.mark.asyncio
    async def test_get_order_detail_not_found(self):
        """Test getting order detail for non-existent order."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": None}})

        result = await orders.handle_tool(
            "order_get_detail",
            {"order_id": 999},
            mock_client
        )

        assert "Order #999 not found" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_with_date_range(self):
        """Test listing sales orders with date range."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": [
                {"trans_number": "SO-100", "contact_name": "Test",
                 "trans_date": "2024-10-15", "grand_total": 10000, "status_name": "Pending"}
            ]}
        })

        result = await orders.handle_tool(
            "order_list_sales",
            {"date_from": "2024-10-01", "date_to": "2024-10-31"},
            mock_client
        )

        assert "SO-100" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_calculates_total(self):
        """Test that list calculates total amount."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": [
                {"trans_number": "SO-1", "contact_name": "A", "trans_date": "2024-10-01",
                 "grand_total": 50000, "status_name": "Pending"},
                {"trans_number": "SO-2", "contact_name": "B", "trans_date": "2024-10-02",
                 "grand_total": 75000, "status_name": "Approved"}
            ]}
        })

        result = await orders.handle_tool(
            "order_list_sales",
            {},
            mock_client
        )

        assert "125,000" in result or "125000" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_limits_display(self):
        """Test that listing limits display to 20 orders."""
        mock_orders = [
            {"trans_number": f"SO-{i:03d}", "contact_name": f"Customer {i}",
             "trans_date": "2024-10-01", "grand_total": 10000, "status_name": "Pending"}
            for i in range(25)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": mock_orders}})

        result = await orders.handle_tool(
            "order_list_sales",
            {},
            mock_client
        )

        assert "5 more orders" in result

    @pytest.mark.asyncio
    async def test_list_sales_orders_error_handling(self):
        """Test error handling in list sales orders."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await orders.handle_tool(
            "order_list_sales",
            {},
            mock_client
        )

        assert "Error fetching sales orders" in result

    @pytest.mark.asyncio
    async def test_get_order_detail_error_handling(self):
        """Test error handling in get order detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await orders.handle_tool(
            "order_get_detail",
            {"order_id": 123},
            mock_client
        )

        assert "Error fetching order details" in result
