"""
Kledo MCP Server — FastMCP 1.x implementation.

Phase 4 (tool-interface-migration): all 11 tool modules are now plain async
libraries. The old get_tools/handle_tool bridge (_TOOL_MODULES, _make_wrapper,
_register_tools) is replaced with 24 explicit @mcp.tool() decorated functions,
one per registered tool name. Each function reproduces the former dispatch logic
inline and passes (args, client) to the appropriate private implementation.

Tool names are preserved exactly from the Phase 3 bridge to avoid breaking
existing Claude Desktop configs and conversation history.
"""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from typing import Annotated

from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

if __package__:
    from .auth import KledoAuthenticator
    from .cache import KledoCache
    from .kledo_client import KledoAPIClient
    from .tools import (
        analytics,
        commission,
        contacts,
        deliveries,
        financial,
        invoices,
        orders,
        products,
        revenue,
        sales_analytics,
        utilities,
    )
    from .utils.logger import setup_logger
else:  # pragma: no cover — only executed when running server.py as a direct script
    src_dir = Path(__file__).parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from auth import KledoAuthenticator  # type: ignore[no-redef]
    from cache import KledoCache  # type: ignore[no-redef]
    from kledo_client import KledoAPIClient  # type: ignore[no-redef]
    from tools import (  # type: ignore[no-redef]
        analytics,
        commission,
        contacts,
        deliveries,
        financial,
        invoices,
        orders,
        products,
        revenue,
        sales_analytics,
        utilities,
    )
    from utils.logger import setup_logger  # type: ignore[no-redef]


load_dotenv()
setup_logger(log_level=os.getenv("LOG_LEVEL", "INFO"), log_file=os.getenv("LOG_FILE"))


@dataclass
class AppContext:
    """Application state yielded by the FastMCP lifespan hook."""

    client: KledoAPIClient


INSTRUCTIONS = (
    "Read-only Kledo accounting MCP server for a paint distribution company. "
    "All tools are safe to call without user confirmation. "
    "\n\n"
    "INVOICE STATUS CODES: "
    "status_id=1 means Unpaid (Belum Dibayar), "
    "status_id=2 means Partially Paid (Dibayar Sebagian), "
    "status_id=3 means Paid in full (Lunas). "
    "\n\n"
    "COMMISSION FORMULA: commission is calculated on the pre-tax subtotal "
    "(NOT the post-tax total) of PAID invoices only (status_id=3). "
    "Formula: amount_after_tax = subtotal + total_tax. "
    "Commission base = subtotal (before tax). "
    "\n\n"
    "ID LOOKUP GUIDANCE: invoice, contact, product, and order IDs are NOT guessable. "
    "Always call a list tool (invoice_list, contact_list, product_list, order_list) "
    "FIRST to discover IDs, then call the corresponding detail tool. "
    "Do not fabricate numeric IDs. "
    "\n\n"
    "CURRENCY: all amounts are in Indonesian Rupiah (IDR). Format large numbers "
    "with thousands separators when presenting results to the user. "
    "\n\n"
    "LANGUAGE: tool descriptions and arguments accept both English and Indonesian "
    "(bilingual). Common terms: piutang=receivable, omzet=sales, lunas=paid, "
    "belum dibayar=unpaid."
)


