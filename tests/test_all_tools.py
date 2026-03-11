"""
Comprehensive test of ALL MCP tools
Tests each tool to ensure it returns valid data

NOTE: This is an integration test that requires live Kledo API credentials.
Run manually with a configured .env file — skipped in automated test runs.
"""
import pytest
pytestmark = pytest.mark.skip(reason="Integration test requires live Kledo API credentials")

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import date, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache
from src.tools import financial, invoices, orders, products, contacts, deliveries, utilities, sales_analytics


async def test_tool_module(module_name: str, module, client: KledoAPIClient):
    """Test all tools in a module."""
    print(f"\n{'='*100}")
    print(f"MODULE: {module_name}")
    print(f"{'='*100}\n")

    tools = module.get_tools()
    print(f"Found {len(tools)} tools in {module_name}\n")

    results = []

    for tool in tools:
        tool_name = tool.name
        print(f"Testing: {tool_name}...")

        try:
            # Prepare test arguments based on tool name
            args = get_test_args(tool_name)

            # Call the tool
            result = await module.handle_tool(tool_name, args, client)

            # Check result
            if result:
                if isinstance(result, str):
                    result_preview = result[:200] + "..." if len(result) > 200 else result
                else:
                    result_preview = str(result)[:200] + "..."

                print(f"  ✅ SUCCESS - {len(result)} chars returned")
                print(f"     Preview: {result_preview}\n")
                results.append((tool_name, "✅ PASS", None))
            else:
                print(f"  ⚠️  EMPTY RESPONSE\n")
                results.append((tool_name, "⚠️ EMPTY", None))

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}\n")
            results.append((tool_name, "❌ FAIL", str(e)))

    return results


def get_test_args(tool_name: str) -> dict:
    """Get appropriate test arguments for each tool."""
    today = date.today()
    first_of_month = today.replace(day=1)

    # Financial reports
    if tool_name == "financial_activity_team_report":
        return {"date_from": "this_month"}
    elif tool_name == "financial_sales_summary":
        return {"date_from": first_of_month.strftime("%Y-%m-%d")}
    elif tool_name == "financial_purchase_summary":
        return {"date_from": first_of_month.strftime("%Y-%m-%d")}
    elif tool_name == "financial_bank_balances":
        return {}

    # Invoices
    elif tool_name == "invoice_list":
        return {"per_page": 5}
    elif tool_name == "invoice_detail":
        return {"invoice_id": 1}  # Will use first available invoice
    elif tool_name == "invoice_totals":
        return {}
    elif tool_name == "invoice_search":
        return {"query": "INV"}

    # Purchase invoices
    elif tool_name == "purchase_invoice_list":
        return {"per_page": 5}
    elif tool_name == "purchase_invoice_detail":
        return {"invoice_id": 1}
    elif tool_name == "purchase_invoice_totals":
        return {}

    # Orders
    elif tool_name == "order_list":
        return {"per_page": 5}
    elif tool_name == "order_detail":
        return {"order_id": 1}
    elif tool_name == "order_totals":
        return {}
    elif tool_name == "purchase_order_list":
        return {"per_page": 5}
    elif tool_name == "purchase_order_detail":
        return {"order_id": 1}
    elif tool_name == "purchase_order_totals":
        return {}

    # Products
    elif tool_name == "product_list":
        return {"per_page": 5}
    elif tool_name == "product_detail":
        return {"product_id": 1}
    elif tool_name == "product_search":
        return {"query": "cat"}
    elif tool_name == "product_categories":
        return {}

    # Contacts
    elif tool_name == "contact_list":
        return {"per_page": 5}
    elif tool_name == "contact_detail":
        return {"contact_id": 1}
    elif tool_name == "contact_search":
        return {"query": "PT"}
    elif tool_name == "contact_groups":
        return {}

    # Deliveries
    elif tool_name == "delivery_list":
        return {"per_page": 5}
    elif tool_name == "delivery_detail":
        return {"delivery_id": 1}
    elif tool_name == "purchase_delivery_list":
        return {"per_page": 5}
    elif tool_name == "purchase_delivery_detail":
        return {"delivery_id": 1}

    # Utilities
    elif tool_name == "utility_list_warehouses":
        return {}
    elif tool_name == "utility_list_tags":
        return {}
    elif tool_name == "utility_list_units":
        return {}

    # Sales analytics
    elif tool_name == "sales_rep_list":
        return {}
    elif tool_name == "sales_rep_revenue_report":
        week_ago = today - timedelta(days=7)
        return {
            "start_date": week_ago.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "group_by": "day"
        }

    return {}


async def main():
    """Test all tools."""
    print("="*100)
    print("COMPREHENSIVE MCP TOOLS TEST")
    print("="*100)

    # Load environment
    load_dotenv()

    # Initialize client
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")

    if not api_key:
        print("❌ Error: KLEDO_API_KEY not found in .env")
        return

    print("\nInitializing client...")
    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.ensure_authenticated()

    cache_config_path = Path(__file__).parent.parent / "config" / "cache_config.yaml"
    cache = KledoCache(config_path=str(cache_config_path) if cache_config_path.exists() else None)

    endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(endpoints_config_path) if endpoints_config_path.exists() else None
    )

    print("✓ Client initialized\n")

    # Test each module
    all_results = []

    modules = [
        ("Financial Reports", financial),
        ("Invoices", invoices),
        ("Orders", orders),
        ("Products", products),
        ("Contacts", contacts),
        ("Deliveries", deliveries),
        ("Utilities", utilities),
        ("Sales Analytics", sales_analytics),
    ]

    for module_name, module in modules:
        results = await test_tool_module(module_name, module, client)
        all_results.extend(results)
        await asyncio.sleep(1)  # Be nice to API

    # Summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100 + "\n")

    passed = [r for r in all_results if r[1] == "✅ PASS"]
    empty = [r for r in all_results if r[1] == "⚠️ EMPTY"]
    failed = [r for r in all_results if r[1] == "❌ FAIL"]

    print(f"Total Tools Tested: {len(all_results)}")
    print(f"✅ Passed: {len(passed)}")
    print(f"⚠️  Empty Response: {len(empty)}")
    print(f"❌ Failed: {len(failed)}")
    print()

    if empty:
        print("Tools with Empty Responses:")
        for tool_name, status, error in empty:
            print(f"  - {tool_name}")
        print()

    if failed:
        print("Failed Tools:")
        for tool_name, status, error in failed:
            print(f"  - {tool_name}: {error}")
        print()

    if len(passed) == len(all_results):
        print("🎉 ALL TOOLS PASSED! MCP Server is fully operational!")
    else:
        print(f"⚠️  {len(all_results) - len(passed)} tools need attention")

    print("\n" + "="*100)


if __name__ == "__main__":
    asyncio.run(main())
