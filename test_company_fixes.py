#!/usr/bin/env python3
"""
Test the company name display and fuzzy search fixes.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.auth import KledoAuthenticator
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache
from src.tools.invoices import (
    format_customer_display,
    fuzzy_company_match,
    filter_invoices_by_company_fuzzy
)

async def test_fixes():
    """Test company name display and fuzzy search."""
    
    print("=" * 80)
    print("COMPANY NAME DISPLAY & FUZZY SEARCH TEST")
    print("=" * 80)
    
    # Initialize client
    auth = KledoAuthenticator(
        base_url=os.getenv("KLEDO_BASE_URL", "https://ptcepatservicestation.api.kledo.com/api/v1"),
        api_key=os.getenv("KLEDO_API_KEY")
    )
    
    await auth.login()
    print("✓ Authenticated\n")
    
    cache = KledoCache(enabled=False)
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(Path(__file__).parent / "config" / "endpoints.yaml")
    )
    
    # Test 1: Company name display
    print("\n" + "=" * 80)
    print("TEST 1: Company Name Display Function")
    print("=" * 80)
    
    test_cases = [
        {
            "contact": {
                "name": "Darma",
                "company": "PT Nippon Paint Indonesia"
            }
        },
        {
            "contact": {
                "name": "Suwito",
                "company": None
            }
        },
        {
            "contact": {
                "name": "PT Alta Airindo",
                "company": "PT Alta Airindo"  # Same as name
            }
        }
    ]
    
    for i, invoice in enumerate(test_cases, 1):
        result = format_customer_display(invoice)
        print(f"\n[{i}] Input: name={invoice['contact']['name']}, company={invoice['contact'].get('company')}")
        print(f"    Output: {result}")
    
    # Test 2: Fuzzy company matching
    print("\n" + "=" * 80)
    print("TEST 2: Fuzzy Company Name Matching")
    print("=" * 80)
    
    fuzzy_tests = [
        ("Nipsea", "PT Nippon Paint Indonesia", "Darma"),
        ("Nipon", "PT Nippon Paint Indonesia", "Darma"),
        ("Nippon", "PT Nippon Paint Indonesia", "Darma"),
        ("Kurnia", "PT. KURNIA PROPERTINDO SEJAHTERA", "Teguh"),
        ("Alta", "PT. ALTA AIRINDO GEMILANG", "Agung"),
    ]
    
    for search, company, contact in fuzzy_tests:
        is_match, score = fuzzy_company_match(search, company, contact)
        status = "✓ MATCH" if is_match else "✗ NO MATCH"
        print(f"\n{status} (score: {score:.1f})")
        print(f"  Search: '{search}'")
        print(f"  Company: '{company}'")
        print(f"  Contact: '{contact}'")
    
    # Test 3: Real invoice data
    print("\n" + "=" * 80)
    print("TEST 3: Real Invoice Data (Jan 2026)")
    print("=" * 80)
    
    data = await client.list_invoices(
        date_from="2026-01-01",
        date_to="2026-01-31",
        per_page=20,
        force_refresh=False
    )
    
    invoices = data.get("data", {}).get("data", [])
    
    print(f"\nFetched {len(invoices)} invoices\n")
    
    if invoices:
        print("Sample invoice displays:")
        for i, inv in enumerate(invoices[:5], 1):
            display = format_customer_display(inv)
            ref = inv.get("ref_number", "N/A")
            print(f"\n  [{i}] {ref}")
            print(f"      {display}")
    
    # Test 4: Fuzzy search on real data
    print("\n" + "=" * 80)
    print("TEST 4: Fuzzy Search on Real Data")
    print("=" * 80)
    
    search_terms = ["Nippon", "Kurnia", "Alta"]
    
    for search in search_terms:
        print(f"\n--- Searching for: '{search}' ---")
        matches = filter_invoices_by_company_fuzzy(invoices, search)
        print(f"Found {len(matches)} matches")
        
        for i, inv in enumerate(matches[:3], 1):
            display = format_customer_display(inv)
            ref = inv.get("ref_number", "N/A")
            print(f"  [{i}] {ref} - {display}")
    
    print("\n" + "=" * 80)
    print("✓ All tests complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_fixes())