async def _build_client() -> KledoAPIClient:
    """
    Build and authenticate a KledoAPIClient.

    Extracted from the old module-level `initialize_client()` singleton — the
    lifespan hook calls this once per server lifetime. Auth priority:
    KLEDO_API_KEY (recommended) > KLEDO_EMAIL + KLEDO_PASSWORD (legacy).

    Raises:
        ValueError: if no valid credentials are in the environment or login fails.
    """
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    app_client_type = os.getenv("KLEDO_APP_CLIENT", "android")

    api_key = os.getenv("KLEDO_API_KEY")
    if api_key:
        logger.info("Using API key authentication (recommended)")
        auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    else:
        email = os.getenv("KLEDO_EMAIL")
        password = os.getenv("KLEDO_PASSWORD")
        if not email or not password:
            raise ValueError(
                "Must provide either KLEDO_API_KEY (recommended) or "
                "(KLEDO_EMAIL and KLEDO_PASSWORD) in environment variables"
            )
        logger.warning(
            "Using email/password authentication (legacy). "
            "Consider using KLEDO_API_KEY for better security."
        )
        auth = KledoAuthenticator(
            base_url=base_url,
            email=email,
            password=password,
            app_client=app_client_type,
        )

    logger.info("Performing initial authentication...")
    if not await auth.login():
        raise ValueError("Failed to authenticate with Kledo API")

    cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_config_path = Path(__file__).parent.parent / "config" / "cache_config.yaml"
    cache = KledoCache(
        config_path=str(cache_config_path) if cache_config_path.exists() else None,
        enabled=cache_enabled,
    )

    endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(endpoints_config_path) if endpoints_config_path.exists() else None,
    )

    logger.info("Kledo API client initialized successfully")
    return client


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Initialize the KledoAPIClient on server start and tear it down on shutdown.

    Replaces the old `initialize_client()` module-level singleton. The yielded
    AppContext is accessible from tool handlers via
    `ctx.request_context.lifespan_context.client`.
    """
    logger.info("Starting Kledo MCP Server lifespan...")
    client = await _build_client()
    try:
        yield AppContext(client=client)
    finally:
        if hasattr(client, "_http_client") and getattr(client, "_http_client", None):
            try:
                await client._http_client.aclose()
                logger.info("Closed KledoAPIClient HTTP session")
            except Exception as e:
                logger.warning(f"Error closing HTTP session: {e}")
        logger.info("Kledo MCP Server lifespan ended")


mcp = FastMCP(
    os.getenv("MCP_SERVER_NAME", "kledo-crm"),
    instructions=INSTRUCTIONS,
    lifespan=lifespan,
)

# Applied to every @mcp.tool() registration — signals to the MCP client that
# all tools are safe, read-only, and may reference resources not in the context.
_READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


def _recovery_hint(tool_name: str, error: Exception) -> str:
    """
    Return a context-aware recovery hint for Claude based on the error signal.

    SECURITY: must NOT echo API key values or other secrets. The caller is
    responsible for stripping env-var values from the error string before
    including them in the outer ToolError message — this function only
    produces the advisory hint.
    """
    error_str = str(error).lower()
    if "401" in error_str or "unauthorized" in error_str or "invalid api key" in error_str:
        return "Check that KLEDO_API_KEY is set correctly in your .env file."
    if "403" in error_str or "forbidden" in error_str:
        return (
            "The API key lacks permission for this resource. Verify scopes in the Kledo dashboard."
        )
    if "404" in error_str or "not found" in error_str:
        return (
            f"The requested resource was not found. "
            f"Call a list tool first (invoice_list, contact_list, etc.) to discover valid IDs "
            f"before calling {tool_name} again."
        )
    if "timeout" in error_str or "connect" in error_str or "network" in error_str:
        return "Kledo API is unreachable. Check KLEDO_BASE_URL and your network connection."
    if "rate" in error_str and "limit" in error_str:
        return "Kledo API rate limit hit. Wait a few seconds and retry."
    return "Check your environment configuration with `kledo-mcp --test`."


def _scrub_secrets(message: str) -> str:
    """Remove KLEDO_API_KEY value from error messages before returning them to Claude."""
    api_key = os.getenv("KLEDO_API_KEY")
    if api_key and len(api_key) >= 8 and api_key in message:
        return message.replace(api_key, "***REDACTED***")
    return message


# ---------------------------------------------------------------------------
# Financial tools (3)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="financial_activity",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches the team activity log from Kledo — actions performed by each user "
        "(creates, edits, deletes) within an optional date range. "
        "RETURNS: A chronological list of user actions, each with username, action type, "
        "affected document reference, and timestamp. No numeric IDs exposed (not needed — "
        "this is an audit log, not a navigable list). "
        "NOT: Does not return financial totals or invoice details — use financial_summary "
        "for aggregated figures. "
        "SIBLING: Use financial_summary for sales/purchase totals grouped by customer or "
        "sales rep; use invoice_list to browse individual invoices."
    ),
)
async def _tool_financial_activity(
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase (e.g. 'bulan ini'). Default: none (all time)."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Fetch team activity log from Kledo."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"date_from": date_from, "date_to": date_to}
    try:
        return await financial._activity_team_report(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'financial_activity' failed: {scrubbed}. {_recovery_hint('financial_activity', e)}"
        ) from e


@mcp.tool(
    name="financial_summary",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches an aggregated financial summary from Kledo, grouping sales or "
        "purchase totals by customer or by sales representative for a date range. "
        "RETURNS: Grouped rows with contact or rep name, total invoice amount, total paid, "
        "and outstanding balance. Amounts in IDR. "
        "NOT: Does not list individual invoices — use invoice_list for that. Does not "
        "calculate commission — use commission_report for that. "
        "SIBLING: Use invoice_list to see individual invoice rows; use commission_report "
        "to calculate per-rep commission from paid invoice subtotals."
    ),
)
async def _tool_financial_summary(
    type: Annotated[
        str,
        Field(description="Direction: 'sales' (default) or 'purchase'."),
    ] = "sales",
    group_by: Annotated[
        str,
        Field(description="Grouping: 'customer' (default) or 'sales_rep'."),
    ] = "customer",
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Fetch aggregated financial summary grouped by customer or sales rep."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"type": type, "group_by": group_by, "date_from": date_from, "date_to": date_to}
    try:
        if type == "purchase":
            return await financial._purchase_summary(args, app_ctx.client)
        elif group_by == "sales_rep":
            return await financial._sales_by_person(args, app_ctx.client)
        else:
            return await financial._sales_summary(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'financial_summary' failed: {scrubbed}. {_recovery_hint('financial_summary', e)}"
        ) from e


@mcp.tool(
    name="financial_balances",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches current bank account balances for all accounts registered in Kledo. "
        "RETURNS: A list of accounts — each with account name, account number, bank name, "
        "and current balance in IDR. No date filtering — always reflects the current state. "
        "NOT: Does not show transaction history — this is a snapshot of balances only. "
        "SIBLING: Use financial_activity to see recent transactions; use financial_summary "
        "for aggregated revenue/cost figures."
    ),
)
async def _tool_financial_balances(ctx: Context = None) -> str:
    """Fetch current bank account balances for all Kledo accounts."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        return await financial._bank_balances({}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'financial_balances' failed: {scrubbed}. {_recovery_hint('financial_balances', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Invoice tools (3)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="invoice_list",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Lists Kledo sales or purchase invoices filtered by date range, customer, "
        "payment status, or keyword. "
        "RETURNS: Up to per_page invoice rows — each includes invoice_id (integer, use this "
        "in invoice_get), ref_number, customer name, invoice date, subtotal (pre-tax), "
        "tax amount, gross total, outstanding due, and payment status label. Shows up to 20 "
        "rows; omitted count is stated explicitly ('... and N more invoices'). "
        "NOT: Does not return line-item detail — call invoice_get with invoice_id for items "
        "and product breakdown. "
        "SIBLING: Use invoice_get to fetch a single invoice by invoice_id; use "
        "invoice_summarize for aggregate totals (by_customer, by_vendor) without individual rows."
    ),
)
async def _tool_invoice_list(
    type: Annotated[
        str,
        Field(description="Invoice direction: 'sales' (default) or 'purchase'."),
    ] = "sales",
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase (e.g. 'bulan ini', 'januari 2026'). Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none. Pair with date_from for a range."),
    ] = None,
    contact_id: Annotated[
        int | None,
        Field(description="Filter by customer: numeric contact_id from contact_list. Default: none (all customers)."),
    ] = None,
    status_id: Annotated[
        int | None,
        Field(description="Filter by payment status: 1=Unpaid, 2=Partially Paid, 3=Paid. Default: none (all statuses)."),
    ] = None,
    search: Annotated[
        str | None,
        Field(description="Keyword search on ref_number or customer name. Default: none."),
    ] = None,
    per_page: Annotated[
        int,
        Field(description="Max rows to fetch from Kledo. Integer 1-200. Default: 50. Display is capped at 20."),
    ] = 50,
    ctx: Context = None,
) -> str:
    """List sales or purchase invoices with optional filters."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {
        "type": type,
        "date_from": date_from,
        "date_to": date_to,
        "contact_id": contact_id,
        "status_id": status_id,
        "search": search,
        "per_page": per_page,
    }
    try:
        if type == "purchase":
            return await invoices._list_purchase_invoices(args, app_ctx.client)
        else:
            return await invoices._list_sales_invoices(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'invoice_list' failed: {scrubbed}. {_recovery_hint('invoice_list', e)}"
        ) from e


@mcp.tool(
    name="invoice_get",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches full detail for a single invoice from Kledo by its numeric ID. "
        "RETURNS: Invoice header (ref_number, date, customer, status, subtotal, tax, total, "
        "outstanding) plus all line items (product name, quantity, unit price, discount, "
        "subtotal per line). "
        "NOT: Does not list multiple invoices — use invoice_list to browse and discover "
        "invoice_id values. "
        "SIBLING: Use invoice_list first to find invoice_id; use invoice_summarize for "
        "aggregate totals without individual line items."
    ),
)
async def _tool_invoice_get(
    invoice_id: Annotated[
        int,
        Field(description="Numeric invoice ID from invoice_list output. Required."),
    ],
    ctx: Context = None,
) -> str:
    """Fetch full detail for a single invoice by numeric ID."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        return await invoices._get_invoice_detail({"invoice_id": invoice_id}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'invoice_get' failed: {scrubbed}. {_recovery_hint('invoice_get', e)}"
        ) from e


