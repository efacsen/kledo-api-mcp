"""
Tests for Kledo MCP Server
"""
import pytest
import os
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from mcp.types import TextContent

from src.server import KledoMCPServer


class TestKledoMCPServer:
    """Test suite for KledoMCPServer class."""

    def test_init(self):
        """Test server initialization."""
        server = KledoMCPServer()

        assert server.server is not None
        assert server.client is None

    @pytest.mark.asyncio
    async def test_initialize_client_success(self, mock_env_vars):
        """Test successful client initialization."""
        server = KledoMCPServer()

        with patch("src.server.KledoAuthenticator") as mock_auth_class, \
             patch("src.server.KledoCache") as mock_cache_class, \
             patch("src.server.KledoAPIClient") as mock_client_class:

            mock_auth = AsyncMock()
            mock_auth.login = AsyncMock(return_value=True)
            mock_auth_class.return_value = mock_auth

            mock_cache = Mock()
            mock_cache_class.return_value = mock_cache

            mock_client = Mock()
            mock_client_class.return_value = mock_client

            await server.initialize_client()

            assert server.client is not None
            mock_auth.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_client_missing_credentials(self):
        """Test client initialization with missing credentials."""
        server = KledoMCPServer()

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="KLEDO_EMAIL and KLEDO_PASSWORD must be set"):
                await server.initialize_client()

    @pytest.mark.asyncio
    async def test_initialize_client_login_failure(self, mock_env_vars):
        """Test client initialization with login failure."""
        server = KledoMCPServer()

        with patch("src.server.KledoAuthenticator") as mock_auth_class:
            mock_auth = AsyncMock()
            mock_auth.login = AsyncMock(return_value=False)
            mock_auth_class.return_value = mock_auth

            with pytest.raises(ValueError, match="Failed to authenticate"):
                await server.initialize_client()

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing all available tools."""
        server = KledoMCPServer()

        with patch("src.server.financial") as mock_financial, \
             patch("src.server.invoices") as mock_invoices, \
             patch("src.server.orders") as mock_orders, \
             patch("src.server.products") as mock_products, \
             patch("src.server.contacts") as mock_contacts, \
             patch("src.server.deliveries") as mock_deliveries, \
             patch("src.server.utilities") as mock_utilities:

            mock_financial.get_tools.return_value = [Mock(name="financial_tool")]
            mock_invoices.get_tools.return_value = [Mock(name="invoice_tool")]
            mock_orders.get_tools.return_value = [Mock(name="order_tool")]
            mock_products.get_tools.return_value = [Mock(name="product_tool")]
            mock_contacts.get_tools.return_value = [Mock(name="contact_tool")]
            mock_deliveries.get_tools.return_value = [Mock(name="delivery_tool")]
            mock_utilities.get_tools.return_value = [Mock(name="utility_tool")]

            tools = await server.list_tools()

            assert len(tools) == 7

    @pytest.mark.asyncio
    async def test_call_tool_financial(self, mock_env_vars):
        """Test calling a financial tool."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.financial") as mock_financial:
            mock_financial.handle_tool = AsyncMock(return_value="Financial result")

            result = await server.call_tool(
                "financial_activity_team_report",
                {"date_from": "2024-01-01"}
            )

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert result[0].text == "Financial result"
            mock_financial.handle_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_invoice(self, mock_env_vars):
        """Test calling an invoice tool."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.invoices") as mock_invoices:
            mock_invoices.handle_tool = AsyncMock(return_value="Invoice result")

            result = await server.call_tool(
                "invoice_list_sales",
                {"per_page": 10}
            )

            assert len(result) == 1
            assert result[0].text == "Invoice result"

    @pytest.mark.asyncio
    async def test_call_tool_order(self, mock_env_vars):
        """Test calling an order tool."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.orders") as mock_orders:
            mock_orders.handle_tool = AsyncMock(return_value="Order result")

            result = await server.call_tool(
                "order_list_sales",
                {}
            )

            assert result[0].text == "Order result"

    @pytest.mark.asyncio
    async def test_call_tool_product(self, mock_env_vars):
        """Test calling a product tool."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.products") as mock_products:
            mock_products.handle_tool = AsyncMock(return_value="Product result")

            result = await server.call_tool(
                "product_list",
                {}
            )

            assert result[0].text == "Product result"

    @pytest.mark.asyncio
    async def test_call_tool_contact(self, mock_env_vars):
        """Test calling a contact tool."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.contacts") as mock_contacts:
            mock_contacts.handle_tool = AsyncMock(return_value="Contact result")

            result = await server.call_tool(
                "contact_list",
                {}
            )

            assert result[0].text == "Contact result"

    @pytest.mark.asyncio
    async def test_call_tool_delivery(self, mock_env_vars):
        """Test calling a delivery tool."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.deliveries") as mock_deliveries:
            mock_deliveries.handle_tool = AsyncMock(return_value="Delivery result")

            result = await server.call_tool(
                "delivery_list",
                {}
            )

            assert result[0].text == "Delivery result"

    @pytest.mark.asyncio
    async def test_call_tool_utility(self, mock_env_vars):
        """Test calling a utility tool."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.utilities") as mock_utilities:
            mock_utilities.handle_tool = AsyncMock(return_value="Utility result")

            result = await server.call_tool(
                "utility_clear_cache",
                {}
            )

            assert result[0].text == "Utility result"

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self, mock_env_vars):
        """Test calling an unknown tool."""
        server = KledoMCPServer()
        server.client = Mock()

        result = await server.call_tool(
            "unknown_tool",
            {}
        )

        assert len(result) == 1
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_error_handling(self, mock_env_vars):
        """Test tool call error handling."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch("src.server.invoices") as mock_invoices:
            mock_invoices.handle_tool = AsyncMock(
                side_effect=Exception("Test error")
            )

            result = await server.call_tool(
                "invoice_list_sales",
                {}
            )

            assert len(result) == 1
            assert "Error executing tool" in result[0].text
            assert "Test error" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_initializes_client_if_needed(self, mock_env_vars):
        """Test that call_tool initializes client if not present."""
        server = KledoMCPServer()
        assert server.client is None

        with patch.object(server, "initialize_client", new=AsyncMock()) as mock_init, \
             patch("src.server.utilities") as mock_utilities:

            mock_utilities.handle_tool = AsyncMock(return_value="Result")

            await server.call_tool("utility_test_connection", {})

            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_skips_initialization_if_client_exists(self, mock_env_vars):
        """Test that call_tool doesn't re-initialize if client exists."""
        server = KledoMCPServer()
        server.client = Mock()

        with patch.object(server, "initialize_client", new=AsyncMock()) as mock_init, \
             patch("src.server.utilities") as mock_utilities:

            mock_utilities.handle_tool = AsyncMock(return_value="Result")

            await server.call_tool("utility_test_connection", {})

            mock_init.assert_not_called()
