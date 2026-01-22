"""
Live test of sales analytics tools with real API data
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache
from src.tools import sales_analytics


async def test_sales_analytics():
    """Test the sales analytics tools."""
    print("="*100)
    print("SALES ANALYTICS TOOLS - LIVE TEST")
    print("="*100)
    print()

    # Load environment
    load_dotenv()

    # Initialize authenticator
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")

    if not api_key:
        print("❌ Error: KLEDO_API_KEY not found in .env")
        return

    print("Initializing...")
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

    print("✓ Client initialized")
    print()

    # Test 1: List sales reps
    print("="*100)
    print("TEST 1: sales_rep_list")
    print("="*100)
    print()

    result = await sales_analytics.handle_tool("sales_rep_list", {}, client)
    print(result)
    print()

    # Test 2: Revenue report for January 2026
    print("="*100)
    print("TEST 2: sales_rep_revenue_report (January 2026)")
    print("="*100)
    print()

    result = await sales_analytics.handle_tool(
        "sales_rep_revenue_report",
        {
            "start_date": "2026-01-01",
            "end_date": "2026-01-22",
            "group_by": "month"
        },
        client
    )
    print(result)
    print()

    # Test 3: Revenue report for last 7 days with daily breakdown
    print("="*100)
    print("TEST 3: sales_rep_revenue_report (Last 7 Days, Daily)")
    print("="*100)
    print()

    from datetime import date, timedelta
    today = date.today()
    week_ago = today - timedelta(days=7)

    result = await sales_analytics.handle_tool(
        "sales_rep_revenue_report",
        {
            "start_date": week_ago.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "group_by": "day"
        },
        client
    )
    print(result)
    print()

    print("="*100)
    print("TESTING COMPLETE ✅")
    print("="*100)


if __name__ == "__main__":
    asyncio.run(test_sales_analytics())
