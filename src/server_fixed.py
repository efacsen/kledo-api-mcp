"""
Kledo MCP Server - Fixed implementation with proper MCP protocol support
"""
import os
import asyncio
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from loguru import logger

from .auth import KledoAuthenticator
from .cache import KledoCache
from .kledo_client import KledoAPIClient
from .utils.logger import setup_logger

# Import tool handlers
from .tools import financial, invoices, orders, products, contacts, deliveries, utilities


# Load environment variables
load_dotenv()

# Setup logging
setup_logger(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE")
)


# Initialize the MCP server
server = Server(os.getenv("MCP_SERVER_NAME", "kledo-crm"))
client: KledoAPIClient | None = None


async def initialize_client() -> KledoAPIClient:
    """Initialize Kledo API client with authentication."""
    global client

    if client is not None:
        return client

    try:
        # Get configuration from environment
        base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
        app_client_type = os.getenv("KLEDO_APP_CLIENT", "android")

        # Try API key first (recommended method)
        api_key = os.getenv("KLEDO_API_KEY")
        if api_key:
            logger.info("Using API key authentication (recommended)")
            auth = KledoAuthenticator(
                base_url=base_url,
                api_key=api_key
            )
        else:
            # Fallback to email/password (legacy method)
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
                app_client=app_client_type
            )

        # Perform initial login (no-op for API key, actual login for email/password)
        logger.info("Performing initial authentication...")
        if not await auth.login():
            raise ValueError("Failed to authenticate with Kledo API")

        # Initialize cache
        cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        cache_config_path = Path(__file__).parent.parent / "config" / "cache_config.yaml"

        cache = KledoCache(
            config_path=str(cache_config_path) if cache_config_path.exists() else None,
            enabled=cache_enabled
        )

        # Initialize client
        endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
        client = KledoAPIClient(
            auth,
            cache=cache,
            endpoints_config=str(endpoints_config_path) if endpoints_config_path.exists() else None
        )

        logger.info("Kledo API client initialized successfully")
        return client

    except Exception as e:
        logger.error(f"Failed to initialize Kledo API client: {str(e)}")
        raise


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    tools = []

    # Financial report tools
    tools.extend(financial.get_tools())

    # Invoice tools
    tools.extend(invoices.get_tools())

    # Order tools
    tools.extend(orders.get_tools())

    # Product tools
    tools.extend(products.get_tools())

    # Contact tools
    tools.extend(contacts.get_tools())

    # Delivery tools
    tools.extend(deliveries.get_tools())

    # Utility tools
    tools.extend(utilities.get_tools())

    logger.info(f"Listed {len(tools)} available tools")
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Call a tool with given arguments.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of text content responses
    """
    # Initialize client if needed
    api_client = await initialize_client()

    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    try:
        # Route to appropriate handler
        if name.startswith("financial_"):
            result = await financial.handle_tool(name, arguments, api_client)
        elif name.startswith("invoice_"):
            result = await invoices.handle_tool(name, arguments, api_client)
        elif name.startswith("order_"):
            result = await orders.handle_tool(name, arguments, api_client)
        elif name.startswith("product_"):
            result = await products.handle_tool(name, arguments, api_client)
        elif name.startswith("contact_"):
            result = await contacts.handle_tool(name, arguments, api_client)
        elif name.startswith("delivery_"):
            result = await deliveries.handle_tool(name, arguments, api_client)
        elif name.startswith("utility_"):
            result = await utilities.handle_tool(name, arguments, api_client)
        else:
            raise ValueError(f"Unknown tool: {name}")

        logger.info(f"Tool {name} completed successfully")
        return [TextContent(type="text", text=result)]

    except Exception as e:
        error_msg = f"Error executing tool {name}: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Main entry point."""
    logger.info("Starting Kledo MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
