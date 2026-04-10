"""
Phase 5 — Tool Quality contract tests.

These tests are intentionally RED until Phase 5 implementation is complete.
Wave 0 purpose: lock behavioral contracts before any code changes.

Requirements: QUAL-01, QUAL-02, QUAL-03
"""
import pytest
from unittest.mock import AsyncMock, Mock
from src.server import mcp
from src.tools import invoices, orders, deliveries, contacts, products
from src.kledo_client import KledoAPIClient


def _get_tools() -> dict:
    """Return the dict of registered tools from the FastMCP tool manager."""
    # mcp._tool_manager._tools is the internal dict[str, Tool] in mcp>=1.0.0
    return mcp._tool_manager._tools


# ---------------------------------------------------------------------------
# Tool names — all 24 tools registered in server.py
# ---------------------------------------------------------------------------

ALL_TOOL_NAMES = [
    "financial_activity",
    "financial_summary",
    "financial_balances",
    "invoice_list",
    "invoice_get",
    "invoice_summarize",
    "order_list",
    "order_get",
    "product_list",
    "product_get",
    "contact_list",
    "contact_get",
    "delivery_list",
    "delivery_get",
    "utility_cache",
    "utility_test_connection",
    "sales_rep_report",
    "sales_rep_list",
    "revenue_summary",
    "revenue_receivables",
    "revenue_ranking",
    "analytics_compare",
    "analytics_targets",
    "commission_report",
]


class TestToolDescriptions:
    """QUAL-01: Every @mcp.tool() must have a four-part description with WHAT/RETURNS/NOT/SIBLING."""

    @pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
    def test_description_has_what_marker(self, tool_name):
        """Each tool description must contain 'WHAT:'."""
        tools = _get_tools()
        assert tool_name in tools, f"Tool '{tool_name}' not registered in mcp"
        tool = tools[tool_name]
        desc = tool.description or ""
        assert "WHAT:" in desc, (
            f"Tool '{tool_name}' description missing 'WHAT:' marker. "
            f"Got: {desc[:100]!r}"
        )

    @pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
    def test_description_has_returns_marker(self, tool_name):
        """Each tool description must contain 'RETURNS:'."""
        tools = _get_tools()
        assert tool_name in tools, f"Tool '{tool_name}' not registered in mcp"
        tool = tools[tool_name]
        desc = tool.description or ""
        assert "RETURNS:" in desc, (
            f"Tool '{tool_name}' description missing 'RETURNS:' marker. "
            f"Got: {desc[:100]!r}"
        )

    @pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
    def test_description_has_not_marker(self, tool_name):
        """Each tool description must contain 'NOT:'."""
        tools = _get_tools()
        assert tool_name in tools, f"Tool '{tool_name}' not registered in mcp"
        tool = tools[tool_name]
        desc = tool.description or ""
        assert "NOT:" in desc, (
            f"Tool '{tool_name}' description missing 'NOT:' marker. "
            f"Got: {desc[:100]!r}"
        )

    @pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
    def test_description_has_sibling_marker(self, tool_name):
        """Each tool description must contain 'SIBLING:'."""
        tools = _get_tools()
        assert tool_name in tools, f"Tool '{tool_name}' not registered in mcp"
        tool = tools[tool_name]
        desc = tool.description or ""
        assert "SIBLING:" in desc, (
            f"Tool '{tool_name}' description missing 'SIBLING:' marker. "
            f"Got: {desc[:100]!r}"
        )


class TestToolParameters:
    """QUAL-02: Every non-ctx parameter must have a 'description' key in its inputSchema property."""

    @pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
    def test_all_non_ctx_params_have_description(self, tool_name):
        """Every parameter except 'ctx' must include a 'description' in its schema."""
        tools = _get_tools()
        assert tool_name in tools, f"Tool '{tool_name}' not registered in mcp"
        tool = tools[tool_name]

        params = tool.parameters
        if not params:
            return  # No parameters — trivially passes

        props = params.get("properties", {})
        if not props:
            return  # No properties — trivially passes

        for param_key, param_val in props.items():
            if param_key == "ctx":
                continue  # ctx is injected by FastMCP — must NOT appear in schema
            assert "description" in param_val, (
                f"Tool '{tool_name}' parameter '{param_key}' missing 'description' "
                f"in inputSchema. Got keys: {list(param_val.keys())}"
            )

    @pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
    def test_ctx_not_in_input_schema(self, tool_name):
        """ctx must NOT appear in inputSchema.properties (FastMCP injects it automatically)."""
        tools = _get_tools()
        assert tool_name in tools, f"Tool '{tool_name}' not registered in mcp"
        tool = tools[tool_name]

        params = tool.parameters
        if not params:
            return

        props = params.get("properties", {})
        assert "ctx" not in props, (
            f"Tool '{tool_name}' has 'ctx' in inputSchema.properties — "
            f"ctx must be left bare (not wrapped in Annotated) so FastMCP excludes it."
        )


