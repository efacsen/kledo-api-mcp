#!/usr/bin/env python3
"""
Test all 21 business intelligence queries for PT CSS
Document results, bottlenecks, and feature requests
"""
import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time

import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.auth import KledoAuthenticator
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache
from src.routing import route_query
from src.tools import financial, invoices, orders, products, contacts, deliveries, utilities


# Define all 21 test queries
TEST_QUERIES = {
    "Cash Flow & Collections": [
        "Siapa yang invoice-nya jatuh tempo minggu ini?",
        "Outstanding total berapa sekarang? Breakdown per customer",
        "Customer mana yang telat bayar >30 hari?",
        "Invoice mana yang udah >60 hari belum lunas?",
        "PI yang jatuh tempo bulan ini, total berapa?",
        "Outstanding ke vendor X berapa?",
        "Vendor mana yang harus dibayar minggu depan?"
    ],
    "Revenue Tracking": [
        "Revenue bulan ini vs bulan lalu, berapa %?",
        "Top 10 customer bulan ini",
        "Project mana yang paling profitable bulan ini?"
    ],
    "Customer Health": [
        "Customer yang biasanya bayar tapi sekarang telat, siapa aja?",
        "Customer baru yang transaksinya udah >50 juta",
        "Customer yang transaksinya turun vs 3 bulan lalu"
    ],
    "Sales Performance": [
        "Ranking sales rep bulan ini",
        "Pencapaian target bulan ini per sales gimana statusnya?"
    ],
    "Auto-notify Scenarios": [
        "Invoice >Rp 50 juta telat >7 hari",
        "Customer baru transaksi >Rp 20 juta",
        "Outstanding naik >20% vs minggu lalu",
        "Vendor invoice jatuh tempo dalam 3 hari"
    ],
    "Commission Calculations": [
        "Komisi Elmo bulan ini berapa? (paid invoices tgl 25-24)",
        "Breakdown komisi per sales rep Q1 2026"
    ]
}


async def execute_query_with_metrics(query: str, client: KledoAPIClient):
    """Execute query and capture detailed metrics."""
    result = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "execution_time": 0,
        "tool_name": None,
        "params": {},
        "routing_result": {},
        "output": None,
        "error": None,
        "bottlenecks": [],
        "api_calls": 0,
        "manual_processing_needed": False
    }
    
    start_time = time.time()
    
    try:
        # Route the query
        routing_result = route_query(query)
        result["routing_result"] = {
            "date_range": routing_result.date_range,
            "clarification_needed": routing_result.clarification_needed,
            "matched_tools_count": len(routing_result.matched_tools) if routing_result.matched_tools else 0
        }
        
        if routing_result.clarification_needed:
            result["error"] = f"Clarification needed: {routing_result.clarification_needed}"
            result["bottlenecks"].append("Missing disambiguation/clarification capability")
            return result
        
        if not routing_result.matched_tools:
            result["error"] = "No matching tools found"
            result["bottlenecks"].append("Query pattern not recognized by router")
            result["manual_processing_needed"] = True
            return result
        
        # Get top tool
        top_tool = routing_result.matched_tools[0]
        tool_name = top_tool.tool_name
        result["tool_name"] = tool_name
        
        # Build parameters
        params = {}
        if routing_result.date_range:
            params["date_from"] = routing_result.date_range[0]
            params["date_to"] = routing_result.date_range[1]
        
        if top_tool.suggested_params:
            params.update(top_tool.suggested_params)
        
        result["params"] = params
        
        # Execute the tool
        tool_result = None
        if tool_name.startswith("financial_"):
            tool_result = await financial.handle_tool(tool_name, params, client)
            result["api_calls"] = 1  # Estimate
        elif tool_name.startswith("invoice_"):
            tool_result = await invoices.handle_tool(tool_name, params, client)
            result["api_calls"] = 1
        elif tool_name.startswith("order_"):
            tool_result = await orders.handle_tool(tool_name, params, client)
            result["api_calls"] = 1
        elif tool_name.startswith("product_"):
            tool_result = await products.handle_tool(tool_name, params, client)
            result["api_calls"] = 1
        elif tool_name.startswith("contact_"):
            tool_result = await contacts.handle_tool(tool_name, params, client)
            result["api_calls"] = 1
        elif tool_name.startswith("delivery_"):
            tool_result = await deliveries.handle_tool(tool_name, params, client)
            result["api_calls"] = 1
        elif tool_name.startswith("utility_"):
            tool_result = await utilities.handle_tool(tool_name, params, client)
            result["api_calls"] = 1
        else:
            result["error"] = f"Unknown tool category: {tool_name}"
            result["bottlenecks"].append("Tool category not handled")
            return result
        
        result["output"] = str(tool_result)[:500]  # Truncate for readability
        result["success"] = True
        
        # Analyze bottlenecks
        if "aggregation" in query.lower() or "total" in query.lower():
            result["bottlenecks"].append("Client-side aggregation required")
        if "vs" in query.lower() or "comparison" in query.lower():
            result["bottlenecks"].append("Multi-period comparison requires multiple API calls")
        if "outstanding" in query.lower():
            result["bottlenecks"].append("Outstanding calculation requires filtering unpaid invoices")
        if "jatuh tempo" in query.lower() or "due" in query.lower():
            result["bottlenecks"].append("Due date filtering requires date range calculations")
        
    except Exception as e:
        result["error"] = str(e)
        result["bottlenecks"].append(f"Execution error: {str(e)[:100]}")
    
    finally:
        result["execution_time"] = time.time() - start_time
    
    return result


