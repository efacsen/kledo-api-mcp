#!/usr/bin/env python3
"""
Natural Language Query Demo for Kledo MCP Server
Uses the smart routing system from Phase 4 to understand queries
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.auth import KledoAuthenticator
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache
from src.routing import route_query
from src.tools import financial, invoices, orders, products, contacts, deliveries, utilities


async def execute_natural_language_query(query: str, client: KledoAPIClient):
    """
    Execute a natural language query by routing it to the appropriate tool.

    Args:
        query: Natural language question (e.g., "What's my bank balance?")
        client: Initialized Kledo API client
    """
    print(f"\n{'='*70}")
    print(f"Query: \"{query}\"")
    print(f"{'='*70}")

    # Use the smart routing system to find the right tool
    routing_result = route_query(query)

    print(f"\n🤖 Routing Analysis:")
    print(f"   Date range: {routing_result.date_range or 'None'}")

    if routing_result.clarification_needed:
        print(f"\n⚠️  Need clarification: {routing_result.clarification_needed}")
        return

    if not routing_result.matched_tools:
        print(f"\n❌ No matching tools found")
        return

    print(f"\n🎯 Suggested tools ({len(routing_result.matched_tools)}):")
    for i, suggestion in enumerate(routing_result.matched_tools[:3], 1):
        print(f"   {i}. {suggestion.tool_name} (score: {suggestion.score:.1f})")
        print(f"      Purpose: {suggestion.purpose}")

    # Use the top suggestion
    top_tool = routing_result.matched_tools[0]
    tool_name = top_tool.tool_name
    print(f"\n⚡ Executing: {tool_name}")

    # Build parameters from routing result
    params = {}
    if routing_result.date_range:
        params["date_from"] = routing_result.date_range[0]
        params["date_to"] = routing_result.date_range[1]

    # Add suggested parameters if any
    if top_tool.suggested_params:
        params.update(top_tool.suggested_params)

    # Add per_page limit for cleaner output
    if "list" in tool_name and "per_page" not in params:
        params["per_page"] = 5

    print(f"   Parameters: {params if params else 'None'}")

    try:
        # Route to the appropriate handler

        if tool_name.startswith("financial_"):
            result = await financial.handle_tool(tool_name, params, client)
        elif tool_name.startswith("invoice_"):
            result = await invoices.handle_tool(tool_name, params, client)
        elif tool_name.startswith("order_"):
            result = await orders.handle_tool(tool_name, params, client)
        elif tool_name.startswith("product_"):
            result = await products.handle_tool(tool_name, params, client)
        elif tool_name.startswith("contact_"):
            result = await contacts.handle_tool(tool_name, params, client)
        elif tool_name.startswith("delivery_"):
            result = await deliveries.handle_tool(tool_name, params, client)
        elif tool_name.startswith("utility_"):
            result = await utilities.handle_tool(tool_name, params, client)
        else:
            print(f"❌ Unknown tool category: {tool_name}")
            return

        print(f"\n✅ Result:\n")
        print(result)

    except Exception as e:
        print(f"\n❌ Error executing tool: {str(e)}")


async def main():
    """Main demo function."""

    # Load environment variables
    load_dotenv()

    print("="*70)
    print("  NATURAL LANGUAGE QUERY DEMO")
    print("  Powered by Phase 4 Smart Routing")
    print("="*70)

    # Initialize client
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")

    if not api_key or api_key == "kledo_pat_your_api_key_here":
        print("❌ ERROR: Valid KLEDO_API_KEY not found in .env file")
        return

    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.login()

    cache = KledoCache(enabled=True)
    endpoints_config = Path(__file__).parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(endpoints_config) if endpoints_config.exists() else None
    )

    print("\n✓ Connected to Kledo API")

    # Demo queries - both English and Indonesian
    demo_queries = [
        # English queries
        "What's my bank balance?",
        "Show me all customers",
        "List all products",
        "Show unpaid invoices",
        "Who owes me money?",

        # Indonesian queries
        "Berapa saldo bank saya?",
        "Tampilkan semua produk",
        "Siapa yang belum bayar?",
    ]

    print(f"\n{'='*70}")
    print("  DEMO QUERIES")
    print(f"{'='*70}")
    print("\nTrying these natural language queries:")
    for i, q in enumerate(demo_queries, 1):
        print(f"{i}. {q}")

    print(f"\n{'='*70}")
    print("  EXECUTING QUERIES")
    print(f"{'='*70}")

    # Execute each demo query
    for query in demo_queries[:5]:  # Run first 5 queries
        await execute_natural_language_query(query, client)
        await asyncio.sleep(1)  # Brief pause between queries

    print(f"\n{'='*70}")
    print("  DEMO COMPLETE")
    print(f"{'='*70}")
    print("\n💡 Your smart routing system is working!")
    print("   - Understands English and Indonesian")
    print("   - Matches patterns and keywords")
    print("   - Routes to the correct tools automatically")
    print("\n🚀 Ready for integration with Claude Desktop or other MCP clients!")


if __name__ == "__main__":
    asyncio.run(main())
