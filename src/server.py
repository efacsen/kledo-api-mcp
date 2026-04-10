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

from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

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


@mcp.tool(name="financial_activity", annotations=_READ_ONLY)
async def _tool_financial_activity(
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """Get team activity report. Shows actions performed by each user."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"date_from": date_from, "date_to": date_to}
    try:
        return await financial._activity_team_report(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'financial_activity' failed: {scrubbed}. {_recovery_hint('financial_activity', e)}"
        ) from e


@mcp.tool(name="financial_summary", annotations=_READ_ONLY)
async def _tool_financial_summary(
    type: str = "sales",
    group_by: str = "customer",
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """Get financial summary. type='sales' or 'purchase'. group_by='customer' or 'sales_rep'."""
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


@mcp.tool(name="financial_balances", annotations=_READ_ONLY)
async def _tool_financial_balances(ctx: Context = None) -> str:
    """Get current bank account balances for all accounts."""
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


@mcp.tool(name="invoice_list", annotations=_READ_ONLY)
async def _tool_invoice_list(
    type: str = "sales",
    date_from: str | None = None,
    date_to: str | None = None,
    contact_id: int | None = None,
    status_id: int | None = None,
    search: str | None = None,
    per_page: int = 50,
    ctx: Context = None,
) -> str:
    """List invoices. type='sales' (default) or 'purchase'."""
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


@mcp.tool(name="invoice_get", annotations=_READ_ONLY)
async def _tool_invoice_get(invoice_id: int, ctx: Context = None) -> str:
    """Get full details for a single invoice by ID."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    try:
        return await invoices._get_invoice_detail({"invoice_id": invoice_id}, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'invoice_get' failed: {scrubbed}. {_recovery_hint('invoice_get', e)}"
        ) from e


@mcp.tool(name="invoice_summarize", annotations=_READ_ONLY)
async def _tool_invoice_summarize(
    view: str = "totals",
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """Summarize invoices. view='totals', 'by_customer', or 'by_vendor'."""
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


@mcp.tool(name="order_list", annotations=_READ_ONLY)
async def _tool_order_list(
    type: str = "sales",
    date_from: str | None = None,
    date_to: str | None = None,
    status_id: int | None = None,
    per_page: int = 50,
    ctx: Context = None,
) -> str:
    """List orders. type='sales' (default) or 'purchase'."""
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


@mcp.tool(name="order_get", annotations=_READ_ONLY)
async def _tool_order_get(order_id: int, ctx: Context = None) -> str:
    """Get full details for a single order by ID."""
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


@mcp.tool(name="product_list", annotations=_READ_ONLY)
async def _tool_product_list(
    search: str | None = None,
    include_inventory: bool = False,
    per_page: int = 50,
    ctx: Context = None,
) -> str:
    """List products. Optionally filter by search term or include inventory quantities."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"search": search, "include_inventory": include_inventory, "per_page": per_page}
    try:
        return await products._list_products(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'product_list' failed: {scrubbed}. {_recovery_hint('product_list', e)}"
        ) from e


@mcp.tool(name="product_get", annotations=_READ_ONLY)
async def _tool_product_get(
    product_id: int | None = None,
    sku: str | None = None,
    ctx: Context = None,
) -> str:
    """Get product details by ID or SKU code."""
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


@mcp.tool(name="contact_list", annotations=_READ_ONLY)
async def _tool_contact_list(
    search: str | None = None,
    type: str | None = None,
    per_page: int = 50,
    ctx: Context = None,
) -> str:
    """List contacts (customers and vendors). Optionally filter by name or type."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    args = {"search": search, "type": type, "per_page": per_page}
    try:
        return await contacts._list_contacts(args, app_ctx.client)
    except Exception as e:
        scrubbed = _scrub_secrets(str(e))
        raise ToolError(
            f"Tool 'contact_list' failed: {scrubbed}. {_recovery_hint('contact_list', e)}"
        ) from e


@mcp.tool(name="contact_get", annotations=_READ_ONLY)
async def _tool_contact_get(
    contact_id: int | None = None,
    include_transactions: bool = False,
    ctx: Context = None,
) -> str:
    """Get contact details and optionally their transaction history."""
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


@mcp.tool(name="delivery_list", annotations=_READ_ONLY)
async def _tool_delivery_list(
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    per_page: int = 50,
    ctx: Context = None,
) -> str:
    """List delivery orders. Optionally filter by date range or status."""
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


@mcp.tool(name="delivery_get", annotations=_READ_ONLY)
async def _tool_delivery_get(delivery_id: int, ctx: Context = None) -> str:
    """Get full details for a single delivery order by ID."""
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


@mcp.tool(name="utility_cache", annotations=_READ_ONLY)
async def _tool_utility_cache(
    action: str = "stats",
    ctx: Context = None,
) -> str:
    """Manage API cache. action='stats' (default) or 'clear'."""
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


@mcp.tool(name="utility_test_connection", annotations=_READ_ONLY)
async def _tool_utility_test_connection(ctx: Context = None) -> str:
    """Test the connection to the Kledo API and report authentication status."""
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


@mcp.tool(name="sales_rep_report", annotations=_READ_ONLY)
async def _tool_sales_rep_report(
    period: str | None = None,
    sales_rep_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """Get detailed sales performance report for a sales representative."""
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


@mcp.tool(name="sales_rep_list", annotations=_READ_ONLY)
async def _tool_sales_rep_list(
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """List all active sales representatives with their paid invoice counts."""
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


@mcp.tool(name="revenue_summary", annotations=_READ_ONLY)
async def _tool_revenue_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """Get revenue summary for a date range (total, paid, outstanding, by customer)."""
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


@mcp.tool(name="revenue_receivables", annotations=_READ_ONLY)
async def _tool_revenue_receivables(
    view: str = "list",
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """Get receivables report. view='list' (default), 'aging', or 'concentration'."""
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


@mcp.tool(name="revenue_ranking", annotations=_READ_ONLY)
async def _tool_revenue_ranking(
    group_by: str = "customer",
    date_from: str | None = None,
    date_to: str | None = None,
    ctx: Context = None,
) -> str:
    """Rank revenue. group_by='customer' (default) or 'day' for daily breakdown."""
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


@mcp.tool(name="analytics_compare", annotations=_READ_ONLY)
async def _tool_analytics_compare(
    metric: str = "revenue",
    period_a: str | None = None,
    period_b: str | None = None,
    ctx: Context = None,
) -> str:
    """Compare metrics between two periods. metric='revenue' or 'outstanding'."""
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


@mcp.tool(name="analytics_targets", annotations=_READ_ONLY)
async def _tool_analytics_targets(
    action: str = "report",
    period: str | None = None,
    sales_person: str | None = None,
    target_amount: float | None = None,
    ctx: Context = None,
) -> str:
    """Manage sales targets. action='report', 'underperformers', or 'set'."""
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


@mcp.tool(name="commission_report", annotations=_READ_ONLY)
async def _tool_commission_report(
    period: str | None = None,
    sales_person_name: str | None = None,
    flat_rate: float | None = None,
    ctx: Context = None,
) -> str:
    """Calculate commission for sales reps. Omit sales_person_name for all reps."""
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
