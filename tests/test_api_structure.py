"""
API Structure Testing Script
Tests actual Kledo API responses to validate entity model mappings
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import src as package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache

# Load environment variables
load_dotenv()


async def test_endpoint(client: KledoAPIClient, category: str, endpoint: str, name: str):
    """Test a single endpoint and display its response structure"""
    print(f"\n{'='*80}")
    print(f"TESTING: {name}")
    print(f"Endpoint: {category}.{endpoint}")
    print(f"{'='*80}\n")

    try:
        # Make the request with pagination
        response = await client.get(
            category=category,
            name=endpoint,
            params={"per_page": 5, "page": 1}  # Just get first 5 items
        )

        # Check if we got data
        if not response:
            print("⚠️  Empty response")
            return

        # Display summary
        if isinstance(response, dict):
            if "data" in response:
                items = response["data"]

                # Handle both list and dict responses
                if isinstance(items, list):
                    total = response.get("total", len(items))
                    print(f"✓ Got {len(items)} items (total: {total})\n")

                    if items and len(items) > 0:
                        first_item = items[0]
                        print("FIRST ITEM STRUCTURE:")
                        print("-" * 80)
                        print(json.dumps(first_item, indent=2, ensure_ascii=False))
                        print("-" * 80)

                        # Show available fields
                        print(f"\nAVAILABLE FIELDS ({len(first_item)} total):")
                        for key in first_item.keys():
                            value = first_item[key]
                            value_type = type(value).__name__

                            # Show sample value for simple types
                            if isinstance(value, (str, int, float, bool)):
                                sample = f" = {repr(value)[:50]}"
                            elif isinstance(value, list):
                                sample = f" (array with {len(value)} items)"
                            elif isinstance(value, dict):
                                sample = f" (object with {len(value)} keys)"
                            elif value is None:
                                sample = " = null"
                            else:
                                sample = ""

                            print(f"  • {key:<30} [{value_type}]{sample}")
                    else:
                        print("⚠️  No items in response")
                elif isinstance(items, dict):
                    # Data is a single object (dict)
                    print(f"✓ Got single object response\n")
                    print("RESPONSE STRUCTURE:")
                    print("-" * 80)
                    print(json.dumps(items, indent=2, ensure_ascii=False))
                    print("-" * 80)

                    # Show available fields
                    print(f"\nAVAILABLE FIELDS ({len(items)} total):")
                    for key in items.keys():
                        value = items[key]
                        value_type = type(value).__name__

                        # Show sample value for simple types
                        if isinstance(value, (str, int, float, bool)):
                            sample = f" = {repr(value)[:50]}"
                        elif isinstance(value, list):
                            sample = f" (array with {len(value)} items)"
                        elif isinstance(value, dict):
                            sample = f" (object with {len(value)} keys)"
                        elif value is None:
                            sample = " = null"
                        else:
                            sample = ""

                        print(f"  • {key:<30} [{value_type}]{sample}")
                else:
                    print(f"⚠️  Unexpected data type: {type(items).__name__}")
                    print(json.dumps(items, indent=2, ensure_ascii=False))
            else:
                print("Response structure:")
                print(json.dumps(response, indent=2, ensure_ascii=False))
        else:
            print(f"Response type: {type(response).__name__}")
            print(json.dumps(response, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Test priority endpoints"""
    print("="*80)
    print("KLEDO API STRUCTURE VALIDATION")
    print("="*80)

    # Get configuration from environment
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")
    email = os.getenv("KLEDO_EMAIL")
    password = os.getenv("KLEDO_PASSWORD")
    app_client = os.getenv("KLEDO_APP_CLIENT", "pos")

    # Initialize authenticator
    if api_key:
        print("Using API key authentication\n")
        auth = KledoAuthenticator(
            base_url=base_url,
            api_key=api_key
        )
    elif email and password:
        print("Using email/password authentication\n")
        auth = KledoAuthenticator(
            base_url=base_url,
            email=email,
            password=password,
            app_client=app_client
        )
    else:
        print("❌ Error: No authentication credentials found in .env")
        print("   Set either KLEDO_API_KEY or KLEDO_EMAIL + KLEDO_PASSWORD")
        return

    # Initialize cache
    cache_config_path = Path(__file__).parent.parent / "config" / "cache_config.yaml"
    cache = KledoCache(config_path=str(cache_config_path) if cache_config_path.exists() else None)

    # Initialize client
    endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(endpoints_config_path) if endpoints_config_path.exists() else None
    )

    # Login first
    print("Authenticating...")
    await client.auth.ensure_authenticated()
    print("✓ Authenticated\n")

    # Test priority endpoints
    tests = [
        ("contacts", "list", "Contacts List"),
        ("invoices", "list", "Sales Invoices List"),
        ("purchase_invoices", "list", "Purchase Invoices List"),
        ("products", "list", "Products List"),
    ]

    for category, endpoint, name in tests:
        await test_endpoint(client, category, endpoint, name)
        await asyncio.sleep(0.5)  # Be nice to the API

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