@mcp.tool(
    name="invoice_summarize",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Returns aggregated invoice totals from Kledo — overall totals, breakdown by "
        "customer, or breakdown by vendor — without listing individual rows. "
        "RETURNS: view='totals' -> grand total, paid, outstanding, tax totals; "
        "view='by_customer' -> per-customer outstanding sorted descending; "
        "view='by_vendor' -> per-vendor purchase totals. Amounts in IDR. "
        "NOT: Does not return individual invoice rows or line items — use invoice_list or "
        "invoice_get for that. "
        "SIBLING: Use invoice_list to browse individual invoices; use invoice_get for "
        "line-item detail on a specific invoice."
    ),
)
async def _tool_invoice_summarize(
    view: Annotated[
        str,
        Field(description="Summary mode: 'totals' (default, grand totals), 'by_customer' (per-customer outstanding), or 'by_vendor' (per-vendor purchases)."),
    ] = "totals",
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Return aggregated invoice totals without individual rows."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"view": view, "date_from": date_from, "date_to": date_to}
    try:
        if view == "by_customer":
            return await invoices._outstanding_by_customer(args, app_ctx.client)
        elif view == "by_vendor":
            return await invoices._outstanding_by_vendor(args, app_ctx.client)
        else:
            return await invoices._get_invoice_totals(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'invoice_summarize' failed: {scrubbed}. {_recovery_hint('invoice_summarize', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Order tools (2)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="order_list",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Lists Kledo sales or purchase orders filtered by date range or status. "
        "RETURNS: Up to per_page rows — each with order_id (use in order_get), ref_number, "
        "customer/vendor, date, total amount, and status. Shows up to 20; omitted count stated. "
        "NOT: Does not include order line items — use order_get for that. "
        "SIBLING: Use order_get with order_id for full line-item detail."
    ),
)
async def _tool_order_list(
    type: Annotated[
        str,
        Field(description="Order direction: 'sales' (default) or 'purchase'."),
    ] = "sales",
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    status_id: Annotated[
        int | None,
        Field(description="Filter by order status ID. Default: none (all statuses)."),
    ] = None,
    per_page: Annotated[
        int,
        Field(description="Max rows to fetch from Kledo. Integer 1-200. Default: 50. Display is capped at 20."),
    ] = 50,
    ctx: Context = None,
) -> str:
    """List sales or purchase orders with optional filters."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {
        "type": type,
        "date_from": date_from,
        "date_to": date_to,
        "status_id": status_id,
        "per_page": per_page,
    }
    try:
        if type == "purchase":
            return await orders._list_purchase_orders(args, app_ctx.client)
        elif type == "sales":
            return await orders._list_sales_orders(args, app_ctx.client)
        else:
            return await orders._list_orders(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'order_list' failed: {scrubbed}. {_recovery_hint('order_list', e)}"
        ) from e


@mcp.tool(
    name="order_get",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches full detail for a single order by its numeric ID. "
        "RETURNS: Order header (ref_number, customer/vendor, date, status, total) "
        "plus all line items (product name, quantity, unit price, subtotal per line). "
        "NOT: Does not list multiple orders — use order_list to find order_id. "
        "SIBLING: Use order_list first to discover order_id values."
    ),
)
async def _tool_order_get(
    order_id: Annotated[
        int,
        Field(description="Numeric order ID from order_list output. Required."),
    ],
    ctx: Context = None,
) -> str:
    """Fetch full detail for a single order by numeric ID."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        return await orders._get_order({"order_id": order_id}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'order_get' failed: {scrubbed}. {_recovery_hint('order_get', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Product tools (2)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="product_list",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Lists products in the Kledo product catalog, optionally filtered by "
        "name/code keyword. "
        "RETURNS: Up to per_page rows — each with product_id (use in product_get), product "
        "name, SKU code, unit, selling price, and optionally stock quantity. Shows up to 20; "
        "omitted count stated. "
        "NOT: Does not return purchase price or full supplier history — use product_get for that. "
        "SIBLING: Use product_get with product_id or sku for full product detail and pricing."
    ),
)
async def _tool_product_list(
    search: Annotated[
        str | None,
        Field(description="Keyword to filter by product name or SKU code. Default: none (all products)."),
    ] = None,
    include_inventory: Annotated[
        bool,
        Field(description="If True, include current stock quantity for each product. Default: False."),
    ] = False,
    per_page: Annotated[
        int,
        Field(description="Max rows to fetch from Kledo. Integer 1-200. Default: 50. Display is capped at 20."),
    ] = 50,
    ctx: Context = None,
) -> str:
    """List products with optional keyword filter and inventory quantities."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"search": search, "include_inventory": include_inventory, "per_page": per_page}
    try:
        return await products._list_products(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'product_list' failed: {scrubbed}. {_recovery_hint('product_list', e)}"
        ) from e


@mcp.tool(
    name="product_get",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches full detail for a single product by numeric ID or SKU code. "
        "RETURNS: Full product record — name, code, description, unit, selling price, "
        "purchase price, stock level, category. "
        "NOT: Does not list multiple products — use product_list to browse and find product_id. "
        "SIBLING: Use product_list to discover product_id or SKU before calling this tool."
    ),
)
async def _tool_product_get(
    product_id: Annotated[
        int | None,
        Field(description="Numeric product ID from product_list output. Use this or sku, not both. Default: none."),
    ] = None,
    sku: Annotated[
        str | None,
        Field(description="SKU/product code string from product_list output. Use this or product_id, not both. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Fetch full product detail by ID or SKU code."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        if sku:
            return await products._search_by_sku({"sku": sku}, app_ctx.client)
        return await products._get_product_detail({"product_id": product_id}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'product_get' failed: {scrubbed}. {_recovery_hint('product_get', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Contact tools (2)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="contact_list",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Lists contacts (customers and/or vendors) in Kledo, optionally filtered by "
        "name or contact type. "
        "RETURNS: Up to per_page rows — each with contact_id (use in contact_get), display "
        "name, contact type (customer/vendor), phone, and email. Shows up to 20; omitted "
        "count stated. "
        "NOT: Does not return transaction history — use contact_get with "
        "include_transactions=True for that. "
        "SIBLING: Use contact_get with contact_id for full contact detail and optional "
        "transaction history."
    ),
)
async def _tool_contact_list(
    search: Annotated[
        str | None,
        Field(description="Keyword to filter by contact name or email. Default: none (all contacts)."),
    ] = None,
    type: Annotated[
        str | None,
        Field(description="Contact type filter: 'customer', 'vendor', or None (all). Default: none."),
    ] = None,
    per_page: Annotated[
        int,
        Field(description="Max rows to fetch from Kledo. Integer 1-200. Default: 50. Display is capped at 20."),
    ] = 50,
    ctx: Context = None,
) -> str:
    """List contacts with optional name/type filter."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"search": search, "type": type, "per_page": per_page}
    try:
        return await contacts._list_contacts(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'contact_list' failed: {scrubbed}. {_recovery_hint('contact_list', e)}"
        ) from e


