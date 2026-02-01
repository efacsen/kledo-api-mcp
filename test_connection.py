#!/usr/bin/env python3
"""
Simple test script to verify Kledo API connection with API key.
Run this to test your API key authentication before using the MCP server.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.auth import KledoAuthenticator
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache


async def test_connection():
    """Test connection to Kledo API."""

    # Load environment variables
    load_dotenv()

    print("=" * 60)
    print("KLEDO API CONNECTION TEST")
    print("=" * 60)

    # Get configuration
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")
    email = os.getenv("KLEDO_EMAIL")

    print(f"\n📍 Base URL: {base_url}")

    # Determine auth method
    if api_key and api_key != "kledo_pat_your_api_key_here":
        print(f"🔑 Auth Method: API Key")
        print(f"🔑 API Key: {api_key[:15]}...{api_key[-4:] if len(api_key) > 19 else ''}")

        auth = KledoAuthenticator(
            base_url=base_url,
            api_key=api_key
        )
    elif email:
        password = os.getenv("KLEDO_PASSWORD")
        print(f"🔑 Auth Method: Email/Password (legacy)")
        print(f"📧 Email: {email}")

        if not password:
            print("❌ ERROR: KLEDO_PASSWORD not set in .env file")
            return

        auth = KledoAuthenticator(
            base_url=base_url,
            email=email,
            password=password,
            app_client=os.getenv("KLEDO_APP_CLIENT", "android")
        )
    else:
        print("❌ ERROR: No authentication credentials found in .env file")
        print("   Please set either KLEDO_API_KEY or (KLEDO_EMAIL + KLEDO_PASSWORD)")
        return

    print("\n" + "=" * 60)
    print("STEP 1: Authentication")
    print("=" * 60)

    # Test authentication
    try:
        success = await auth.login()
        if success:
            print("✅ Authentication successful!")
            print(f"   Auth method: {auth.auth_method}")
            print(f"   Is authenticated: {auth.is_authenticated}")
        else:
            print("❌ Authentication failed!")
            return
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return

    print("\n" + "=" * 60)
    print("STEP 2: Initialize API Client")
    print("=" * 60)

    # Initialize client with minimal cache
    try:
        cache = KledoCache(enabled=False)  # Disable cache for testing

        endpoints_config = Path(__file__).parent / "config" / "endpoints.yaml"
        client = KledoAPIClient(
            auth,
            cache=cache,
            endpoints_config=str(endpoints_config) if endpoints_config.exists() else None
        )
        print("✅ API client initialized")
    except Exception as e:
        print(f"❌ Client initialization error: {str(e)}")
        return

    print("\n" + "=" * 60)
    print("STEP 3: Test API Calls")
    print("=" * 60)

    # Test 1: Get bank accounts (lightweight endpoint)
    print("\n🧪 Test 1: Fetching bank accounts...")
    try:
        banks = await client.get_raw("/banks")
        if banks and "data" in banks:
            bank_count = len(banks.get("data", []))
            print(f"✅ Success! Found {bank_count} bank account(s)")

            # Show first bank if available
            if bank_count > 0:
                first_bank = banks["data"][0]
                print(f"   Example: {first_bank.get('name', 'N/A')} - {first_bank.get('account_no', 'N/A')}")
        else:
            print("⚠️  Empty response from API")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    # Test 2: Get contacts (common endpoint)
    print("\n🧪 Test 2: Fetching contacts...")
    try:
        contacts = await client.get_raw("/finance/contacts", params={"per_page": 3})
        if contacts and "data" in contacts:
            contact_count = len(contacts.get("data", []))
            print(f"✅ Success! Found {contact_count} contact(s) (showing first 3)")

            # Show first contact if available
            if contact_count > 0:
                first_contact = contacts["data"][0]
                print(f"   Example: {first_contact.get('name', 'N/A')} ({first_contact.get('email', 'No email')})")
        else:
            print("⚠️  Empty response from API")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    # Test 3: Get products
    print("\n🧪 Test 3: Fetching products...")
    try:
        products = await client.get_raw("/finance/products", params={"per_page": 3})
        if products and "data" in products:
            product_count = len(products.get("data", []))
            print(f"✅ Success! Found {product_count} product(s) (showing first 3)")

            # Show first product if available
            if product_count > 0:
                first_product = products["data"][0]
                print(f"   Example: {first_product.get('name', 'N/A')} - SKU: {first_product.get('sku', 'N/A')}")
        else:
            print("⚠️  Empty response from API")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ Connection test completed!")
    print("\n📝 Next steps:")
    print("   1. If all tests passed, your MCP server is ready to use")
    print("   2. Run the server with: python -m src.server")
    print("   3. Configure Claude Desktop to use this MCP server")
    print("   4. Start asking questions about your Kledo data!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_connection())
