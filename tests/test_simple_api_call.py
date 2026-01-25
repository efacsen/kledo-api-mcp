#!/usr/bin/env python3
"""
Simple test to see what the API actually returns
"""
import asyncio
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


async def test_simple_call():
    """Make a simple API call and print the raw response."""
    from src.auth import KledoAuthenticator
    from src.cache import KledoCache
    from src.kledo_client import KledoAPIClient
    from src.tools import revenue

    # Initialize
    base_url = os.getenv("KLEDO_BASE_URL")
    api_key = os.getenv("KLEDO_API_KEY")

    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.login()

    cache = KledoCache(enabled=True)
    endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(auth, cache=cache, endpoints_config=str(endpoints_config_path))

    logger.info("Client initialized successfully")

    # Test 1: Get revenue summary for this month
    logger.info("\n" + "="*80)
    logger.info("TEST: Revenue Summary for This Month")
    logger.info("="*80)

    result = await revenue.handle_tool(
        "revenue_summary",
        {"date_from": "this_month"},
        client
    )

    logger.info(f"\n📋 Result type: {type(result)}")
    logger.info(f"📋 Result length: {len(result) if result else 0}")
    logger.info(f"📋 Result preview:\n{result[:500] if result else '(empty)'}")

    # Test 2: Try direct API call
    logger.info("\n" + "="*80)
    logger.info("TEST: Direct API Call to list_invoices")
    logger.info("="*80)

    api_response = await client.list_invoices(status_id=3, per_page=5)
    logger.info(f"\n📋 API Response type: {type(api_response)}")
    logger.info(f"📋 API Response keys: {list(api_response.keys()) if isinstance(api_response, dict) else 'N/A'}")

    if isinstance(api_response, dict) and "data" in api_response:
        data_content = api_response["data"]
        logger.info(f"📋 'data' field type: {type(data_content)}")
        logger.info(f"📋 'data' field keys: {list(data_content.keys()) if isinstance(data_content, dict) else 'N/A'}")

        if isinstance(data_content, dict) and "data" in data_content:
            invoices = data_content["data"]
            logger.info(f"📋 Number of invoices: {len(invoices) if isinstance(invoices, list) else 'N/A'}")

            if invoices and len(invoices) > 0:
                logger.info(f"📋 First invoice keys: {list(invoices[0].keys())}")
                logger.info(f"📋 First invoice preview: {invoices[0]}")


if __name__ == "__main__":
    asyncio.run(test_simple_call())