@mcp.tool(
    name="contact_get",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches full detail for a single contact by numeric ID, optionally including "
        "their transaction history. "
        "RETURNS: Contact record (name, type, phone, email, address, tax ID); if "
        "include_transactions=True, also returns recent invoices and payments. "
        "NOT: Does not list all contacts — use contact_list first to find contact_id. "
        "SIBLING: Use contact_list to discover contact_id; use invoice_list with contact_id "
        "to filter invoices for a specific customer."
    ),
)
async def _tool_contact_get(
    contact_id: Annotated[
        int | None,
        Field(description="Numeric contact ID from contact_list output. Required."),
    ] = None,
    include_transactions: Annotated[
        bool,
        Field(description="If True, include recent invoices and payment history for this contact. Default: False."),
    ] = False,
    ctx: Context = None,
) -> str:
    """Fetch full contact detail by ID, optionally with transaction history."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        if include_transactions:
            return await contacts._get_contact_transactions(
                {"contact_id": contact_id}, app_ctx.client
            )
        return await contacts._get_contact_detail({"contact_id": contact_id}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'contact_get' failed: {scrubbed}. {_recovery_hint('contact_get', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Delivery tools (2)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="delivery_list",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Lists delivery orders from Kledo, optionally filtered by date range or status. "
        "RETURNS: Up to per_page rows — each with delivery_id (use in delivery_get), "
        "ref_number, customer, delivery date, and status (pending/shipped/done). Shows up to "
        "20; omitted count stated. status='pending' returns only unshipped orders. "
        "NOT: Does not include delivery line items — use delivery_get for that. "
        "SIBLING: Use delivery_get with delivery_id for full line-item detail on a specific "
        "delivery."
    ),
)
async def _tool_delivery_list(
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    status: Annotated[
        str | None,
        Field(description="Status filter: 'pending' (unshipped only), 'shipped', 'done', or None (all). Default: none."),
    ] = None,
    per_page: Annotated[
        int,
        Field(description="Max rows to fetch from Kledo. Integer 1-200. Default: 50. Display is capped at 20."),
    ] = 50,
    ctx: Context = None,
) -> str:
    """List delivery orders with optional date/status filter."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"date_from": date_from, "date_to": date_to, "status": status, "per_page": per_page}
    try:
        if status == "pending":
            return await deliveries._get_pending_deliveries(args, app_ctx.client)
        return await deliveries._list_deliveries(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'delivery_list' failed: {scrubbed}. {_recovery_hint('delivery_list', e)}"
        ) from e


