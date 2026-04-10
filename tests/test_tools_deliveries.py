"""
Tests for delivery tools — post-migration (no get_tools/handle_tool).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from src.tools import deliveries
from src.kledo_client import KledoAPIClient


class TestDeliveryHandlerFunctions:
    """Verify private handler functions exist and are async."""

    def test_handler_functions_are_callable(self):
        assert callable(deliveries._list_deliveries)
        assert asyncio.iscoroutinefunction(deliveries._list_deliveries)
        assert callable(deliveries._get_delivery_detail)
        assert asyncio.iscoroutinefunction(deliveries._get_delivery_detail)
        assert callable(deliveries._get_pending_deliveries)
        assert asyncio.iscoroutinefunction(deliveries._get_pending_deliveries)

    def test_no_legacy_interface(self):
        assert not hasattr(deliveries, "get_tools"), "deliveries still exports get_tools()"
        assert not hasattr(deliveries, "handle_tool"), "deliveries still exports handle_tool()"


class TestDeliveryTools:
    """Test suite for delivery private functions."""

    @pytest.mark.asyncio
    async def test_list_deliveries(self):
        """Test _list_deliveries returns formatted list."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "ref_number": "DEL-001",
                            "contact": {"name": "Customer A"},
                            "trans_date": "2024-10-15",
                            "status_id": 3,
                            "shipping_company": {"name": "JNE"},
                        },
                        {
                            "ref_number": "DEL-002",
                            "contact": {"name": "Customer B"},
                            "trans_date": "2024-10-16",
                            "status_id": 2,
                            "shipping_company": {"name": "JNT"},
                        },
                    ]
                }
            }
        )

        result = await deliveries._list_deliveries({}, mock_client)

        assert isinstance(result, str)
        assert "Deliveries" in result
        assert "DEL-001" in result
        assert "Customer A" in result
        assert "JNE" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail(self):
        """Test _get_delivery_detail returns formatted delivery info."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": {
                        "ref_number": "DEL-123",
                        "contact": {"name": "ABC Corp"},
                        "trans_date": "2024-10-20",
                        "status_id": 3,
                        "shipping_company": {"name": "JNE Express"},
                        "tracking_number": "JNE123456789",
                        "shipping_address": "Jl. Sudirman No. 123, Jakarta",
                        "memo": "Handle with care",
                        "detail": [
                            {"desc": "Product A", "qty": 5},
                            {"desc": "Product B", "qty": 2},
                        ],
                    }
                }
            }
        )

        result = await deliveries._get_delivery_detail({"delivery_id": 123}, mock_client)

        assert "Delivery Details" in result
        assert "DEL-123" in result
        assert "JNE123456789" in result
        assert "Product A" in result

    @pytest.mark.asyncio
    async def test_get_pending_deliveries(self):
        """Test _get_pending_deliveries returns pending list."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "ref_number": "DEL-001",
                            "contact": {"name": "Customer X"},
                            "trans_date": "2024-10-18",
                        },
                        {
                            "ref_number": "DEL-002",
                            "contact": {"name": "Customer Y"},
                            "trans_date": "2024-10-19",
                        },
                    ]
                }
            }
        )

        result = await deliveries._get_pending_deliveries({}, mock_client)

        assert "Pending Deliveries" in result
        assert "Total Pending" in result
        assert "DEL-001" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_no_results(self):
        """Test listing deliveries with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await deliveries._list_deliveries({}, mock_client)

        assert "No deliveries found" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail_missing_id(self):
        """Test getting delivery detail without delivery_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await deliveries._get_delivery_detail({}, mock_client)

        assert "delivery_id is required" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail_not_found(self):
        """Test getting delivery detail for non-existent delivery."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": None}})

        result = await deliveries._get_delivery_detail({"delivery_id": 999}, mock_client)

        assert "Delivery #999 not found" in result

    @pytest.mark.asyncio
    async def test_get_pending_deliveries_none(self):
        """Test getting pending deliveries with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await deliveries._get_pending_deliveries({}, mock_client)

        assert "No pending deliveries found" in result
        assert "All orders have been delivered" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_with_date_range(self):
        """Test listing deliveries with date range."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "ref_number": "DEL-100",
                            "contact": {"name": "Test Customer"},
                            "trans_date": "2024-10-15",
                            "status_id": 3,
                            "shipping_company": {"name": "JNE"},
                        }
                    ]
                }
            }
        )

        result = await deliveries._list_deliveries(
            {"date_from": "2024-10-01", "date_to": "2024-10-31"}, mock_client
        )

        assert "DEL-100" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_limits_display(self):
        """Test that listing limits display to 20 deliveries."""
        mock_deliveries = [
            {
                "ref_number": f"DEL-{i:03d}",
                "contact": {"name": f"Customer {i}"},
                "trans_date": "2024-10-01",
                "status_id": 3,
                "shipping_company": {"name": "JNE"},
            }
            for i in range(25)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": mock_deliveries}})

        result = await deliveries._list_deliveries({}, mock_client)

        assert "5 more deliveries" in result

    @pytest.mark.asyncio
    async def test_list_deliveries_error_handling(self):
        """Test error handling in list deliveries."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await deliveries._list_deliveries({}, mock_client)

        assert "Error fetching deliveries" in result

    @pytest.mark.asyncio
    async def test_get_delivery_detail_error_handling(self):
        """Test error handling in get delivery detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await deliveries._get_delivery_detail({"delivery_id": 123}, mock_client)

        assert "Error fetching delivery details" in result

    @pytest.mark.asyncio
    async def test_get_pending_deliveries_error_handling(self):
        """Test error handling in get pending deliveries."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Database error"))

        result = await deliveries._get_pending_deliveries({}, mock_client)

        assert "Error fetching pending deliveries" in result