async def main():
    """Run all 21 test queries and generate report."""
    print("="*80)
    print("  TESTING 21 KLEDO API QUERIES FOR PT CSS")
    print("="*80)
    
    # Initialize client
    load_dotenv()
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")
    
    if not api_key or api_key == "kledo_pat_your_api_key_here":
        print("❌ ERROR: Valid KLEDO_API_KEY not found in .env file")
        return
    
    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.login()
    
    cache = KledoCache(enabled=True)
    endpoints_config = Path(__file__).parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(endpoints_config) if endpoints_config.exists() else None
    )
    
    print("✓ Connected to Kledo API\n")
    
    # Run all tests
    all_results = {}
    total_queries = sum(len(queries) for queries in TEST_QUERIES.values())
    current = 0
    
    for category, queries in TEST_QUERIES.items():
        print(f"\n{'='*80}")
        print(f"  CATEGORY: {category} ({len(queries)} queries)")
        print(f"{'='*80}\n")
        
        category_results = []
        
        for query in queries:
            current += 1
            print(f"[{current}/{total_queries}] Testing: {query}")
            
            result = await execute_query_with_metrics(query, client)
            category_results.append(result)
            
            status = "✓" if result["success"] else "✗"
            print(f"    {status} Time: {result['execution_time']:.2f}s | Tool: {result['tool_name'] or 'N/A'}")
            
            if result["error"]:
                print(f"    ⚠️  Error: {result['error'][:80]}")
            
            if result["bottlenecks"]:
                print(f"    🔍 Bottlenecks: {', '.join(result['bottlenecks'][:2])}")
            
            print()
            
            # Small delay between queries
            await asyncio.sleep(0.5)
        
        all_results[category] = category_results
    
    # Generate summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)
    
    total_success = sum(1 for cat_results in all_results.values() for r in cat_results if r["success"])
    total_failed = total_queries - total_success
    avg_time = sum(r["execution_time"] for cat_results in all_results.values() for r in cat_results) / total_queries
    
    print(f"\nTotal Queries: {total_queries}")
    print(f"Successful: {total_success} ({total_success/total_queries*100:.1f}%)")
    print(f"Failed: {total_failed} ({total_failed/total_queries*100:.1f}%)")
    print(f"Average Execution Time: {avg_time:.2f}s")
    
    # Count bottlenecks
    all_bottlenecks = {}
    for cat_results in all_results.values():
        for result in cat_results:
            for bottleneck in result["bottlenecks"]:
                all_bottlenecks[bottleneck] = all_bottlenecks.get(bottleneck, 0) + 1
    
    print(f"\n{'='*80}")
    print("  TOP BOTTLENECKS")
    print(f"{'='*80}")
    for bottleneck, count in sorted(all_bottlenecks.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {count:2d}x {bottleneck}")
    
    # Save results to JSON
    output_file = Path(__file__).parent / "test_results_21_queries.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_queries": total_queries,
                "successful": total_success,
                "failed": total_failed,
                "avg_execution_time": avg_time
            },
            "results": all_results,
            "bottlenecks": all_bottlenecks
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
