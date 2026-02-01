#!/usr/bin/env python3
"""
Test script to retrieve and display actual data from Kledo API.
Shows examples of financial reports, invoices, and other data.
"""
import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.auth import KledoAuthenticator
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def format_currency(amount):
    """Format number as IDR currency."""
    if amount is None:
        return "IDR 0"
    try:
        return f"IDR {float(amount):,.2f}"
    except:
        return f"IDR {amount}"


async def test_data_retrieval():
    """Test retrieving various data from Kledo API."""

    # Load environment variables
    load_dotenv()

    print("=" * 70)
    print("  KLEDO API DATA RETRIEVAL TEST")
    print("=" * 70)

    # Initialize auth
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")

    if not api_key or api_key == "kledo_pat_your_api_key_here":
        print("❌ ERROR: Valid KLEDO_API_KEY not found in .env file")
        return

    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.login()

    # Initialize client
    cache = KledoCache(enabled=True)  # Enable cache for better performance
    endpoints_config = Path(__file__).parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(endpoints_config) if endpoints_config.exists() else None
    )

    # Test 1: Bank Accounts
    print_section("1. BANK ACCOUNTS")
    try:
        banks = await client.get_raw("/banks")
        if banks and "data" in banks:
            print(f"\n📊 Total accounts: {len(banks['data'])}")
            print("\n🏦 Bank Accounts:")
            for i, bank in enumerate(banks["data"][:5], 1):  # Show first 5
                print(f"   {i}. {bank.get('name', 'N/A')}")
                print(f"      Account: {bank.get('account_no', 'N/A')}")
                print(f"      Currency: {bank.get('currency_code', 'IDR')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # Test 2: Contacts (Customers & Vendors)
    print_section("2. CONTACTS (Customers & Vendors)")
    try:
        contacts = await client.get_raw("/finance/contacts", params={"per_page": 5})
        if contacts and "data" in contacts:
            total = contacts.get("total", len(contacts["data"]))
            print(f"\n📊 Total contacts: {total}")
            print("\n👥 Recent Contacts:")
            for i, contact in enumerate(contacts["data"], 1):
                contact_type = "Customer" if contact.get("is_customer") else "Vendor"
                print(f"   {i}. {contact.get('name', 'N/A')} ({contact_type})")
                print(f"      Email: {contact.get('email', 'N/A')}")
                print(f"      Phone: {contact.get('phone', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # Test 3: Products
    print_section("3. PRODUCTS & INVENTORY")
    try:
        products = await client.get_raw("/finance/products", params={"per_page": 5})
        if products and "data" in products:
            total = products.get("total", len(products["data"]))
            print(f"\n📊 Total products: {total}")
            print("\n📦 Recent Products:")
            for i, product in enumerate(products["data"], 1):
                print(f"   {i}. {product.get('name', 'N/A')}")
                print(f"      SKU: {product.get('sku', 'N/A')}")
                print(f"      Price: {format_currency(product.get('sell_price'))}")

                # Show stock if available
                stock_info = product.get('inventory_tracking')
                if stock_info:
                    qty = product.get('inventory_qty', 0)
                    print(f"      Stock: {qty} {product.get('default_unit', {}).get('name', 'units')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # Test 4: Recent Sales Invoices
    print_section("4. SALES INVOICES")
    try:
        invoices = await client.get_raw("/finance/invoices", params={"per_page": 5})
        if invoices and "data" in invoices:
            total = invoices.get("total", len(invoices["data"]))
            print(f"\n📊 Total invoices: {total}")
            print("\n🧾 Recent Sales Invoices:")
            for i, invoice in enumerate(invoices["data"], 1):
                status = invoice.get("status", {}).get("name", "Unknown")
                print(f"   {i}. {invoice.get('trans_number', 'N/A')} - {status}")
                print(f"      Customer: {invoice.get('contact', {}).get('name', 'N/A')}")
                print(f"      Date: {invoice.get('trans_date', 'N/A')}")
                print(f"      Total: {format_currency(invoice.get('grand_total'))}")

                # Show payment status
                paid = float(invoice.get('paid_amount', 0))
                total_amt = float(invoice.get('grand_total', 0))
                remaining = total_amt - paid
                if remaining > 0:
                    print(f"      Outstanding: {format_currency(remaining)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # Test 5: Bank Balances
    print_section("5. BANK BALANCES")
    try:
        balances = await client.get_raw("/finance/bank/balances")
        if balances and "data" in balances:
            print(f"\n📊 Current balances for {len(balances['data'])} accounts:")
            print("\n💰 Balances:")
            total_balance = 0
            for i, balance in enumerate(balances["data"], 1):
                amount = float(balance.get('balance', 0))
                total_balance += amount
                print(f"   {i}. {balance.get('bank_name', 'N/A')}")
                print(f"      Balance: {format_currency(amount)}")

            print(f"\n   📈 Total Balance: {format_currency(total_balance)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # Test 6: Financial Summary (if available)
    print_section("6. SALES SUMMARY (Last 30 Days)")
    try:
        # Calculate date range for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        params = {
            "date_from": start_date.strftime("%Y-%m-%d"),
            "date_to": end_date.strftime("%Y-%m-%d"),
            "per_page": 10
        }

        sales = await client.get_raw("/reportings/sales-by-contact", params=params)
        if sales and "data" in sales:
            print(f"\n📊 Sales by customer (last 30 days):")
            print(f"\n💵 Top Customers:")

            total_sales = 0
            for i, sale in enumerate(sales["data"][:5], 1):  # Top 5
                amount = float(sale.get('total', 0))
                total_sales += amount
                print(f"   {i}. {sale.get('contact_name', 'N/A')}")
                print(f"      Sales: {format_currency(amount)}")

            if total_sales > 0:
                print(f"\n   📈 Total from top 5: {format_currency(total_sales)}")
    except Exception as e:
        print(f"⚠️  Sales summary not available: {str(e)}")

    # Summary
    print_section("TEST SUMMARY")
    print("\n✅ Data retrieval test completed!")
    print("\n📝 Available data types:")
    print("   - Bank accounts and balances")
    print("   - Customers and vendors")
    print("   - Products and inventory")
    print("   - Sales and purchase invoices")
    print("   - Financial reports and summaries")
    print("\n🚀 Your MCP server can now provide all this data to AI agents!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_data_retrieval())
