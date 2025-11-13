"""
Tests for delivery tools
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import deliveries
from src.kledo_client import KledoAPIClient


class TestDeliveryTools:
    """Test suite for delivery tools."""

    def test_get_tools(self):
        """Test get_tools returns correct tool definitions."""
        tools = deliveries.get_tools()

        assert len(tools) == 3
        assert all(isinstance(tool, Tool) for tool in tools)

        tool_names = [tool.name for tool in tools]
        assert "delivery_list" in tool_names
        assert "delivery_get_detail" in tool_names
        assert "delivery_get_pending" in tool_names

    def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = deliveries.get_tools()

        for tool in tools:
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_handle_tool_list_deliveries(self):
        """Test handle_tool routes delivery_list correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "trans_number": "DEL-001",
                        "contact_name": "Customer A",
                        "trans_date": "2024-10-15",
                        "status_name": "Delivered",
                        "shipping_company_name": "JNE"
                    },
                    {
                        "trans_number": "DEL-002",
                        "contact_name": "Customer B",
                        "trans_date": "2024-10-16",
                        "status_name": "In Transit",
                        "shipping_company_name": "JNT"
                    }
                ]
            }
        })

        result = await deliveries.handle_tool(
            "delivery_list",
            {},
            mock_client
        )

        assert isinstance(result, str)
        assert "Deliveries" in result
        assert "DEL-001" in result
        assert "Customer A" in result
        assert "JNE" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_delivery_detail(self):
        """Test handle_tool routes delivery_get_detail correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": {
                    "trans_number": "DEL-123",
                    "contact_name": "ABC Corp",
                    "trans_date": "2024-10-20",
                    "status_name": "Delivered",
                    "shipping_company_name": "JNE Express",
                    "tracking_number": "JNE123456789",
                    "shipping_address": "Jl. Sudirman No. 123, Jakarta",
                    "ref_number": "INV-456",
                    "memo": "Handle with care",
                    "detail": [
                        {
                            "desc": "Product A",
                            "qty": 5
                        },
                        {
                            "desc": "Product B",
                            "qty": 2
                        }
                    ]
                }
            }
        })

        result = await deliveries.handle_tool(
            "delivery_get_detail",
            {"delivery_id": 123},
            mock_client
        )

        assert "Delivery Details" in result
        assert "DEL-123" in result
        assert "JNE123456789" in result
        assert "Product A" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_pending_deliveries(self):
        """Test handle_tool routes delivery_get_pending correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "trans_number": "DEL-001",
                        "contact_name": "Customer X",
                        "trans_date": "2024-10-18"
                    },
                    {
                        "trans_number": "DEL-002",
                        "contact_name": "Customer Y",
                        "trans_date": "2024-10-19"
                    }
                ]
            }
        })

        result = await deliveries.handle_tool(
            "delivery_get_pending",
            {},
            mock_client
        )

        assert "Pending Deliveries" in result
        assert "Total Pending" in result
        assert "DEL-001" in result

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await deliveries.handle_tool(
            "delivery_unknown_tool",
            {},
            mock_client
        )

        assert "Unknown delivery tool" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_no_results(self):
        """Test listing deliveries with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await deliveries.handle_tool(
            "delivery_list",
            {},
            mock_client
        )

        assert "No deliveries found" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail_missing_id(self):
        """Test getting delivery detail without delivery_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await deliveries.handle_tool(
            "delivery_get_detail",
            {},
            mock_client
        )

        assert "delivery_id is required" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail_not_found(self):
        """Test getting delivery detail for non-existent delivery."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": None}})

        result = await deliveries.handle_tool(
            "delivery_get_detail",
            {"delivery_id": 999},
            mock_client
        )

        assert "Delivery #999 not found" in result

    @pytest.mark.asyncio
    async def test_get_pending_deliveries_none(self):
        """Test getting pending deliveries with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await deliveries.handle_tool(
            "delivery_get_pending",
            {},
            mock_client
        )

        assert "No pending deliveries found" in result
        assert "All orders have been delivered" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_with_date_range(self):
        """Test listing deliveries with date range."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": [
                {"trans_number": "DEL-100", "contact_name": "Test Customer",
                 "trans_date": "2024-10-15", "status_name": "Delivered",
                 "shipping_company_name": "JNE"}
            ]}
        })

        result = await deliveries.handle_tool(
            "delivery_list",
            {"date_from": "2024-10-01", "date_to": "2024-10-31"},
            mock_client
        )

        assert "DEL-100" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_with_search(self):
        """Test listing deliveries with search parameter."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": [
                {"trans_number": "DEL-999", "contact_name": "ABC", "trans_date": "2024-10-20",
                 "status_name": "Delivered", "shipping_company_name": "JNE"}
            ]}
        })

        result = await deliveries.handle_tool(
            "delivery_list",
            {"search": "DEL-999"},
            mock_client
        )

        assert "DEL-999" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_limits_display(self):
        """Test that listing limits display to 20 deliveries."""
        mock_deliveries = [
            {"trans_number": f"DEL-{i:03d}", "contact_name": f"Customer {i}",
             "trans_date": "2024-10-01", "status_name": "Delivered",
             "shipping_company_name": "JNE"}
            for i in range(25)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": mock_deliveries}})

        result = await deliveries.handle_tool(
            "delivery_list",
            {},
            mock_client
        )

        assert "5 more deliveries" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail_with_all_fields(self):
        """Test delivery detail with all optional fields."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {"data": {
                "trans_number": "DEL-FULL",
                "contact_name": "Full Test",
                "trans_date": "2024-10-20",
                "status_name": "Delivered",
                "shipping_company_name": "Express Co",
                "tracking_number": "TRACK123",
                "shipping_address": "Full Address",
                "ref_number": "REF-123",
                "memo": "Test memo",
                "detail": [{"desc": "Item 1", "qty": 1}]
            }}
        })

        result = await deliveries.handle_tool(
            "delivery_get_detail",
            {"delivery_id": 1},
            mock_client
        )

        assert all(x in result for x in ["DEL-FULL", "TRACK123", "Full Address", "REF-123", "Test memo"])

    @pytest.mark.asyncio
    async def test_list_deliveries_error_handling(self):
        """Test error handling in list deliveries."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await deliveries.handle_tool(
            "delivery_list",
            {},
            mock_client
        )

        assert "Error fetching deliveries" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail_error_handling(self):
        """Test error handling in get delivery detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await deliveries.handle_tool(
            "delivery_get_detail",
            {"delivery_id": 123},
            mock_client
        )

        assert "Error fetching delivery details" in result

    @pytest.mark.asyncio
    async def test_get_pending_deliveries_error_handling(self):
        """Test error handling in get pending deliveries."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Database error"))

        result = await deliveries.handle_tool(
            "delivery_get_pending",
            {},
            mock_client
        )

        assert "Error fetching pending deliveries" in result
