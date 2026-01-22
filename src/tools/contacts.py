"""
Contact/CRM tools for Kledo MCP Server
"""
from typing import Any, Dict
from mcp.types import Tool

from ..kledo_client import KledoAPIClient
from ..utils.helpers import format_currency, safe_get


def get_tools() -> list[Tool]:
    """Get list of contact tools."""
    return [
        Tool(
            name="contact_list",
            description="List customers and vendors with optional search and filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search by name, email, phone, or company"
                    },
                    "type_id": {
                        "type": "integer",
                        "description": "Filter by type (1=Customer, 2=Vendor, 3=Both)"
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 50)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="contact_get_detail",
            description="Get detailed information about a specific contact/customer/vendor.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "integer",
                        "description": "Contact ID"
                    }
                },
                "required": ["contact_id"]
            }
        ),
        Tool(
            name="contact_get_transactions",
            description="Get transaction history for a contact (invoices, payments, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "integer",
                        "description": "Contact ID"
                    }
                },
                "required": ["contact_id"]
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle contact tool calls."""
    if name == "contact_list":
        return await _list_contacts(arguments, client)
    elif name == "contact_get_detail":
        return await _get_contact_detail(arguments, client)
    elif name == "contact_get_transactions":
        return await _get_contact_transactions(arguments, client)
    else:
        return f"Unknown contact tool: {name}"


async def _list_contacts(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List contacts."""
    try:
        data = await client.list_contacts(
            search=args.get("search"),
            type_id=args.get("type_id"),
            per_page=args.get("per_page", 50)
        )

        result = ["# Contacts\n"]

        contacts = safe_get(data, "data.data", [])

        if not contacts:
            result.append("No contacts found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(contacts)}\n")

        result.append("\n## Contact List:\n")

        for contact in contacts[:30]:
            name = safe_get(contact, "name", "Unknown")
            company = safe_get(contact, "company")
            email = safe_get(contact, "email", "N/A")
            phone = safe_get(contact, "phone", "N/A")
            type_name = safe_get(contact, "type_name", "Unknown")

            result.append(f"### {name}")
            if company:
                result.append(f"- **Company**: {company}")
            result.append(f"- **Type**: {type_name}")
            result.append(f"- **Email**: {email}")
            result.append(f"- **Phone**: {phone}\n")

        if len(contacts) > 30:
            result.append(f"... and {len(contacts) - 30} more contacts")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching contacts: {str(e)}"


async def _get_contact_detail(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get contact detail."""
    contact_id = args.get("contact_id")

    if not contact_id:
        return "Error: contact_id is required"

    try:
        data = await client.get(
            "contacts",
            "detail",
            path_params={"id": contact_id},
            cache_category="contacts"
        )

        contact = safe_get(data, "data.data")
        if not contact:
            return f"Contact #{contact_id} not found"

        result = ["# Contact Details\n"]

        result.append(f"**Name**: {safe_get(contact, 'name', 'Unknown')}")

        company = safe_get(contact, "company")
        if company:
            result.append(f"**Company**: {company}")

        result.append(f"**Type**: {safe_get(contact, 'type_name', 'Unknown')}")
        result.append(f"**Email**: {safe_get(contact, 'email', 'N/A')}")
        result.append(f"**Phone**: {safe_get(contact, 'phone', 'N/A')}")

        # Address
        address = safe_get(contact, "address")
        if address:
            result.append(f"**Address**: {address}")

        # Financial info
        result.append("\n## Financial Summary:")
        receivable = safe_get(contact, "total_receivable", 0)
        payable = safe_get(contact, "total_payable", 0)

        if receivable > 0:
            result.append(f"- **Receivable**: {format_currency(receivable)}")
        if payable > 0:
            result.append(f"- **Payable**: {format_currency(payable)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching contact details: {str(e)}"


async def _get_contact_transactions(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get contact transaction history."""
    contact_id = args.get("contact_id")

    if not contact_id:
        return "Error: contact_id is required"

    try:
        data = await client.get(
            "contacts",
            "transactions",
            path_params={"id": contact_id},
            cache_category="contacts"
        )

        result = ["# Contact Transaction History\n"]

        transactions = safe_get(data, "data.data", [])

        if not transactions:
            result.append("No transactions found for this contact.")
            return "\n".join(result)

        result.append(f"**Total Transactions**: {len(transactions)}\n")

        # Calculate summary
        total_amount = sum(safe_get(t, "amount_after_tax", 0) for t in transactions)
        result.append(f"**Total Amount**: {format_currency(total_amount)}\n")

        result.append("\n## Recent Transactions:\n")

        # Status mapping
        status_map = {1: "Draft", 2: "Pending", 3: "Paid", 4: "Partial", 5: "Overdue"}

        for trans in transactions[:20]:
            trans_type = safe_get(trans, "type", "Unknown")
            trans_number = safe_get(trans, "ref_number", "N/A")
            date = safe_get(trans, "trans_date", "")
            amount = safe_get(trans, "amount_after_tax", 0)
            status_id = safe_get(trans, "status_id", 0)
            status = status_map.get(status_id, f"Status-{status_id}")

            result.append(f"### {trans_number}")
            result.append(f"- **Type**: {trans_type}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Amount**: {format_currency(amount)}")
            result.append(f"- **Status**: {status}\n")

        if len(transactions) > 20:
            result.append(f"... and {len(transactions) - 20} more transactions")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching contact transactions: {str(e)}"