# ---------------------------------------------------------------------------
# QUAL-03 helpers — mock clients and sample data for list function tests
# ---------------------------------------------------------------------------


def _make_invoice_mock_client(items: list[dict]) -> Mock:
    """Create a mock client for sales invoices (uses client.list_invoices)."""
    mock_client = Mock(spec=KledoAPIClient)
    mock_client.list_invoices = AsyncMock(return_value={"data": {"data": items}})
    return mock_client


def _make_get_mock_client(items: list[dict]) -> Mock:
    """Create a mock client for endpoints that use client.get()."""
    mock_client = Mock(spec=KledoAPIClient)
    mock_client.get = AsyncMock(return_value={"data": {"data": items}})
    return mock_client


def _make_contacts_mock_client(items: list[dict]) -> Mock:
    """Create a mock client for contacts (uses client.list_contacts)."""
    mock_client = Mock(spec=KledoAPIClient)
    mock_client.list_contacts = AsyncMock(return_value={"data": {"data": items}})
    return mock_client


def _make_products_mock_client(items: list[dict]) -> Mock:
    """Create a mock client for products (uses client.list_products)."""
    mock_client = Mock(spec=KledoAPIClient)
    mock_client.list_products = AsyncMock(return_value={"data": {"data": items}})
    return mock_client


SAMPLE_INVOICE = {
    "id": 101,
    "ref_number": "INV/TEST/001",
    "contact": {"name": "Customer A", "company": "PT Test Co"},
    "trans_date": "2024-01-01",
    "due_date": "2024-01-31",
    "amount_after_tax": 1000000,
    "subtotal": 900000,
    "total_tax": 100000,
    "due": 1000000,
    "status_id": 1,
}

SAMPLE_PURCHASE_INVOICE = {
    "id": 601,
    "ref_number": "PI/TEST/001",
    "contact": {"name": "Vendor A", "company": "PT Vendor Co"},
    "trans_date": "2024-01-01",
    "due_date": "2024-01-31",
    "amount_after_tax": 2000000,
    "subtotal": 1800000,
    "total_tax": 200000,
    "due": 2000000,
    "status_id": 1,
}

SAMPLE_ORDER = {
    "id": 201,
    "ref_number": "SO/TEST/001",
    "contact": {"name": "Customer B"},
    "trans_date": "2024-01-01",
    "amount_after_tax": 500000,
    "subtotal": 450000,
    "status_id": 5,
}

SAMPLE_PURCHASE_ORDER = {
    "id": 701,
    "ref_number": "PO/TEST/001",
    "contact": {"name": "Vendor B"},
    "trans_date": "2024-01-01",
    "amount_after_tax": 750000,
    "subtotal": 675000,
    "status_id": 5,
}

SAMPLE_DELIVERY = {
    "id": 301,
    "ref_number": "DO/TEST/001",
    "contact": {"name": "Customer C"},
    "trans_date": "2024-01-01",
    "status_id": 5,
    "shipping_company": {"name": "JNE"},
}

SAMPLE_CONTACT = {
    "id": 401,
    "name": "Contact D",
    "company": "PT Contact Co",
    "email": "contact@example.com",
    "phone": "08123456789",
    "type_name": "Customer",
}

SAMPLE_PRODUCT = {
    "id": 501,
    "name": "Product E",
    "code": "SKU-001",
    "price": 100000,
    "qty": 50,
    "category_name": "Paint",
}