@mcp.tool(
    name="delivery_get",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches full detail for a single delivery order by its numeric ID. "
        "RETURNS: Delivery header (ref_number, customer, date, status) plus all line items "
        "(product name, quantity, unit). "
        "NOT: Does not list multiple deliveries — use delivery_list to find delivery_id. "
        "SIBLING: Use delivery_list first to discover delivery_id values."
    ),
)
async def _tool_delivery_get(
    delivery_id: Annotated[
        int,
        Field(description="Numeric delivery ID from delivery_list output. Required."),
    ],
    ctx: Context = None,
) -> str:
    """Fetch full detail for a single delivery order by numeric ID."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        return await deliveries._get_delivery_detail({"delivery_id": delivery_id}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'delivery_get' failed: {scrubbed}. {_recovery_hint('delivery_get', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Utility tools (2)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="utility_cache",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Inspects or clears the in-memory API response cache that reduces Kledo API "
        "round-trips. "
        "RETURNS: action='stats' -> hit count, miss count, cached key count, TTL config per "
        "category; action='clear' -> confirmation of cleared entries. "
        "NOT: Does not affect Kledo data — only affects the local cache layer. "
        "SIBLING: No direct sibling — use utility_test_connection to verify the Kledo API "
        "itself is reachable."
    ),
)
async def _tool_utility_cache(
    action: Annotated[
        str,
        Field(description="Cache operation: 'stats' (default, show cache metrics) or 'clear' (flush all cached entries)."),
    ] = "stats",
    ctx: Context = None,
) -> str:
    """Inspect or clear the local API response cache."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"action": action}
    try:
        if action == "clear":
            return await utilities._clear_cache(args, app_ctx.client)
        return await utilities._get_cache_stats(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'utility_cache' failed: {scrubbed}. {_recovery_hint('utility_cache', e)}"
        ) from e


