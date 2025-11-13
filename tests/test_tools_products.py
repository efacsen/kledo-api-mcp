"""
Tests for product tools
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import products
from src.kledo_client import KledoAPIClient


class TestProductTools:
    """Test suite for product tools."""

    def test_get_tools(self):
        """Test get_tools returns correct tool definitions."""
        tools = products.get_tools()

        assert len(tools) == 3
        assert all(isinstance(tool, Tool) for tool in tools)

        tool_names = [tool.name for tool in tools]
        assert "product_list" in tool_names
        assert "product_get_detail" in tool_names
        assert "product_search_by_sku" in tool_names

    def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = products.get_tools()

        for tool in tools:
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_handle_tool_list_products(self):
        """Test handle_tool routes product_list correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_products = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "name": "Laptop Dell XPS",
                        "code": "LAP-001",
                        "price": 15000000,
                        "qty": 5,
                        "category_name": "Electronics"
                    },
                    {
                        "name": "Mouse Wireless",
                        "code": "MSE-001",
                        "price": 150000,
                        "qty": 20,
                        "category_name": "Accessories"
                    }
                ]
            }
        })

        result = await products.handle_tool(
            "product_list",
            {"search": "laptop"},
            mock_client
        )

        assert isinstance(result, str)
        assert "Products" in result
        assert "Laptop Dell XPS" in result
        assert "LAP-001" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_product_detail(self):
        """Test handle_tool routes product_get_detail correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": {
                    "name": "Laptop Dell XPS 15",
                    "code": "LAP-XPS-15",
                    "category_name": "Electronics",
                    "description": "High-performance laptop",
                    "price": 18000000,
                    "buy_price": 15000000,
                    "qty": 3,
                    "warehouses": [
                        {"name": "Main Warehouse", "qty": 2},
                        {"name": "Branch Warehouse", "qty": 1}
                    ]
                }
            }
        })

        result = await products.handle_tool(
            "product_get_detail",
            {"product_id": 123},
            mock_client
        )

        assert "Product Details" in result
        assert "Laptop Dell XPS 15" in result
        assert "Main Warehouse" in result

    @pytest.mark.asyncio
    async def test_handle_tool_search_by_sku(self):
        """Test handle_tool routes product_search_by_sku correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "name": "Product ABC",
                        "code": "SKU-123",
                        "price": 50000,
                        "buy_price": 40000,
                        "qty": 10,
                        "category_name": "General"
                    }
                ]
            }
        })

        result = await products.handle_tool(
            "product_search_by_sku",
            {"sku": "SKU-123"},
            mock_client
        )

        assert "Product Information" in result
        assert "Product ABC" in result
        assert "SKU-123" in result

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await products.handle_tool(
            "product_unknown_tool",
            {},
            mock_client
        )

        assert "Unknown product tool" in result

    @pytest.mark.asyncio
    async def test_list_products_no_results(self):
        """Test listing products with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_products = AsyncMock(return_value={"data": {"data": []}})

        result = await products.handle_tool(
            "product_list",
            {},
            mock_client
        )

        assert "No products found" in result

    @pytest.mark.asyncio
    async def test_get_product_detail_missing_id(self):
        """Test getting product detail without product_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await products.handle_tool(
            "product_get_detail",
            {},
            mock_client
        )

        assert "product_id is required" in result

    @pytest.mark.asyncio
    async def test_get_product_detail_not_found(self):
        """Test getting product detail for non-existent product."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": None}})

        result = await products.handle_tool(
            "product_get_detail",
            {"product_id": 999},
            mock_client
        )

        assert "Product #999 not found" in result

    @pytest.mark.asyncio
    async def test_search_by_sku_missing_sku(self):
        """Test searching by SKU without sku parameter."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await products.handle_tool(
            "product_search_by_sku",
            {},
            mock_client
        )

        assert "sku is required" in result

    @pytest.mark.asyncio
    async def test_search_by_sku_not_found(self):
        """Test searching by SKU that doesn't exist."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await products.handle_tool(
            "product_search_by_sku",
            {"sku": "NONEXISTENT"},
            mock_client
        )

        assert "No product found with SKU: NONEXISTENT" in result

    @pytest.mark.asyncio
    async def test_list_products_with_inventory(self):
        """Test listing products with inventory flag."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_products = AsyncMock(return_value={
            "data": {"data": [
                {"name": "Product A", "code": "PRD-A", "price": 10000,
                 "qty": 15, "category_name": "Cat1"}
            ]}
        })

        result = await products.handle_tool(
            "product_list",
            {"include_inventory": True},
            mock_client
        )

        assert "Stock" in result
        mock_client.list_products.assert_called_once_with(
            search=None,
            include_warehouse_qty=True,
            per_page=50
        )

    @pytest.mark.asyncio
    async def test_list_products_limits_display(self):
        """Test that listing limits display to 30 products."""
        mock_products = [
            {"name": f"Product {i}", "code": f"PRD-{i:03d}", "price": 10000,
             "qty": 5, "category_name": "Category"}
            for i in range(35)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_products = AsyncMock(return_value={"data": {"data": mock_products}})

        result = await products.handle_tool(
            "product_list",
            {},
            mock_client
        )

        assert "5 more products" in result

    @pytest.mark.asyncio
    async def test_list_products_error_handling(self):
        """Test error handling in list products."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_products = AsyncMock(side_effect=Exception("Database error"))

        result = await products.handle_tool(
            "product_list",
            {},
            mock_client
        )

        assert "Error fetching products" in result

    @pytest.mark.asyncio
    async def test_get_product_detail_error_handling(self):
        """Test error handling in get product detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await products.handle_tool(
            "product_get_detail",
            {"product_id": 123},
            mock_client
        )

        assert "Error fetching product details" in result

    @pytest.mark.asyncio
    async def test_search_by_sku_error_handling(self):
        """Test error handling in search by SKU."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Search error"))

        result = await products.handle_tool(
            "product_search_by_sku",
            {"sku": "TEST"},
            mock_client
        )

        assert "Error searching product by SKU" in result
