"""
Tests for contact tools — post-migration (no get_tools/handle_tool).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from src.tools import contacts
from src.kledo_client import KledoAPIClient


class TestContactHandlerFunctions:
    """Verify private handler functions exist and are async."""

    def test_handler_functions_are_callable(self):
        assert callable(contacts._list_contacts)
        assert asyncio.iscoroutinefunction(contacts._list_contacts)
        assert callable(contacts._get_contact_detail)
        assert asyncio.iscoroutinefunction(contacts._get_contact_detail)
        assert callable(contacts._get_contact_transactions)
        assert asyncio.iscoroutinefunction(contacts._get_contact_transactions)

    def test_no_legacy_interface(self):
        assert not hasattr(contacts, "get_tools"), "contacts still exports get_tools()"
        assert not hasattr(contacts, "handle_tool"), "contacts still exports handle_tool()"


class TestContactTools:
    """Test suite for contact private functions."""

    @pytest.mark.asyncio
    async def test_list_contacts(self):
        """Test _list_contacts returns formatted list."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "name": "ABC Corporation",
                            "company": "ABC Corp",
                            "email": "contact@abc.com",
                            "phone": "08123456789",
                            "type_name": "Customer",
                        },
                        {
                            "name": "XYZ Supplier",
                            "company": "XYZ Ltd",
                            "email": "info@xyz.com",
                            "phone": "08198765432",
                            "type_name": "Vendor",
                        },
                    ]
                }
            }
        )

        result = await contacts._list_contacts({"search": "ABC"}, mock_client)

        assert isinstance(result, str)
        assert "Contacts" in result
        assert "ABC Corporation" in result
        assert "contact@abc.com" in result

    @pytest.mark.asyncio
    async def test_get_contact_detail(self):
        """Test _get_contact_detail returns formatted contact info."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": {
                        "name": "John Doe",
                        "company": "Doe Enterprises",
                        "type_name": "Customer",
                        "email": "john@doe.com",
                        "phone": "08111222333",
                        "address": "123 Main Street, Jakarta",
                        "total_receivable": 5000000,
                        "total_payable": 0,
                    }
                }
            }
        )

        result = await contacts._get_contact_detail({"contact_id": 123}, mock_client)

        assert "Contact Details" in result
        assert "John Doe" in result
        assert "Doe Enterprises" in result
        assert "Receivable" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions(self):
        """Test _get_contact_transactions returns transaction history."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "type": "Invoice",
                            "ref_number": "INV-001",
                            "trans_date": "2024-10-15",
                            "amount_after_tax": 1000000,
                            "status_id": 3,
                        },
                        {
                            "type": "Invoice",
                            "ref_number": "INV-002",
                            "trans_date": "2024-10-20",
                            "amount_after_tax": 500000,
                            "status_id": 2,
                        },
                    ]
                }
            }
        )

        result = await contacts._get_contact_transactions({"contact_id": 123}, mock_client)

        assert "Contact Transaction History" in result
        assert "INV-001" in result
        assert "Total Transactions" in result

    @pytest.mark.asyncio
    async def test_list_contacts_no_results(self):
        """Test listing contacts with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(return_value={"data": {"data": []}})

        result = await contacts._list_contacts({}, mock_client)

        assert "No contacts found" in result

    @pytest.mark.asyncio
    async def test_get_contact_detail_missing_id(self):
        """Test getting contact detail without contact_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await contacts._get_contact_detail({}, mock_client)

        assert "contact_id is required" in result

    @pytest.mark.asyncio
    async def test_get_contact_detail_not_found(self):
        """Test getting contact detail for non-existent contact."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": None}})

        result = await contacts._get_contact_detail({"contact_id": 999}, mock_client)

        assert "Contact #999 not found" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_missing_id(self):
        """Test getting transactions without contact_id."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await contacts._get_contact_transactions({}, mock_client)

        assert "contact_id is required" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_no_results(self):
        """Test getting transactions with no results."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": []}})

        result = await contacts._get_contact_transactions({"contact_id": 123}, mock_client)

        assert "No transactions found" in result

    @pytest.mark.asyncio
    async def test_list_contacts_with_type_filter(self):
        """Test listing contacts with type filter."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(
            return_value={
                "data": {
                    "data": [
                        {
                            "name": "Customer A",
                            "company": None,
                            "email": "a@test.com",
                            "phone": "123",
                            "type_name": "Customer",
                        }
                    ]
                }
            }
        )

        result = await contacts._list_contacts({"type_id": 1}, mock_client)

        assert "Customer A" in result
        mock_client.list_contacts.assert_called_once_with(search=None, type_id=1, per_page=50)

    @pytest.mark.asyncio
    async def test_list_contacts_limits_display(self):
        """Test that listing limits display to 30 contacts."""
        mock_contacts = [
            {
                "name": f"Contact {i}",
                "company": f"Company {i}",
                "email": f"email{i}@test.com",
                "phone": f"08{i}",
                "type_name": "Customer",
            }
            for i in range(35)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(return_value={"data": {"data": mock_contacts}})

        result = await contacts._list_contacts({}, mock_client)

        assert "5 more contacts" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_limits_display(self):
        """Test that transactions listing limits to 20 items."""
        mock_transactions = [
            {
                "type": "Invoice",
                "trans_number": f"INV-{i:03d}",
                "date": "2024-10-01",
                "amount": 10000,
                "status": "Paid",
            }
            for i in range(25)
        ]

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(return_value={"data": {"data": mock_transactions}})

        result = await contacts._get_contact_transactions({"contact_id": 123}, mock_client)

        assert "5 more transactions" in result

    @pytest.mark.asyncio
    async def test_list_contacts_error_handling(self):
        """Test error handling in list contacts."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.list_contacts = AsyncMock(side_effect=Exception("Database error"))

        result = await contacts._list_contacts({}, mock_client)

        assert "Error fetching contacts" in result

    @pytest.mark.asyncio
    async def test_get_contact_detail_error_handling(self):
        """Test error handling in get contact detail."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await contacts._get_contact_detail({"contact_id": 123}, mock_client)

        assert "Error fetching contact details" in result

    @pytest.mark.asyncio
    async def test_get_contact_transactions_error_handling(self):
        """Test error handling in get transactions."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await contacts._get_contact_transactions({"contact_id": 123}, mock_client)

        assert "Error fetching contact transactions" in result
