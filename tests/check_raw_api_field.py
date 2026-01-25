#!/usr/bin/env python3
"""
Cek apakah amount_after_tax itu dari API atau buatan kita
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv
from loguru import logger

load_dotenv()


async def check_raw_api():
    """Check raw API response untuk lihat field aslinya."""
    from src.auth import KledoAuthenticator
    from src.cache import KledoCache
    from src.kledo_client import KledoAPIClient

    # Initialize
    base_url = os.getenv("KLEDO_BASE_URL")
    api_key = os.getenv("KLEDO_API_KEY")

    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.login()

    cache = KledoCache(enabled=False)  # Disable cache for fresh data
    endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(auth, cache=cache, endpoints_config=str(endpoints_config_path))

    logger.info("="*80)
    logger.info("RAW API FIELD CHECK - Kledo API Response")
    logger.info("="*80)

    # Get 1 invoice
    response = await client.list_invoices(status_id=3, per_page=1, page=1)

    logger.info("\n📡 RAW API RESPONSE STRUCTURE:")
    logger.info(f"   Type: {type(response)}")
    logger.info(f"   Keys: {list(response.keys())}")

    # Check if amount_after_tax exists
    invoices = response.get('data', {}).get('data', [])

    if invoices:
        invoice = invoices[0]

        logger.info(f"\n📄 SINGLE INVOICE (RAW JSON):")
        logger.info(f"   Invoice ID: {invoice.get('id')}")
        logger.info(f"   Ref Number: {invoice.get('ref_number')}")

        # Check financial fields
        logger.info(f"\n💰 FINANCIAL FIELDS (dari API):")

        financial_fields = [
            'amount',
            'subtotal',
            'total_tax',
            'amount_after_tax',
            'amount_after_tax_ori',
            'amount_ori',
            'due'
        ]

        for field in financial_fields:
            if field in invoice:
                value = invoice.get(field)
                logger.info(f"   ✅ '{field}': {value}")
            else:
                logger.info(f"   ❌ '{field}': NOT FOUND")

        # Show full raw JSON for this invoice (financial fields only)
        logger.info(f"\n📋 RAW JSON EXTRACT (Financial Fields Only):")
        logger.info("```json")
        financial_data = {k: invoice[k] for k in financial_fields if k in invoice}
        logger.info(json.dumps(financial_data, indent=2))
        logger.info("```")

        # CONCLUSION
        logger.info("\n" + "="*80)
        logger.info("CONCLUSION")
        logger.info("="*80)

        if 'amount_after_tax' in invoice:
            logger.info("\n✅ CONFIRMED: 'amount_after_tax' is a REAL field from Kledo API")
            logger.info("   This is NOT something we created!")
            logger.info("   This is the actual field name returned by the API.")
            logger.info(f"\n   Raw value: {invoice.get('amount_after_tax')}")
            logger.info(f"   Type: {type(invoice.get('amount_after_tax'))}")
        else:
            logger.info("\n❌ Field 'amount_after_tax' NOT FOUND in API response")


if __name__ == "__main__":
    asyncio.run(check_raw_api())
