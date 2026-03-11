"""
Tests for Kledo MCP Server module-level functions.

The server uses module-level decorators (@server.list_tools, @server.call_tool)
rather than a class-based approach, so tests target the underlying functions directly.
"""
import pytest
import os
from unittest.mock import AsyncMock, Mock, patch
from mcp.types import TextContent, Tool

import src.server as server_module


class TestListTools:
    """Tests for the list_tools function."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_list(self):
        """Test that list_tools returns a non-empty list of Tool objects."""
        tools = await server_module.list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(t, Tool) for t in tools)

    @pytest.mark.asyncio
    async def test_list_tools_contains_expected_prefixes(self):
        """Test that tools from all modules are registered."""
        tools = await server_module.list_tools()
        tool_names = [t.name for t in tools]

        expected_prefixes = [
            "financial_", "invoice_", "order_", "product_",
            "contact_", "delivery_", "utility_", "sales_rep_",
            "analytics_", "commission_",
        ]
        for prefix in expected_prefixes:
            assert any(n.startswith(prefix) for n in tool_names), (
                f"No tool found with prefix '{prefix}'"
            )

    @pytest.mark.asyncio
    async def test_list_tools_all_have_schemas(self):
        """Test that every registered tool has a valid input schema."""
        tools = await server_module.list_tools()

        for tool in tools:
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"


class TestCallTool:
    """Tests for the call_tool function."""

    @pytest.mark.asyncio
    async def test_call_tool_routes_financial(self):
        """Test that financial_ tools are routed to financial module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.financial") as mock_financial:
            mock_financial.handle_tool = AsyncMock(return_value="Financial result")

            result = await server_module.call_tool(
                "financial_activity_team_report", {"date_from": "2024-01-01"}
            )

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert result[0].text == "Financial result"
            mock_financial.handle_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_routes_invoice(self):
        """Test that invoice_ tools are routed to invoices module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.invoices") as mock_invoices:
            mock_invoices.handle_tool = AsyncMock(return_value="Invoice result")

            result = await server_module.call_tool("invoice_list_sales", {})

            assert result[0].text == "Invoice result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_order(self):
        """Test that order_ tools are routed to orders module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.orders") as mock_orders:
            mock_orders.handle_tool = AsyncMock(return_value="Order result")

            result = await server_module.call_tool("order_list_sales", {})

            assert result[0].text == "Order result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_product(self):
        """Test that product_ tools are routed to products module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.products") as mock_products:
            mock_products.handle_tool = AsyncMock(return_value="Product result")

            result = await server_module.call_tool("product_list", {})

            assert result[0].text == "Product result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_contact(self):
        """Test that contact_ tools are routed to contacts module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.contacts") as mock_contacts:
            mock_contacts.handle_tool = AsyncMock(return_value="Contact result")

            result = await server_module.call_tool("contact_list", {})

            assert result[0].text == "Contact result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_delivery(self):
        """Test that delivery_ tools are routed to deliveries module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.deliveries") as mock_deliveries:
            mock_deliveries.handle_tool = AsyncMock(return_value="Delivery result")

            result = await server_module.call_tool("delivery_list", {})

            assert result[0].text == "Delivery result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_utility(self):
        """Test that utility_ tools are routed to utilities module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.utilities") as mock_utilities:
            mock_utilities.handle_tool = AsyncMock(return_value="Utility result")

            result = await server_module.call_tool("utility_clear_cache", {})

            assert result[0].text == "Utility result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_analytics(self):
        """Test that analytics_ tools are routed to analytics module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.analytics") as mock_analytics:
            mock_analytics.handle_tool = AsyncMock(return_value="Analytics result")

            result = await server_module.call_tool("analytics_compare", {})

            assert result[0].text == "Analytics result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_commission(self):
        """Test that commission_ tools are routed to commission module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.commission") as mock_commission:
            mock_commission.handle_tool = AsyncMock(return_value="Commission result")

            result = await server_module.call_tool("commission_calculate", {})

            assert result[0].text == "Commission result"

    @pytest.mark.asyncio
    async def test_call_tool_routes_revenue(self):
        """Test that revenue tools are routed to revenue module."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.revenue") as mock_revenue:
            mock_revenue.handle_tool = AsyncMock(return_value="Revenue result")

            result = await server_module.call_tool("revenue_summary", {})

            assert result[0].text == "Revenue result"

    @pytest.mark.asyncio
    async def test_call_tool_unknown_returns_error(self):
        """Test that calling an unknown tool returns an error message."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client):
            result = await server_module.call_tool("unknown_tool_xyz", {})

        assert len(result) == 1
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_error_handling(self):
        """Test that exceptions in tool handlers are caught and returned as error text."""
        mock_client = Mock()
        with patch.object(server_module, "client", mock_client), \
             patch("src.server.invoices") as mock_invoices:
            mock_invoices.handle_tool = AsyncMock(side_effect=Exception("Test error"))

            result = await server_module.call_tool("invoice_list_sales", {})

        assert len(result) == 1
        assert "Error executing tool" in result[0].text
        assert "Test error" in result[0].text


class TestInitializeClient:
    """Tests for the initialize_client function."""

    @pytest.mark.asyncio
    async def test_initialize_client_uses_api_key(self, mock_env_vars, monkeypatch):
        """Test that KLEDO_API_KEY takes priority over email/password."""
        monkeypatch.setenv("KLEDO_API_KEY", "test-api-key-123")

        with patch("src.server.KledoAuthenticator") as mock_auth_class, \
             patch("src.server.KledoCache"), \
             patch("src.server.KledoAPIClient") as mock_client_class, \
             patch.object(server_module, "client", None):

            mock_auth = AsyncMock()
            mock_auth.login = AsyncMock(return_value=True)
            mock_auth_class.return_value = mock_auth
            mock_client_class.return_value = Mock()

            await server_module.initialize_client()

            # Auth should be created with api_key, not email/password
            call_kwargs = mock_auth_class.call_args.kwargs
            assert call_kwargs.get("api_key") == "test-api-key-123"
            assert "email" not in call_kwargs

        # Reset global client state
        server_module.client = None

    @pytest.mark.asyncio
    async def test_initialize_client_fails_on_login_error(self, mock_env_vars):
        """Test that failed login raises ValueError."""
        with patch("src.server.KledoAuthenticator") as mock_auth_class, \
             patch.object(server_module, "client", None):

            mock_auth = AsyncMock()
            mock_auth.login = AsyncMock(return_value=False)
            mock_auth_class.return_value = mock_auth

            with pytest.raises(ValueError, match="Failed to authenticate"):
                await server_module.initialize_client()

        server_module.client = None

    @pytest.mark.asyncio
    async def test_initialize_client_reuses_existing(self):
        """Test that initialize_client returns existing client without re-initializing."""
        existing_client = Mock()
        with patch.object(server_module, "client", existing_client), \
             patch("src.server.KledoAuthenticator") as mock_auth_class:

            result = await server_module.initialize_client()

            assert result is existing_client
            mock_auth_class.assert_not_called()
