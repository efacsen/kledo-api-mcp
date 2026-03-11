#!/usr/bin/env python3
"""
Capture real Kledo API responses and save as sanitized JSON fixtures.

Hits the real API once per endpoint, preserves the full response structure
(every field name and nesting), then replaces actual values with generic
dummy data safe to commit to the repo.

Usage:
    python scripts/capture_api_fixtures.py

Output:
    tests/fixtures/*.json  (10 fixture files)

Requires:
    .env with KLEDO_API_KEY or KLEDO_EMAIL + KLEDO_PASSWORD
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.auth import KledoAuthenticator
from src.cache import KledoCache
from src.kledo_client import KledoAPIClient


# ---------------------------------------------------------------------------
# Sanitization helpers
# ---------------------------------------------------------------------------

_name_counter: dict[str, int] = {}

def _generic_name(prefix: str) -> str:
    _name_counter[prefix] = _name_counter.get(prefix, 0) + 1
    return f"{prefix} {_name_counter[prefix]}"


def sanitize(value, key: str = ""):
    """
    Recursively sanitize a value:
    - Dicts: sanitize each value
    - Lists: sanitize each item
    - Strings: replace with generic equivalent
    - Numbers: round to nearest sensible value
    - None / bool / int ids: keep as-is
    """
    if value is None or isinstance(value, bool):
        return value

    if isinstance(value, dict):
        return {k: sanitize(v, k) for k, v in value.items()}

    if isinstance(value, list):
        return [sanitize(item, key) for item in value]

    if isinstance(value, (int, float)):
        return _sanitize_number(value, key)

    if isinstance(value, str):
        return _sanitize_string(value, key)

    return value


def _sanitize_number(value, key: str) -> int | float:
    # IDs — keep small integers as-is
    if key.endswith("_id") or key == "id":
        return value

    # Prices / amounts — keep order of magnitude, round nicely
    if value == 0:
        return 0

    if isinstance(value, float) or value > 100:
        # Round to nearest 100k for large IDR amounts
        magnitude = 10 ** (len(str(int(abs(value)))) - 1)
        rounded = round(value / magnitude) * magnitude
        return rounded

    return value


def _sanitize_string(value: str, key: str) -> str:
    if not value:
        return value

    # Dates — keep format, shift to safe year
    if re.match(r"\d{4}-\d{2}-\d{2}", value):
        return re.sub(r"^\d{4}", "2024", value)

    # Invoice / ref numbers — keep format, replace digits
    if re.match(r"[A-Z]+/\d+/[A-Z]+/\d+", value):
        return re.sub(r"\d+", lambda m: "0" * len(m.group()), value)

    # Email addresses
    if "@" in value and "." in value:
        return "user@example.com"

    # Phone numbers
    if re.match(r"[\d\s\+\-\(\)]{7,}$", value.strip()):
        return "021-0000000"

    # URLs
    if value.startswith("http"):
        return "https://example.com"

    # Company / contact names — common Indonesian patterns
    for prefix in ["PT ", "CV ", "UD ", "PD ", "Toko "]:
        if value.upper().startswith(prefix.upper()):
            return f"{prefix}{_generic_name('Company')}"

    # Generic name fields
    if key in ("name", "contact_name", "user_name", "sales_name"):
        return _generic_name("Name")

    # Tax IDs
    if key == "npwp" or re.match(r"\d{15,}", value):
        return "000000000000000"

    # Addresses
    if key in ("address", "shipping_address") or len(value) > 40:
        return f"Jl. Generic No. {_name_counter.get('addr', 1)}, Jakarta"

    # Anything else: keep as-is (field names, status strings, codes)
    return value


# ---------------------------------------------------------------------------
# API client setup
# ---------------------------------------------------------------------------

async def build_client() -> KledoAPIClient:
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    api_key = os.getenv("KLEDO_API_KEY")
    endpoints_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"

    if api_key:
        auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    else:
        auth = KledoAuthenticator(
            base_url=base_url,
            email=os.getenv("KLEDO_EMAIL"),
            password=os.getenv("KLEDO_PASSWORD"),
            app_client=os.getenv("KLEDO_APP_CLIENT", "android"),
        )

    if not await auth.login():
        raise RuntimeError("Authentication failed — check your .env credentials")

    cache = KledoCache(enabled=False)
    return KledoAPIClient(auth, cache=cache, endpoints_config=str(endpoints_path))


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

async def fetch_list(client: KledoAPIClient, category: str, params: dict = None) -> dict:
    return await client.get(category, "list", params={"per_page": 5, **(params or {})})


async def fetch_detail(client: KledoAPIClient, category: str, item_id: int) -> dict:
    return await client.get(category, "detail", path_params={"id": item_id})


def first_id(response: dict) -> int | None:
    items = response.get("data", {}).get("data", [])
    if items and isinstance(items, list):
        return items[0].get("id")
    return None


def save_fixture(name: str, data: dict):
    path = Path(__file__).parent.parent / "tests" / "fixtures" / f"{name}.json"
    sanitized = sanitize(data)
    with open(path, "w") as f:
        json.dump(sanitized, f, indent=2, ensure_ascii=False, default=str)
    print(f"  ✅ Saved {path.name}")


# ---------------------------------------------------------------------------
# Main capture flow
# ---------------------------------------------------------------------------

async def main():
    print("🔌 Connecting to Kledo API...")
    client = await build_client()
    print("✅ Connected\n")

    # 1. Sales Invoices — fetch all 3 statuses and combine into one list
    print("📄 Fetching invoices (status 1=unpaid, 2=partial, 3=paid)...")
    inv_unpaid   = await fetch_list(client, "invoices", {"status_id": 1, "per_page": 2})
    inv_partial  = await fetch_list(client, "invoices", {"status_id": 2, "per_page": 2})
    inv_paid     = await fetch_list(client, "invoices", {"status_id": 3, "per_page": 2})

    combined_items = (
        (inv_unpaid.get("data", {}).get("data") or [])[:2]
        + (inv_partial.get("data", {}).get("data") or [])[:2]
        + (inv_paid.get("data", {}).get("data") or [])[:2]
    )
    invoices_list_response = {
        "data": {
            "data": combined_items,
            "current_page": 1,
            "last_page": 1,
            "total": len(combined_items),
        }
    }
    save_fixture("invoices_list", invoices_list_response)

    # 2. Invoice detail — use first paid invoice for richest data
    inv_id = first_id(inv_paid) or first_id(inv_unpaid)
    if inv_id:
        print(f"📄 Fetching invoice detail (id={inv_id})...")
        detail = await fetch_detail(client, "invoices", inv_id)
        save_fixture("invoice_detail", detail)
    else:
        print("  ⚠️  No invoice found for detail fixture")

    # 3. Purchase Invoices
    print("💸 Fetching purchase invoices...")
    pi_unpaid = await fetch_list(client, "purchase_invoices", {"status_id": 1, "per_page": 2})
    pi_paid   = await fetch_list(client, "purchase_invoices", {"status_id": 3, "per_page": 2})
    pi_items  = (
        (pi_unpaid.get("data", {}).get("data") or [])[:2]
        + (pi_paid.get("data", {}).get("data") or [])[:2]
    )
    save_fixture("purchase_invoices_list", {
        "data": {"data": pi_items, "current_page": 1, "last_page": 1, "total": len(pi_items)}
    })

    # 4. Orders — status 5=Open, 6=Partial, 7=Converted
    print("📋 Fetching orders...")
    ord_open   = await fetch_list(client, "orders", {"status_id": 5, "per_page": 2})
    ord_partial = await fetch_list(client, "orders", {"status_id": 6, "per_page": 2})
    ord_conv   = await fetch_list(client, "orders", {"status_id": 7, "per_page": 2})
    ord_items  = (
        (ord_open.get("data", {}).get("data") or [])[:2]
        + (ord_partial.get("data", {}).get("data") or [])[:2]
        + (ord_conv.get("data", {}).get("data") or [])[:2]
    )
    save_fixture("orders_list", {
        "data": {"data": ord_items, "current_page": 1, "last_page": 1, "total": len(ord_items)}
    })

    # 5. Order detail
    ord_id = first_id(ord_open) or first_id(ord_partial) or first_id(ord_conv)
    if ord_id:
        print(f"📋 Fetching order detail (id={ord_id})...")
        save_fixture("order_detail", await fetch_detail(client, "orders", ord_id))
    else:
        print("  ⚠️  No order found for detail fixture")

    # 6. Deliveries
    print("🚚 Fetching deliveries...")
    deliveries = await fetch_list(client, "deliveries")
    save_fixture("deliveries_list", deliveries)

    # 7. Delivery detail
    del_id = first_id(deliveries)
    if del_id:
        print(f"🚚 Fetching delivery detail (id={del_id})...")
        save_fixture("delivery_detail", await fetch_detail(client, "deliveries", del_id))
    else:
        print("  ⚠️  No delivery found for detail fixture")

    # 8. Contacts
    print("👥 Fetching contacts...")
    contacts = await fetch_list(client, "contacts", {"type_id": 2})  # customers
    save_fixture("contacts_list", contacts)

    # 9. Contact detail (with transactions)
    con_id = first_id(contacts)
    if con_id:
        print(f"👥 Fetching contact detail (id={con_id})...")
        save_fixture("contact_detail", await fetch_detail(client, "contacts", con_id))
    else:
        print("  ⚠️  No contact found for detail fixture")

    # 10. Products
    print("📦 Fetching products...")
    products = await fetch_list(client, "products")
    save_fixture("products_list", products)

    print("\n✅ All fixtures saved to tests/fixtures/")
    print("   Review the files, then commit them to the repo.")


if __name__ == "__main__":
    asyncio.run(main())