@mcp.tool(
    name="utility_test_connection",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Tests the connection to the Kledo API and verifies authentication credentials "
        "are valid. "
        "RETURNS: Connection status (OK/FAIL), authentication method in use (API key or "
        "email/password), and Kledo API base URL. "
        "NOT: Does not fetch any business data — this is a diagnostic tool only. "
        "SIBLING: Use utility_cache to inspect the cache layer; use any other tool after "
        "confirming connection is OK."
    ),
)
async def _tool_utility_test_connection(ctx: Context = None) -> str:
    """Test Kledo API connectivity and authentication status."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        return await utilities._test_connection({}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'utility_test_connection' failed: {scrubbed}. "
            f"{_recovery_hint('utility_test_connection', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Sales analytics tools (2)
# Note: sales_analytics module uses reversed parameter order (client, args)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="sales_rep_report",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches a detailed sales performance report for one or all sales "
        "representatives from Kledo invoices. "
        "RETURNS: Per-rep breakdown of invoice count, total sales (gross and net), and paid "
        "amount for the period; filterable by sales_rep_id from sales_rep_list. "
        "NOT: Does not calculate commission — use commission_report for that; does not list "
        "individual invoices. "
        "SIBLING: Use sales_rep_list to discover sales_rep_id; use commission_report to "
        "calculate commission based on paid subtotals."
    ),
)
async def _tool_sales_rep_report(
    period: Annotated[
        str | None,
        Field(description="Time period shorthand: e.g. '2026-01' (month), '2026-Q1' (quarter), '2026' (year). Default: none (use date_from/date_to instead)."),
    ] = None,
    sales_rep_id: Annotated[
        int | None,
        Field(description="Numeric sales rep ID from sales_rep_list. Default: none (report all reps)."),
    ] = None,
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Fetch sales performance report for one or all sales reps."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {
        "period": period,
        "sales_rep_id": sales_rep_id,
        "date_from": date_from,
        "date_to": date_to,
    }
    try:
        return await sales_analytics._sales_rep_revenue_report(app_ctx.client, args)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'sales_rep_report' failed: {scrubbed}. {_recovery_hint('sales_rep_report', e)}"
        ) from e


@mcp.tool(
    name="sales_rep_list",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Lists all active sales representatives and their paid invoice counts within "
        "an optional date range. "
        "RETURNS: Each rep's display name, sales_rep_id (use in sales_rep_report and "
        "commission_report), and count of paid invoices (status_id=3) in the period. "
        "NOT: Does not return invoice amounts or commission figures — use sales_rep_report "
        "or commission_report for that. "
        "SIBLING: Use sales_rep_report for detailed per-rep revenue breakdown; use "
        "commission_report for commission calculation."
    ),
)
async def _tool_sales_rep_list(
    date_from: Annotated[
        str | None,
        Field(description="Start date for paid invoice count. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date for paid invoice count. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """List all active sales representatives with paid invoice counts."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"date_from": date_from, "date_to": date_to}
    try:
        return await sales_analytics._sales_rep_list(app_ctx.client, args)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'sales_rep_list' failed: {scrubbed}. {_recovery_hint('sales_rep_list', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Revenue tools (3)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="revenue_summary",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches a high-level revenue summary for a date range — total invoiced, total "
        "paid, outstanding, and per-customer breakdown. "
        "RETURNS: Grand totals (gross revenue, paid, outstanding, tax) plus top-customer rows "
        "each with customer name, contact_id, gross sales, and amount paid. All amounts IDR. "
        "NOT: Does not list individual invoices — use invoice_list for that. Does not rank "
        "customers by revenue — use revenue_ranking for that. "
        "SIBLING: Use revenue_ranking for sorted customer ranking; use invoice_list with "
        "status_id=3 to see paid invoices only."
    ),
)
async def _tool_revenue_summary(
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Fetch high-level revenue summary for a date range."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"date_from": date_from, "date_to": date_to}
    try:
        await ctx.report_progress(0, 3)
        result = await revenue._revenue_summary(args, app_ctx.client)
        await ctx.report_progress(3, 3)
        return result
    except ToolError:
        raise
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'revenue_summary' failed: {scrubbed}. {_recovery_hint('revenue_summary', e)}"
        ) from e


