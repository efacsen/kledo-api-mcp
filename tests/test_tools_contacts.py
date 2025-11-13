"""
Tests for contact tools
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import contacts
from src.kledo_client import KledoAPIClient


class TestContactTools:
    """Test suite for contact tools."""

    def test_get_tools(self):
        """Test get_tools returns correct tool definitions."""
        tools = contacts.get_tools()

        assert len(tools) == 3
        assert all(isinstance(tool, Tool) for tool in tools)

        tool_names = [tool.name for tool in tools]
        assert "contact_list" in tool_names
        assert "contact_get_detail" in tool_names
        assert "contact_get_transactions" in tool_names

    def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = contacts.get_tools()

        for tool in tools:
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_handle_tool_list_contacts(self):
        """Test handle_tool routes contact_list correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "name": "ABC Corporation",
                        "company": "ABC Corp",
                        "email": "contact@abc.com",
                        "phone": "08123456789",
                        "type_name": "Customer"
                    },
                    {
                        "name": "XYZ Supplier",
                        "company": "XYZ Ltd",
                        "email": "info@xyz.com",
                        "phone": "08198765432",
                        "type_name": "Vendor"
                    }
                ]
            }
        })

        result = await contacts.handle_tool(
            "contact_list",
            {"search": "ABC"},
            mock_client
        )

        assert isinstance(result, str)
        assert "Contacts" in result
        assert "ABC Corporation" in result
        assert "contact@abc.com" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_contact_detail(self):
        """Test handle_tool routes contact_get_detail correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": {
                    "name": "John Doe",
                    "company": "Doe Enterprises",
                    "type_name": "Customer",
                    "email": "john@doe.com",
                    "phone": "08111222333",
                    "address": "123 Main Street, Jakarta",
                    "total_receivable": 5000000,
                    "total_payable": 0
                }
            }
        })

        result = await contacts.handle_tool(
            "contact_get_detail",
            {"contact_id": 123},
            mock_client
        )

        assert "Contact Details" in result
        assert "John Doe" in result
        assert "Doe Enterprises" in result
        assert "Receivable" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_contact_transactions(self):
        """Test handle_tool routes contact_get_transactions correctly."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={
            "data": {
                "data": [
                    {
                        "type": "Invoice",
                        "trans_number": "INV-001",
                        "date": "2024-10-15",
                        "amount": 1000000,
                        "status": "Paid"
                    },
                    {
                        "type": "Invoice",
                        "trans_number": "INV-002",
                        "date": "2024-10-20",
                        "amount": 500000,
                        "status": "Pending"
                    }
                ]
            }
        })

        result = await contacts.handle_tool(
            "contact_get_transactions",
            {"contact_id": 123},
            mock_client
        )

        assert "Contact Transaction History" in result
        assert "INV-001" in result
        assert "Total Transactions" in result

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await contacts.handle_tool(
            "contact_unknown_tool",
            {},
            mock_client
        )

        assert "Unknown contact tool" in result

    @pytest.mark.asyncio
    async def test_list_contacts_no_results(self):
        """Test listing contacts with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(return_value={"data": {"data": []}})

        result = await contacts.handle_tool(
            "contact_list",
            {},
            mock_client
        )

        assert "No contacts found" in result

    @pytest.mark.asyncio
    async def test_get_contact_detail_missing_id(self):
        """Test getting contact detail without contact_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await contacts.handle_tool(
            "contact_get_detail",
            {},
            mock_client
        )

        assert "contact_id is required" in result

    @pytest.mark.asyncio
    async def test_get_contact_detail_not_found(self):
        """Test getting contact detail for non-existent contact."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": None}})

        result = await contacts.handle_tool(
            "contact_get_detail",
            {"contact_id": 999},
            mock_client
        )

        assert "Contact #999 not found" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_missing_id(self):
        """Test getting transactions without contact_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await contacts.handle_tool(
            "contact_get_transactions",
            {},
            mock_client
        )

        assert "contact_id is required" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_no_results(self):
        """Test getting transactions with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await contacts.handle_tool(
            "contact_get_transactions",
            {"contact_id": 123},
            mock_client
        )

        assert "No transactions found" in result

    @pytest.mark.asyncio
    async def test_list_contacts_with_type_filter(self):
        """Test listing contacts with type filter."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(return_value={
            "data": {"data": [
                {"name": "Customer A", "company": None, "email": "a@test.com",
                 "phone": "123", "type_name": "Customer"}
            ]}
        })

        result = await contacts.handle_tool(
            "contact_list",
            {"type_id": 1},
            mock_client
        )

        assert "Customer A" in result
        mock_client.list_contacts.assert_called_once_with(
            search=None,
            type_id=1,
            per_page=50
        )

    @pytest.mark.asyncio
    async def test_list_contacts_limits_display(self):
        """Test that listing limits display to 30 contacts."""
        mock_contacts = [
            {"name": f"Contact {i}", "company": f"Company {i}", "email": f"email{i}@test.com",
             "phone": f"08{i}", "type_name": "Customer"}
            for i in range(35)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(return_value={"data": {"data": mock_contacts}})

        result = await contacts.handle_tool(
            "contact_list",
            {},
            mock_client
        )

        assert "5 more contacts" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_limits_display(self):
        """Test that transactions listing limits to 20 items."""
        mock_transactions = [
            {"type": "Invoice", "trans_number": f"INV-{i:03d}", "date": "2024-10-01",
             "amount": 10000, "status": "Paid"}
            for i in range(25)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": mock_transactions}})

        result = await contacts.handle_tool(
            "contact_get_transactions",
            {"contact_id": 123},
            mock_client
        )

        assert "5 more transactions" in result

    @pytest.mark.asyncio
    async def test_list_contacts_error_handling(self):
        """Test error handling in list contacts."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(side_effect=Exception("Database error"))

        result = await contacts.handle_tool(
            "contact_list",
            {},
            mock_client
        )

        assert "Error fetching contacts" in result

    @pytest.mark.asyncio
    async def test_get_contact_detail_error_handling(self):
        """Test error handling in get contact detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await contacts.handle_tool(
            "contact_get_detail",
            {"contact_id": 123},
            mock_client
        )

        assert "Error fetching contact details" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_error_handling(self):
        """Test error handling in get transactions."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await contacts.handle_tool(
            "contact_get_transactions",
            {"contact_id": 123},
            mock_client
        )

        assert "Error fetching contact transactions" in result