class TestListIDExposure:
    """QUAL-03 (ID presence): List function outputs must contain '**ID**:' per item."""

    async def test_invoice_list_exposes_id(self) -> None:
        """Sales invoice list output must include '**ID**:' for each item."""
        mock_client = _make_invoice_mock_client([SAMPLE_INVOICE])
        result = await invoices._list_sales_invoices({"per_page": 3}, mock_client)
        assert "**ID**:" in result, (
            f"invoice_list (sales) output does not contain '**ID**:'. "
            f"Output snippet: {result[:500]!r}"
        )

    async def test_purchase_invoice_list_exposes_id(self) -> None:
        """Purchase invoice list output must include '**ID**:' for each item."""
        mock_client = _make_get_mock_client([SAMPLE_PURCHASE_INVOICE])
        result = await invoices._list_purchase_invoices({"per_page": 3}, mock_client)
        assert "**ID**:" in result, (
            f"invoice_list (purchase) output does not contain '**ID**:'. "
            f"Output snippet: {result[:500]!r}"
        )

    async def test_order_list_exposes_id(self) -> None:
        """Sales order list output must include '**ID**:' for each item."""
        mock_client = _make_get_mock_client([SAMPLE_ORDER])
        result = await orders._list_sales_orders({"per_page": 3}, mock_client)
        assert "**ID**:" in result, (
            f"order_list (sales) output does not contain '**ID**:'. "
            f"Output snippet: {result[:500]!r}"
        )

    async def test_purchase_order_list_exposes_id(self) -> None:
        """Purchase order list output must include '**ID**:' for each item."""
        mock_client = _make_get_mock_client([SAMPLE_PURCHASE_ORDER])
        result = await orders._list_purchase_orders({"per_page": 3}, mock_client)
        assert "**ID**:" in result, (
            f"order_list (purchase) output does not contain '**ID**:'. "
            f"Output snippet: {result[:500]!r}"
        )

    async def test_delivery_list_exposes_id(self) -> None:
        """Delivery list output must include '**ID**:' for each item."""
        mock_client = _make_get_mock_client([SAMPLE_DELIVERY])
        result = await deliveries._list_deliveries({"per_page": 3}, mock_client)
        assert "**ID**:" in result, (
            f"delivery_list output does not contain '**ID**:'. "
            f"Output snippet: {result[:500]!r}"
        )

    async def test_contact_list_exposes_id(self) -> None:
        """Contact list output must include '**ID**:' for each item."""
        mock_client = _make_contacts_mock_client([SAMPLE_CONTACT])
        result = await contacts._list_contacts({"per_page": 3}, mock_client)
        assert "**ID**:" in result, (
            f"contact_list output does not contain '**ID**:'. "
            f"Output snippet: {result[:500]!r}"
        )

    async def test_product_list_exposes_id(self) -> None:
        """Product list output must include '**ID**:' for each item."""
        mock_client = _make_products_mock_client([SAMPLE_PRODUCT])
        result = await products._list_products({"per_page": 3}, mock_client)
        assert "**ID**:" in result, (
            f"product_list output does not contain '**ID**:'. "
            f"Output snippet: {result[:500]!r}"
        )


class TestTruncationConsistency:
    """QUAL-03 (truncation at 20): Contacts and products must truncate at 20, not 30."""

    async def test_contacts_truncate_at_20(self) -> None:
        """Contacts list must truncate at 20 items and report 'and 5 more' for 25 items."""
        items = [
            {
                "id": 400 + i,
                "name": f"Contact {i}",
                "company": f"Company {i}",
                "email": f"contact{i}@example.com",
                "phone": f"0812{i:07d}",
                "type_name": "Customer",
            }
            for i in range(1, 26)
        ]
        mock_client = _make_contacts_mock_client(items)
        result = await contacts._list_contacts({"per_page": 25}, mock_client)
        assert "and 5 more" in result, (
            f"contacts._list_contacts with 25 items should show 'and 5 more' "
            f"(truncating at 20), but output is: {result[-300:]!r}"
        )

    async def test_products_truncate_at_20(self) -> None:
        """Products list must truncate at 20 items and report 'and 5 more' for 25 items."""
        items = [
            {
                "id": 500 + i,
                "name": f"Product {i}",
                "code": f"SKU-{i:03d}",
                "price": 10000 * i,
                "qty": 10 * i,
                "category_name": "Paint",
            }
            for i in range(1, 26)
        ]
        mock_client = _make_products_mock_client(items)
        result = await products._list_products({"per_page": 25}, mock_client)
        assert "and 5 more" in result, (
            f"products._list_products with 25 items should show 'and 5 more' "
            f"(truncating at 20), but output is: {result[-300:]!r}"
        )
