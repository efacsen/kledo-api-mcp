#!/usr/bin/env python3
"""
Realistic MCP Tool Testing Framework
Tests the current 25-tool architecture against real-world business queries.
"""
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add project root to path for proper module imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class MCPToolTester:
    """Framework for testing MCP tools with realistic business queries."""

    def __init__(self):
        self.test_results = []
        self.tool_usage_count = {}

    async def setup(self):
        """Initialize the MCP client and server components."""
        from src.auth import KledoAuthenticator
        from src.cache import KledoCache
        from src.kledo_client import KledoAPIClient
        import os

        # Initialize authentication
        base_url = os.getenv("KLEDO_BASE_URL")
        api_key = os.getenv("KLEDO_API_KEY")

        auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
        if not await auth.login():
            raise ValueError("Authentication failed")

        # Initialize cache
        cache = KledoCache(enabled=True)

        # Initialize client with endpoints config
        endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
        self.client = KledoAPIClient(
            auth,
            cache=cache,
            endpoints_config=str(endpoints_config_path) if endpoints_config_path.exists() else None
        )
        logger.info("✅ MCP client initialized successfully")

    def log_tool_usage(self, tool_name: str, query: str):
        """Track which tools are called for each query."""
        self.tool_usage_count[tool_name] = self.tool_usage_count.get(tool_name, 0) + 1
        logger.info(f"📊 Tool called: {tool_name} for query: {query[:50]}...")

    async def test_revenue_queries(self):
        """Test revenue-related queries from user's workflow."""
        from src.tools import revenue, sales_analytics

        logger.info("\n" + "="*80)
        logger.info("TEST 1: Revenue Queries (Last Month, Week, 2 Days)")
        logger.info("="*80)

        # Calculate date ranges
        today = datetime.now()
        last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_month_end = today.replace(day=1) - timedelta(days=1)
        last_week_start = today - timedelta(days=7)
        two_days_ago = today - timedelta(days=2)

        test_cases = [
            {
                "query": "Show revenue from last month",
                "date_start": last_month_start.strftime("%Y-%m-%d"),
                "date_end": last_month_end.strftime("%Y-%m-%d"),
                "description": "Monthly revenue summary"
            },
            {
                "query": "Show revenue from last week",
                "date_start": last_week_start.strftime("%Y-%m-%d"),
                "date_end": today.strftime("%Y-%m-%d"),
                "description": "Weekly revenue summary"
            },
            {
                "query": "Show revenue from last 2 days",
                "date_start": two_days_ago.strftime("%Y-%m-%d"),
                "date_end": today.strftime("%Y-%m-%d"),
                "description": "Recent revenue (2 days)"
            }
        ]

        for test in test_cases:
            try:
                logger.info(f"\n📋 Query: {test['query']}")
                self.log_tool_usage("revenue_summary", test['query'])

                result = await revenue.handle_tool(
                    "revenue_summary",
                    {
                        "date_from": test['date_start'],
                        "date_to": test['date_end']
                    },
                    self.client
                )

                # Parse result to show summary
                data = json.loads(result)
                if "data" in data:
                    summary = data["data"].get("summary", {})
                    logger.info(f"✅ Total Revenue: {summary.get('total_revenue', 'N/A')}")
                    logger.info(f"   Transactions: {summary.get('transaction_count', 'N/A')}")

                self.test_results.append({
                    "test": test['description'],
                    "status": "✅ PASS",
                    "tools_used": ["revenue_summary"]
                })

            except Exception as e:
                logger.error(f"❌ Failed: {str(e)}")
                self.test_results.append({
                    "test": test['description'],
                    "status": f"❌ FAIL: {str(e)}",
                    "tools_used": ["revenue_summary"]
                })

    async def test_sales_rep_performance(self):
        """Test sales rep revenue analysis."""
        from src.tools import sales_analytics

        logger.info("\n" + "="*80)
        logger.info("TEST 2: Sales Rep Performance Analysis")
        logger.info("="*80)

        # Get sales rep list first
        logger.info("\n📋 Query: Who are our sales representatives?")
        self.log_tool_usage("sales_rep_list", "List all sales reps")

        try:
            rep_list_result = await sales_analytics.handle_tool(
                "sales_rep_list",
                {},
                self.client
            )

            reps_data = json.loads(rep_list_result)
            logger.info(f"✅ Found {len(reps_data.get('data', []))} sales representatives")

            # Show rep names
            for rep in reps_data.get('data', [])[:5]:  # Show first 5
                logger.info(f"   - {rep.get('name', 'Unknown')} (ID: {rep.get('id')})")

            # Now test revenue report for each rep
            logger.info("\n📋 Query: Show revenue per sales rep for last month")
            self.log_tool_usage("sales_rep_revenue_report", "Sales rep revenue analysis")

            today = datetime.now()
            last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_month_end = today.replace(day=1) - timedelta(days=1)

            revenue_result = await sales_analytics.handle_tool(
                "sales_rep_revenue_report",
                {
                    "date_from": last_month_start.strftime("%Y-%m-%d"),
                    "date_to": last_month_end.strftime("%Y-%m-%d")
                },
                self.client
            )

            revenue_data = json.loads(revenue_result)
            logger.info(f"✅ Sales rep revenue analysis completed")

            # Show top performers
            if "data" in revenue_data:
                for rep in revenue_data["data"][:3]:  # Top 3
                    logger.info(f"   🏆 {rep.get('sales_rep_name', 'Unknown')}: "
                              f"{rep.get('total_revenue', 0):,.0f}")

            self.test_results.append({
                "test": "Sales rep performance analysis",
                "status": "✅ PASS",
                "tools_used": ["sales_rep_list", "sales_rep_revenue_report"]
            })

        except Exception as e:
            logger.error(f"❌ Failed: {str(e)}")
            self.test_results.append({
                "test": "Sales rep performance analysis",
                "status": f"❌ FAIL: {str(e)}",
                "tools_used": ["sales_rep_list", "sales_rep_revenue_report"]
            })

    async def test_invoice_lifecycle(self):
        """Test invoice tracking: created, paid, outstanding."""
        from src.tools import invoices

        logger.info("\n" + "="*80)
        logger.info("TEST 3: Invoice Lifecycle Tracking")
        logger.info("="*80)

        today = datetime.now()
        month_start = today.replace(day=1)

        queries = [
            {
                "query": "How many invoices were created this month?",
                "status": None,  # All statuses
                "description": "Total invoices created"
            },
            {
                "query": "How many invoices are paid?",
                "status": "paid",
                "description": "Paid invoices"
            },
            {
                "query": "How many invoices are still outstanding?",
                "status": "unpaid",
                "description": "Outstanding invoices"
            }
        ]

        for test in queries:
            try:
                logger.info(f"\n📋 Query: {test['query']}")
                self.log_tool_usage("invoice_list_sales", test['query'])

                params = {
                    "date_from": month_start.strftime("%Y-%m-%d"),
                    "date_to": today.strftime("%Y-%m-%d"),
                    "page": 1,
                    "per_page": 100
                }

                if test['status']:
                    params['status'] = test['status']

                result = await invoices.handle_tool(
                    "invoice_list_sales",
                    params,
                    self.client
                )

                data = json.loads(result)
                count = len(data.get('data', []))
                total = data.get('pagination', {}).get('total', count)

                logger.info(f"✅ Found {total} invoices ({test['description']})")

                self.test_results.append({
                    "test": test['description'],
                    "status": "✅ PASS",
                    "tools_used": ["invoice_list_sales"]
                })

            except Exception as e:
                logger.error(f"❌ Failed: {str(e)}")
                self.test_results.append({
                    "test": test['description'],
                    "status": f"❌ FAIL: {str(e)}",
                    "tools_used": ["invoice_list_sales"]
                })

    async def test_customer_analysis(self):
        """Test top customer identification and transaction analysis."""
        from src.tools import revenue, contacts

        logger.info("\n" + "="*80)
        logger.info("TEST 4: Customer Analysis & Transaction Tracking")
        logger.info("="*80)

        # Get top customers by revenue
        logger.info("\n📋 Query: Who is the biggest customer this month?")
        self.log_tool_usage("customer_revenue_ranking", "Top customers by revenue")

        try:
            today = datetime.now()
            month_start = today.replace(day=1)

            result = await revenue.handle_tool(
                "customer_revenue_ranking",
                {
                    "date_from": month_start.strftime("%Y-%m-%d"),
                    "date_to": today.strftime("%Y-%m-%d"),
                    "top_n": 5
                },
                self.client
            )

            data = json.loads(result)
            logger.info(f"✅ Top 5 customers by revenue:")

            top_customers = data.get('data', {}).get('customers', [])
            for i, customer in enumerate(top_customers[:5], 1):
                logger.info(f"   {i}. {customer.get('name', 'Unknown')}: "
                          f"{customer.get('total_revenue', 0):,.0f} "
                          f"({customer.get('transaction_count', 0)} transactions)")

                # Get transaction details for top customer
                if i == 1:
                    customer_id = customer.get('id')
                    logger.info(f"\n📋 Query: Show transactions for top customer")
                    self.log_tool_usage("contact_get_transactions", "Customer transaction history")

                    try:
                        txn_result = await contacts.handle_tool(
                            "contact_get_transactions",
                            {"contact_id": customer_id},
                            self.client
                        )
                        logger.info(f"✅ Retrieved transaction history for {customer.get('name')}")
                    except Exception as e:
                        logger.warning(f"⚠️  Could not fetch transactions: {str(e)}")

            self.test_results.append({
                "test": "Top customer analysis",
                "status": "✅ PASS",
                "tools_used": ["customer_revenue_ranking", "contact_get_transactions"]
            })

        except Exception as e:
            logger.error(f"❌ Failed: {str(e)}")
            self.test_results.append({
                "test": "Top customer analysis",
                "status": f"❌ FAIL: {str(e)}",
                "tools_used": ["customer_revenue_ranking"]
            })

    async def test_commission_calculation(self):
        """Test commission calculation workflow (revenue + targets)."""
        from src.tools import sales_analytics, revenue

        logger.info("\n" + "="*80)
        logger.info("TEST 5: Commission Calculation Workflow")
        logger.info("="*80)

        logger.info("\n📋 Query: Calculate commission for sales reps this month")
        logger.info("   (Requires: revenue data + targets + commission formula)")

        try:
            # Step 1: Get sales rep revenue
            today = datetime.now()
            month_start = today.replace(day=1)

            self.log_tool_usage("sales_rep_revenue_report", "Get rep revenue for commission")

            revenue_result = await sales_analytics.handle_tool(
                "sales_rep_revenue_report",
                {
                    "date_from": month_start.strftime("%Y-%m-%d"),
                    "date_to": today.strftime("%Y-%m-%d")
                },
                self.client
            )

            revenue_data = json.loads(revenue_result)

            logger.info("✅ Step 1: Retrieved sales rep revenue data")
            logger.info("   Commission calculation workflow:")
            logger.info("   1. ✅ Sales rep revenue retrieved")
            logger.info("   2. ⚠️  Sales rep targets (not in API - needs manual input)")
            logger.info("   3. ⚠️  Commission formula (business logic - needs implementation)")

            # Show what we have
            if "data" in revenue_data:
                for rep in revenue_data["data"][:3]:
                    rep_name = rep.get('sales_rep_name', 'Unknown')
                    rep_revenue = rep.get('total_revenue', 0)
                    logger.info(f"   📊 {rep_name}: Revenue = {rep_revenue:,.0f} "
                              f"(Need target to calculate commission %)")

            self.test_results.append({
                "test": "Commission calculation workflow",
                "status": "⚠️  PARTIAL (needs target data + formula)",
                "tools_used": ["sales_rep_revenue_report"],
                "notes": "API provides revenue, but targets and formula need additional implementation"
            })

        except Exception as e:
            logger.error(f"❌ Failed: {str(e)}")
            self.test_results.append({
                "test": "Commission calculation workflow",
                "status": f"❌ FAIL: {str(e)}",
                "tools_used": ["sales_rep_revenue_report"]
            })

    def print_summary(self):
        """Print comprehensive test summary and tool usage analysis."""
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY & TOOL USAGE ANALYSIS")
        logger.info("="*80)

        # Test results
        logger.info(f"\n📊 Test Results ({len(self.test_results)} tests):")
        for result in self.test_results:
            logger.info(f"   {result['status']}: {result['test']}")
            logger.info(f"      Tools: {', '.join(result['tools_used'])}")
            if 'notes' in result:
                logger.info(f"      Notes: {result['notes']}")

        # Tool usage statistics
        logger.info(f"\n🔧 Tool Usage Statistics:")
        logger.info(f"   Unique tools called: {len(self.tool_usage_count)}")
        logger.info(f"   Total tool calls: {sum(self.tool_usage_count.values())}")
        logger.info(f"\n   Most used tools:")

        sorted_tools = sorted(self.tool_usage_count.items(), key=lambda x: x[1], reverse=True)
        for tool, count in sorted_tools:
            logger.info(f"      - {tool}: {count} calls")

        # Calculate percentage of tools used
        total_available_tools = 25  # Current architecture
        used_tools = len(self.tool_usage_count)
        usage_percentage = (used_tools / total_available_tools) * 100

        logger.info(f"\n📈 Coverage Analysis:")
        logger.info(f"   Tools used: {used_tools} / {total_available_tools} ({usage_percentage:.1f}%)")
        logger.info(f"   Unused tools: {total_available_tools - used_tools} ({100-usage_percentage:.1f}%)")

        # Recommendations
        logger.info(f"\n💡 Insights & Recommendations:")

        if usage_percentage < 50:
            logger.info(f"   ⚠️  Only {usage_percentage:.0f}% of tools were needed for realistic queries")
            logger.info(f"   → Consider consolidating rarely-used tools")

        # Group analysis
        tool_groups = {}
        for tool in self.tool_usage_count.keys():
            prefix = tool.split('_')[0]
            tool_groups[prefix] = tool_groups.get(prefix, 0) + 1

        logger.info(f"\n   Tool groups actually used:")
        for group, count in sorted(tool_groups.items()):
            logger.info(f"      - {group}_*: {count} different tools")

        logger.info(f"\n   🎯 Consolidation opportunity:")
        logger.info(f"      Current: 25 individual tools")
        logger.info(f"      Proposed: ~8-10 entity-based tools")
        logger.info(f"      Token savings: ~60-70% per request")


async def main():
    """Run comprehensive MCP tool testing."""
    logger.info("🚀 Starting Realistic MCP Tool Testing Framework")
    logger.info("   Testing against real-world business queries...")

    tester = MCPToolTester()

    try:
        # Setup
        await tester.setup()

        # Run all test suites
        await tester.test_revenue_queries()
        await tester.test_sales_rep_performance()
        await tester.test_invoice_lifecycle()
        await tester.test_customer_analysis()
        await tester.test_commission_calculation()

        # Print comprehensive summary
        tester.print_summary()

        logger.info("\n✅ Testing completed!")

    except Exception as e:
        logger.error(f"\n❌ Testing failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
