"""
Kledo MCP Server — FastMCP 1.x implementation.

Phase 3 (v1.1 SDK Foundation): replaces the pre-1.0 `mcp.server.Server` pattern
with `FastMCP`, adds a `lifespan` hook for KledoAPIClient init/teardown, injects
domain facts via the `instructions` field, and returns machine-readable errors
via `ToolError`.

The 11 tool modules in `src/tools/` are NOT modified in Phase 3. Their existing
`get_tools()` / `handle_tool()` interface is bridged into FastMCP via a
registration loop that wraps each Tool in a closure calling `handle_tool`.
Phase 4 will replace this bridge with `@mcp.tool()` decorators per module.
"""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import Tool

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
        # KledoAPIClient currently creates httpx.AsyncClient per-request
        # (src/kledo_client.py line 141), so there is no long-lived HTTP session
        # to close. The defensive check below is for forward compatibility if
        # the client is ever refactored to hold a persistent AsyncClient.
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


# Maps tool-module reference → handler callable. All modules expose the same
# (get_tools, handle_tool) pair. revenue_ tools include a few legacy names
# without the "revenue_" prefix — all go to revenue.handle_tool.
_TOOL_MODULES = [
    financial,
    invoices,
    orders,
    products,
    contacts,
    deliveries,
    utilities,
    sales_analytics,
    revenue,
    analytics,
    commission,
]


def _make_wrapper(module: Any, tool: Tool) -> Any:
    """
    Build an async closure that FastMCP can register as a tool.

    The closure captures the tool name and owning module. At call time it
    fetches the KledoAPIClient from the lifespan context and routes through
    the module's existing `handle_tool` dispatch. On exception it raises
    ToolError with a scrubbed recovery hint.
    """
    tool_name = tool.name

    async def _wrapper(**arguments: Any) -> str:
        ctx = mcp.get_context()
        app_ctx: AppContext = ctx.request_context.lifespan_context  # type: ignore[assignment]
        client = app_ctx.client
        logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
        try:
            result = await module.handle_tool(tool_name, arguments, client)
            logger.info(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            scrubbed = _scrub_secrets(str(e))
            hint = _recovery_hint(tool_name, e)
            logger.exception(f"Tool {tool_name} failed: {scrubbed}")
            raise ToolError(f"Tool '{tool_name}' failed: {scrubbed}. {hint}") from e

    _wrapper.__name__ = tool_name
    _wrapper.__doc__ = tool.description or f"Kledo tool: {tool_name}"
    return _wrapper


def _register_tools() -> int:
    """Register every legacy tool with FastMCP. Returns the number registered."""
    count = 0
    for module in _TOOL_MODULES:
        for tool in module.get_tools():
            wrapper = _make_wrapper(module, tool)
            mcp.add_tool(
                wrapper,
                name=tool.name,
                description=tool.description,
            )
            count += 1
    logger.info(f"Registered {count} tools with FastMCP")
    return count


_TOOL_COUNT = _register_tools()


def main() -> None:
    """CLI entry point — runs the FastMCP server over stdio."""
    logger.info(f"Starting Kledo MCP Server ({_TOOL_COUNT} tools registered)...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
