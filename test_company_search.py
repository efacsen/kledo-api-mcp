#!/usr/bin/env python3
"""
Test Kledo API search behavior for company names.
Verify which fields the API 'search' parameter actually searches.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.auth import KledoAuthenticator
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache

load_dotenv()

async def test_search():
    """Test various search terms to understand API behavior."""
    
    print("=" * 80)
    print("KLEDO API SEARCH BEHAVIOR TEST")
    print("=" * 80)
    
    # Initialize client
    auth = KledoAuthenticator(
        base_url=os.getenv("KLEDO_BASE_URL", "https://ptcepatservicestation.api.kledo.com/api/v1"),
        api_key=os.getenv("KLEDO_API_KEY")
    )
    
    await auth.login()
    print("✓ Authenticated\n")
    
    cache = KledoCache(enabled=False)  # Disable cache for testing
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(Path(__file__).parent / "config" / "endpoints.yaml")
    )
    
    # Test terms
    test_cases = [
        ("Nippon", "Known company (PT Nippon Paint)"),
        ("Nipsea", "Typo variation"),
        ("Nipon", "Typo variation 2"),
        ("PT Nippon", "With prefix"),
    ]
    
    for search_term, description in test_cases:
        print(f"\n{'=' * 80}")
        print(f"TEST: '{search_term}' ({description})")
        print('=' * 80)
        
        try:
            # Test sales invoices
            data = await client.list_invoices(
                search=search_term,
                per_page=10,
                force_refresh=True
            )
            
            invoices = data.get("data", {}).get("data", [])
            
            print(f"\n✓ Found {len(invoices)} sales invoices\n")
            
            if invoices:
                print("Results:")
                for i, inv in enumerate(invoices[:5], 1):  # Show max 5
                    ref = inv.get("ref_number", "N/A")
                    contact_name = inv.get("contact", {}).get("name", "")
                    company_name = inv.get("contact", {}).get("company", "")
                    
                    print(f"\n  [{i}] Invoice: {ref}")
                    print(f"      Contact Name: {contact_name}")
                    print(f"      Company Name: {company_name}")
                    
                    # Highlight which field matched
                    search_lower = search_term.lower()
                    name_match = search_lower in (contact_name or "").lower()
                    company_match = search_lower in (company_name or "").lower()
                    ref_match = search_lower in (ref or "").lower()
                    
                    matches = []
                    if name_match:
                        matches.append("contact.name")
                    if company_match:
                        matches.append("contact.company")
                    if ref_match:
                        matches.append("ref_number")
                    
                    if matches:
                        print(f"      ✓ Matched: {', '.join(matches)}")
                    else:
                        print(f"      ⚠ No exact match (fuzzy match by API?)")
            else:
                print("  ✗ No results found")
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("\nConclusions:")
    print("- Check which fields consistently matched across test cases")
    print("- Verify if API supports fuzzy search or exact match only")
    print("- Determine if company field is included in search\n")

if __name__ == "__main__":
    asyncio.run(test_search())
