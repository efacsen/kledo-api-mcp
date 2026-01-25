"""
List vs Detail Endpoint Comparison
Compares fields available in LIST endpoints vs DETAIL endpoints for all entity types
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Set, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache

# Load environment
load_dotenv()


def extract_fields(obj: Any, prefix: str = "") -> Set[str]:
    """
    Recursively extract all field paths from an object.

    Examples:
        {"name": "X", "group": {"id": 1}}
        → {"name", "group", "group.id", "group.name"}
    """
    fields = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            field_path = f"{prefix}.{key}" if prefix else key
            fields.add(field_path)

            # Recursively extract nested fields
            if isinstance(value, dict):
                fields.update(extract_fields(value, field_path))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # For arrays of objects, extract fields from first item
                fields.update(extract_fields(value[0], f"{field_path}[0]"))

    return fields


def compare_fields(list_fields: Set[str], detail_fields: Set[str]) -> Dict[str, Set[str]]:
    """Compare two field sets and return differences."""
    return {
        "only_in_list": list_fields - detail_fields,
        "only_in_detail": detail_fields - list_fields,
        "in_both": list_fields & detail_fields
    }


async def test_list_vs_detail(
    client: KledoAPIClient,
    category: str,
    list_endpoint: str,
    detail_endpoint: str,
    name: str
):
    """Compare LIST vs DETAIL endpoint for an entity type."""
    print(f"\n{'='*100}")
    print(f"TESTING: {name}")
    print(f"Category: {category}")
    print(f"{'='*100}\n")

    try:
        # Test LIST endpoint
        print(f"📋 Testing LIST endpoint: {category}.{list_endpoint}")
        list_response = await client.get(
            category=category,
            name=list_endpoint,
            params={"per_page": 1, "page": 1}
        )

        # Extract first item from list response
        list_item = None
        if list_response:
            if "data" in list_response:
                data = list_response["data"]
                if isinstance(data, dict) and "data" in data:
                    # Paginated response: {data: {data: [...]}}
                    items = data["data"]
                    if items:
                        list_item = items[0]
                elif isinstance(data, list) and data:
                    # Direct array: {data: [...]}
                    list_item = data[0]

        if not list_item:
            print("⚠️  No items in LIST response - skipping comparison")
            return

        # Get ID for detail lookup
        item_id = list_item.get("id")
        if not item_id:
            print("⚠️  No 'id' field in list item - cannot fetch detail")
            return

        print(f"✓ Got list item (ID: {item_id})\n")

        # Test DETAIL endpoint
        print(f"📄 Testing DETAIL endpoint: {category}.{detail_endpoint} (ID: {item_id})")
        detail_response = await client.get(
            category=category,
            name=detail_endpoint,
            path_params={"id": item_id}
        )

        # Extract detail item
        detail_item = None
        if detail_response:
            if "data" in detail_response:
                detail_item = detail_response["data"]
            else:
                detail_item = detail_response

        if not detail_item:
            print("⚠️  No data in DETAIL response - skipping comparison")
            return

        print(f"✓ Got detail item\n")

        # Extract fields from both
        list_fields = extract_fields(list_item)
        detail_fields = extract_fields(detail_item)

        # Compare
        comparison = compare_fields(list_fields, detail_fields)

        # Display results
        print("="*100)
        print("FIELD COMPARISON RESULTS")
        print("="*100)

        print(f"\n📊 STATISTICS:")
        print(f"  • Fields in LIST:   {len(list_fields)}")
        print(f"  • Fields in DETAIL: {len(detail_fields)}")
        print(f"  • In both:          {len(comparison['in_both'])}")
        print(f"  • Only in DETAIL:   {len(comparison['only_in_detail'])}")
        print(f"  • Only in LIST:     {len(comparison['only_in_list'])}")

        if comparison['only_in_detail']:
            print(f"\n⭐ FIELDS ONLY IN DETAIL (missing from LIST): {len(comparison['only_in_detail'])}")
            print("-"*100)
            for field in sorted(comparison['only_in_detail']):
                # Get the value from detail item
                value = detail_item
                for part in field.split('.'):
                    if part.endswith('[0]'):
                        part = part[:-3]
                        value = value.get(part, [])
                        if value:
                            value = value[0]
                    else:
                        value = value.get(part) if isinstance(value, dict) else None
                    if value is None:
                        break

                # Format value for display
                if isinstance(value, str):
                    sample = f" = {repr(value[:50])}" if len(value) > 50 else f" = {repr(value)}"
                elif isinstance(value, (int, float, bool)):
                    sample = f" = {value}"
                elif value is None:
                    sample = " = null"
                elif isinstance(value, list):
                    sample = f" (array with {len(value)} items)"
                elif isinstance(value, dict):
                    sample = f" (object with {len(value)} keys)"
                else:
                    sample = ""

                print(f"  • {field:<40} {sample}")

        if comparison['only_in_list']:
            print(f"\n📋 FIELDS ONLY IN LIST (missing from DETAIL): {len(comparison['only_in_list'])}")
            print("-"*100)
            for field in sorted(comparison['only_in_list']):
                print(f"  • {field}")

        # Show sample objects
        print(f"\n📄 SAMPLE LIST OBJECT:")
        print("-"*100)
        print(json.dumps(list_item, indent=2, ensure_ascii=False)[:1000] + "...")

        print(f"\n📄 SAMPLE DETAIL OBJECT:")
        print("-"*100)
        print(json.dumps(detail_item, indent=2, ensure_ascii=False)[:1000] + "...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Test all entity types."""
    print("="*100)
    print("KLEDO API: LIST vs DETAIL COMPARISON")
    print("="*100)

    # Initialize client
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")

    if not api_key:
        print("❌ Error: KLEDO_API_KEY not found in .env")
        return

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

    print("✓ Authenticated\n")

    # Define tests: (category, list_endpoint, detail_endpoint, name)
    tests = [
        ("contacts", "list", "detail", "Contacts"),
        ("invoices", "list", "detail", "Sales Invoices"),
        ("purchase_invoices", "list", "detail", "Purchase Invoices"),
        ("products", "list", "detail", "Products"),
        ("orders", "list", "detail", "Sales Orders"),
        ("purchase_orders", "list", "detail", "Purchase Orders"),
        ("deliveries", "list", "detail", "Deliveries"),
        ("purchase_deliveries", "list", "detail", "Purchase Deliveries"),
    ]

    for category, list_ep, detail_ep, name in tests:
        await test_list_vs_detail(client, category, list_ep, detail_ep, name)
        await asyncio.sleep(0.5)  # Be nice to API

    print("\n" + "="*100)
    print("TESTING COMPLETE")
    print("="*100)


if __name__ == "__main__":
    asyncio.run(main())
