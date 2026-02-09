#!/bin/bash
# Simple wrapper for natural language queries to Kledo API
cd ~/kledo-api-mcp
source venv/bin/activate 2>/dev/null || true

# Create a temporary Python script that takes command-line query
python3 - <<EOF "$@"
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

sys.path.insert(0, str(Path.home() / "kledo-api-mcp"))

from src.auth import KledoAuthenticator
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache
from src.routing import route_query
from src.tools import financial, invoices, orders, products, contacts, deliveries, utilities

async def execute_query(query: str):
    load_dotenv()
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")
    
    if not api_key or api_key == "kledo_pat_your_api_key_here":
        print("ERROR: Valid KLEDO_API_KEY not found")
        return None
    
    start_time = datetime.now()
    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.login()
    
    cache = KledoCache(enabled=True)
    endpoints_config = Path.home() / "kledo-api-mcp" / "config" / "endpoints.yaml"
    client = KledoAPIClient(
        auth,
        cache=cache,
        endpoints_config=str(endpoints_config) if endpoints_config.exists() else None
    )
    
    routing_result = route_query(query)
    
    if routing_result.clarification_needed:
        print(f"CLARIFICATION NEEDED: {routing_result.clarification_needed}")
        return None
    
    if not routing_result.matched_tools:
        print("NO MATCHING TOOLS FOUND")
        return None
    
    top_tool = routing_result.matched_tools[0]
    tool_name = top_tool.tool_name
    
    params = {}
    if routing_result.date_range:
        params["date_from"] = routing_result.date_range[0]
        params["date_to"] = routing_result.date_range[1]
    
    if top_tool.suggested_params:
        params.update(top_tool.suggested_params)
    
    if "list" in tool_name and "per_page" not in params:
        params["per_page"] = 10
    
    try:
        if tool_name.startswith("financial_"):
            result = await financial.handle_tool(tool_name, params, client)
        elif tool_name.startswith("invoice_"):
            result = await invoices.handle_tool(tool_name, params, client)
        elif tool_name.startswith("order_"):
            result = await orders.handle_tool(tool_name, params, client)
        elif tool_name.startswith("product_"):
            result = await products.handle_tool(tool_name, params, client)
        elif tool_name.startswith("contact_"):
            result = await contacts.handle_tool(tool_name, params, client)
        elif tool_name.startswith("delivery_"):
            result = await deliveries.handle_tool(tool_name, params, client)
        elif tool_name.startswith("utility_"):
            result = await utilities.handle_tool(tool_name, params, client)
        else:
            print(f"UNKNOWN TOOL: {tool_name}")
            return None
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"EXECUTION_TIME: {elapsed:.2f}s")
        print(f"TOOL: {tool_name}")
        print(f"PARAMS: {params}")
        print("RESULT:")
        print(result)
        return result
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: query.sh 'your natural language query'")
        sys.exit(1)
    
    query = sys.argv[1]
    asyncio.run(execute_query(query))
EOF
