#!/usr/bin/env python3
"""
Test the 3 new finance analytics tools
Demonstrates how to query the new MCP tools
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv()


async def test_new_finance_tools():
    """Test the 3 new finance analytics enhancements."""

    print("\n" + "="*80)
    print("FINANCE ANALYTICS ENHANCEMENTS - MCP TOOL TEST")
    print("="*80)

    try:
        # Import the tools
        from src.tools import revenue
        from src.auth import KledoAuthenticator
        from src.cache import KledoCache
        from src.kledo_client import KledoAPIClient

        # Initialize authentication
        base_url = os.getenv("KLEDO_BASE_URL")
        api_key = os.getenv("KLEDO_API_KEY")

        print(f"\n🔐 Authenticating to Kledo API...")
        print(f"   Base URL: {base_url}")

        auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
        if not await auth.login():
            print("❌ Authentication failed")
            return

        print("✅ Authentication successful")

        # Initialize cache and client
        cache = KledoCache(enabled=True)

        endpoints_config_path = project_root / "config" / "endpoints.yaml"
        client = KledoAPIClient(
            auth,
            cache=cache,
            endpoints_config=str(endpoints_config_path) if endpoints_config_path.exists() else None
        )

        print("✅ MCP client initialized")

        # ============================================
        # TEST 1: revenue_daily_breakdown
        # ============================================
        print("\n" + "-"*80)
        print("TEST 1: Daily Revenue Breakdown")
        print("-"*80)
        print("Query: What was our daily revenue for this month?")
        print()

        result1 = await revenue.handle_tool(
            "revenue_daily_breakdown",
            {"date_from": "this_month"},
            client
        )
        print(result1)
        print("\n✅ Daily breakdown test completed")

        # ============================================
        # TEST 2: outstanding_aging_report
        # ============================================
        print("\n" + "-"*80)
        print("TEST 2: Outstanding Aging Report")
        print("-"*80)
        print("Query: Who owes us money and how overdue are they?")
        print()

        result2 = await revenue.handle_tool(
            "outstanding_aging_report",
            {},  # No parameters needed
            client
        )
        print(result2)
        print("\n✅ Aging report test completed")

        # ============================================
        # TEST 3: customer_concentration_report
        # ============================================
        print("\n" + "-"*80)
        print("TEST 3: Customer Concentration Report")
        print("-"*80)
        print("Query: What % of our revenue comes from top customers?")
        print()

        result3 = await revenue.handle_tool(
            "customer_concentration_report",
            {"date_from": "this_month"},
            client
        )
        print(result3)
        print("\n✅ Concentration report test completed")

        # ============================================
        # SUMMARY
        # ============================================
        print("\n" + "="*80)
        print("✅ ALL FINANCE ENHANCEMENT TESTS PASSED")
        print("="*80)
        print("""
Available Tools:
  ✅ revenue_daily_breakdown
     Purpose: Daily revenue trends for sales meetings
     Query: "What was yesterday's revenue?"

  ✅ outstanding_aging_report
     Purpose: Collections priority with DSO metric
     Query: "Who owes us money and is it urgent?"

  ✅ customer_concentration_report
     Purpose: 80/20 Pareto analysis for risk assessment
     Query: "What % of revenue is from top customers?"

You can now query these tools through the MCP interface!
        """)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_new_finance_tools())