@mcp.tool(
    name="revenue_receivables",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Fetches the accounts receivable report from Kledo in three views: flat list, "
        "aging buckets, or concentration analysis. "
        "RETURNS: view='list' -> outstanding invoice rows with customer, due date, and amount; "
        "view='aging' -> amounts grouped by age (current, 30d, 60d, 90d+); "
        "view='concentration' -> top customers by share of total outstanding (with contact_id). "
        "NOT: Does not show paid invoices — filters to outstanding only. Does not list "
        "individual line items. "
        "SIBLING: Use invoice_list with status_id=1 for unpaid invoices; use revenue_summary "
        "for a combined paid/outstanding overview."
    ),
)
async def _tool_revenue_receivables(
    view: Annotated[
        str,
        Field(description="Report view: 'list' (default, outstanding rows), 'aging' (age buckets), or 'concentration' (top customers by share)."),
    ] = "list",
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Fetch accounts receivable report in list, aging, or concentration view."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"view": view, "date_from": date_from, "date_to": date_to}
    try:
        if view == "aging":
            return await revenue._outstanding_aging_report(args, app_ctx.client)
        elif view == "concentration":
            return await revenue._customer_concentration_report(args, app_ctx.client)
        else:
            return await revenue._outstanding_receivables(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'revenue_receivables' failed: {scrubbed}. "
            f"{_recovery_hint('revenue_receivables', e)}"
        ) from e


@mcp.tool(
    name="revenue_ranking",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Ranks revenue from Kledo by customer or by calendar day for a date range. "
        "RETURNS: group_by='customer' -> customers ranked by gross sales, each with "
        "contact_id, name, invoice count, and total; group_by='day' -> daily revenue totals "
        "with date and amount in IDR. "
        "NOT: Does not filter by payment status — includes all invoices. Does not show "
        "per-product breakdown. "
        "SIBLING: Use revenue_summary for grand totals; use revenue_receivables for "
        "outstanding-only analysis."
    ),
)
async def _tool_revenue_ranking(
    group_by: Annotated[
        str,
        Field(description="Ranking dimension: 'customer' (default, sorted by gross sales) or 'day' (daily totals)."),
    ] = "customer",
    date_from: Annotated[
        str | None,
        Field(description="Start date. Format: YYYY-MM-DD or Indonesian phrase. Default: none."),
    ] = None,
    date_to: Annotated[
        str | None,
        Field(description="End date. Format: YYYY-MM-DD. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Rank revenue by customer or day for a date range."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"group_by": group_by, "date_from": date_from, "date_to": date_to}
    try:
        if group_by == "day":
            return await revenue._revenue_daily_breakdown(args, app_ctx.client)
        else:
            return await revenue._customer_revenue_ranking(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'revenue_ranking' failed: {scrubbed}. {_recovery_hint('revenue_ranking', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Analytics tools (2)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="analytics_compare",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Compares a single metric (revenue or outstanding receivables) between two "
        "named periods. "
        "RETURNS: Side-by-side comparison of the two periods — each with total amount, change "
        "(absolute and percent), and direction (up/down/flat). Periods accept YYYY-MM, "
        "YYYY-QN, or plain year formats. "
        "NOT: Does not compare individual customers or products — this is aggregate only. "
        "SIBLING: Use revenue_summary or revenue_receivables for a single-period view; use "
        "analytics_targets for target vs. actual comparison."
    ),
)
async def _tool_analytics_compare(
    metric: Annotated[
        str,
        Field(description="Metric to compare: 'revenue' (default, gross invoice totals) or 'outstanding' (unpaid receivables)."),
    ] = "revenue",
    period_a: Annotated[
        str | None,
        Field(description="First comparison period. Format: YYYY-MM (month), YYYY-QN (quarter), or YYYY (year). Default: none."),
    ] = None,
    period_b: Annotated[
        str | None,
        Field(description="Second comparison period. Same format as period_a. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Compare a metric between two named periods."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"metric": metric, "period_a": period_a, "period_b": period_b}
    try:
        await ctx.report_progress(0, 2)
        if metric == "outstanding":
            result = await analytics._compare_outstanding(args, app_ctx.client)
        else:
            result = await analytics._compare_revenue(args, app_ctx.client)
        await ctx.report_progress(2, 2)
        return result
    except ToolError:
        raise
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'analytics_compare' failed: {scrubbed}. {_recovery_hint('analytics_compare', e)}"
        ) from e


@mcp.tool(
    name="analytics_targets",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Reports on, identifies underperformers against, or sets sales targets for "
        "sales representatives. "
        "RETURNS: action='report' -> all reps with their target, actual paid revenue, and "
        "achievement %; action='underperformers' -> only reps below 100% achievement; "
        "action='set' -> confirmation of stored target for the named sales_person and period. "
        "NOT: Does not pull targets from Kledo API — targets are stored locally in "
        "SalesTargetManager. Target setting (action='set') writes local state only. "
        "SIBLING: Use sales_rep_report for detailed per-rep revenue without targets; use "
        "commission_report for commission calculation."
    ),
)
async def _tool_analytics_targets(
    action: Annotated[
        str,
        Field(description="Operation: 'report' (default, all reps vs targets), 'underperformers' (below 100%), or 'set' (store a new target)."),
    ] = "report",
    period: Annotated[
        str | None,
        Field(description="Period for the target: e.g. '2026-01' (month) or '2026' (year). Default: none (current period)."),
    ] = None,
    sales_person: Annotated[
        str | None,
        Field(description="Sales rep display name for action='set'. Default: none (not used for report/underperformers)."),
    ] = None,
    target_amount: Annotated[
        float | None,
        Field(description="Target revenue amount in IDR for action='set'. Default: none."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Report on, identify underperformers, or set sales targets."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {
        "action": action,
        "period": period,
        "sales_person": sales_person,
        "target_amount": target_amount,
    }
    try:
        if action == "underperformers":
            return await analytics._underperformers(args, app_ctx.client)
        elif action == "set":
            return await analytics._set_target(args, app_ctx.client)
        else:
            return await analytics._target_achievement(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'analytics_targets' failed: {scrubbed}. {_recovery_hint('analytics_targets', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Commission tools (1)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="commission_report",
    annotations=_READ_ONLY,
    description=(
        "WHAT: Calculates commission for one or all sales representatives based on paid "
        "invoice subtotals (pre-tax) from Kledo. "
        "RETURNS: Per-rep rows with: rep name, paid invoice count, total pre-tax subtotal "
        "(commission base), flat rate applied, and commission amount. Omit sales_person_name "
        "to report all reps. Amounts in IDR. "
        "NOT: Does NOT use post-tax gross totals — commission base is always the pre-tax "
        "subtotal of status_id=3 invoices only. Does not write to Kledo. "
        "SIBLING: Use sales_rep_report for revenue figures without commission calculation; "
        "use analytics_targets to compare against set targets."
    ),
)
async def _tool_commission_report(
    period: Annotated[
        str | None,
        Field(description="Time period: e.g. '2026-01' (month), '2026-Q1' (quarter), '2026' (year). Default: none (current month)."),
    ] = None,
    sales_person_name: Annotated[
        str | None,
        Field(description="Sales rep display name to filter to a single rep. Default: none (report all reps)."),
    ] = None,
    flat_rate: Annotated[
        float | None,
        Field(description="Commission rate as a decimal fraction (e.g. 0.02 for 2%). Default: none (uses configured default rate)."),
    ] = None,
    ctx: Context = None,
) -> str:
    """Calculate commission from paid invoice subtotals for one or all reps."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"period": period, "sales_person_name": sales_person_name, "flat_rate": flat_rate}
    try:
        await ctx.report_progress(0, 2)
        if sales_person_name:
            result = await commission._commission_calculate(args, app_ctx.client)
        else:
            result = await commission._commission_report(args, app_ctx.client)
        await ctx.report_progress(2, 2)
        return result
    except ToolError:
        raise
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'commission_report' failed: {scrubbed}. {_recovery_hint('commission_report', e)}"
        ) from e


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point — runs the FastMCP server over stdio."""
    logger.info("Starting Kledo MCP Server (24 tools registered)...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
