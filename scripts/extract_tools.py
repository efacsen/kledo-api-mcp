#!/usr/bin/env python3
"""
Tool extraction script for Kledo MCP Server documentation.

Extracts tool metadata from all tool modules for catalog generation.
"""
import importlib
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

TOOL_MODULES = [
    "src.tools.invoices",
    "src.tools.contacts",
    "src.tools.products",
    "src.tools.orders",
    "src.tools.deliveries",
    "src.tools.financial",
    "src.tools.revenue",
    "src.tools.analytics",
    "src.tools.commission",
    "src.tools.sales_analytics",
    "src.tools.utilities",
]

# Domain mapping for organization
DOMAIN_MAP = {
    "invoices": {
        "invoice_list": "sales",
        "invoice_get": "sales",
        "invoice_summarize": "sales",
    },
    "orders": {
        "order_list": "sales",
        "order_get": "sales",
    },
    "contacts": {
        "contact_list": "crm",
        "contact_get": "crm",
    },
    "products": {
        "product_list": "inventory",
        "product_get": "inventory",
    },
    "deliveries": {
        "delivery_list": "inventory",
        "delivery_get": "inventory",
    },
    "financial": {
        "financial_activity": "finance",
        "financial_summary": "finance",
        "financial_balances": "finance",
    },
    "revenue": {
        "revenue_summary": "finance",
        "revenue_receivables": "finance",
        "revenue_ranking": "finance",
    },
    "analytics": {
        "analytics_compare": "analytics",
        "analytics_targets": "analytics",
    },
    "commission": {
        "commission_report": "analytics",
    },
    "sales_analytics": {
        "sales_rep_report": "analytics",
        "sales_rep_list": "analytics",
    },
    "utilities": {
        "utility_cache": "system",
        "utility_test_connection": "system",
    },
}

# Entity associations
ENTITY_MAP = {
    "invoice_list": "Invoice",
    "invoice_get": "Invoice",
    "invoice_summarize": "Invoice",
    "order_list": "Order",
    "order_get": "Order",
    "contact_list": "Contact",
    "contact_get": "Contact",
    "product_list": "Product",
    "product_get": "Product",
    "delivery_list": "Delivery",
    "delivery_get": "Delivery",
    "financial_activity": None,
    "financial_summary": None,
    "financial_balances": "Account",
    "revenue_summary": None,
    "revenue_receivables": None,
    "revenue_ranking": None,
    "analytics_compare": None,
    "analytics_targets": None,
    "commission_report": None,
    "sales_rep_report": None,
    "sales_rep_list": None,
    "utility_cache": None,
    "utility_test_connection": None,
}


def extract_tool_catalog() -> list[dict[str, Any]]:
    """Extract all tools from tool modules."""
    tools = []

    for module_path in TOOL_MODULES:
        module = importlib.import_module(module_path)
        module_name = module_path.split(".")[-1]
        domain_mappings = DOMAIN_MAP.get(module_name, {})

        for tool in module.get_tools():
            domain = domain_mappings.get(tool.name, "unknown")
            entity = ENTITY_MAP.get(tool.name)

            tools.append({
                "name": tool.name,
                "description": tool.description,
                "module": module_name,
                "domain": domain,
                "entity": entity,
                "parameters": tool.inputSchema.get("properties", {}),
                "required": tool.inputSchema.get("required", []),
            })

    return tools


def get_tools_by_domain(tools: list[dict]) -> dict[str, list[dict]]:
    """Group tools by business domain."""
    by_domain: dict[str, list[dict]] = {}

    for tool in tools:
        domain = tool["domain"]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(tool)

    return by_domain


def print_summary(tools: list[dict]) -> None:
    """Print tool catalog summary."""
    print(f"\nTotal tools: {len(tools)}")
    print("\nBy module:")

    modules = {}
    for tool in tools:
        mod = tool["module"]
        modules[mod] = modules.get(mod, 0) + 1

    for mod, count in sorted(modules.items()):
        print(f"  {mod}: {count}")

    print("\nBy domain:")
    domains = {}
    for tool in tools:
        dom = tool["domain"]
        domains[dom] = domains.get(dom, 0) + 1

    for dom, count in sorted(domains.items()):
        print(f"  {dom}: {count}")


if __name__ == "__main__":
    catalog = extract_tool_catalog()

    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        print_summary(catalog)
    else:
        print(json.dumps(catalog, indent=2))
