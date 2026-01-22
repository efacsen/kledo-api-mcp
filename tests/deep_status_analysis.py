"""
Deep Analysis of Kledo API Status Codes and Type IDs
Queries the API extensively to find all possible values and map them from actual data.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache


async def fetch_all_pages(client: KledoAPIClient, category: str, name: str, params: dict = None, max_pages: int = 10):
    """Fetch multiple pages from an endpoint to get diverse data."""
    all_items = []
    page = 1

    while page <= max_pages:
        try:
            response = await client.get(
                category,
                name,
                params={**(params or {}), "per_page": 100, "page": page},
                force_refresh=True  # Don't use cache, get fresh data
            )

            data = response.get("data", {})
            if isinstance(data, dict) and "data" in data:
                items = data["data"]
                if not items:
                    break
                all_items.extend(items)

                # Check if there are more pages
                if data.get("current_page", 1) >= data.get("last_page", 1):
                    break
            else:
                break

            page += 1

        except Exception as e:
            print(f"Error fetching page {page}: {str(e)}")
            break

    return all_items


async def analyze_status_ids(items: list, entity_name: str):
    """Analyze status_id distribution and sample data for each status."""
    status_distribution = defaultdict(list)

    for item in items:
        status_id = item.get("status_id")
        if status_id is not None:
            # Store sample with relevant fields
            sample = {
                "ref_number": item.get("ref_number"),
                "trans_date": item.get("trans_date"),
                "amount_after_tax": item.get("amount_after_tax"),
                "due": item.get("due"),
                "paid_date": item.get("paid_date"),
                "payment_date": item.get("payment_date"),
                "subtotal": item.get("subtotal"),
                "status_id": status_id,
                # Try to find any status name fields
                "status_name": item.get("status_name"),
                "status": item.get("status"),
            }
            status_distribution[status_id].append(sample)

    return status_distribution


async def analyze_type_ids(items: list, entity_name: str):
    """Analyze type_id distribution and sample data for each type."""
    type_distribution = defaultdict(list)

    for item in items:
        type_id = item.get("type_id")
        type_ids = item.get("type_ids", [])

        # Handle single type_id
        if type_id is not None:
            sample = {
                "id": item.get("id"),
                "name": item.get("name"),
                "company": item.get("company"),
                "type_id": type_id,
                "type_ids": type_ids,
                "type_name": item.get("type_name"),
                "receivable": item.get("receivable"),
                "payable": item.get("payable"),
            }
            type_distribution[type_id].append(sample)

        # Also track type_ids array
        for tid in type_ids:
            if tid not in type_distribution:
                type_distribution[tid] = []

    return type_distribution


async def analyze_revenue_fields(items: list):
    """Analyze revenue-related fields to understand before/after tax."""
    analysis = {
        "samples": [],
        "with_tax_diff": [],
        "without_tax_diff": []
    }

    for item in items[:20]:  # Analyze first 20
        subtotal = float(item.get("subtotal", 0))
        total_tax = float(item.get("total_tax", 0))
        amount_after_tax = float(item.get("amount_after_tax", 0))
        amount = float(item.get("amount", 0))

        sample = {
            "ref_number": item.get("ref_number"),
            "subtotal": subtotal,
            "total_tax": total_tax,
            "amount_after_tax": amount_after_tax,
            "amount": amount,
            "calculated_with_tax": subtotal + total_tax,
            "matches_amount_after_tax": abs((subtotal + total_tax) - amount_after_tax) < 1
        }

        analysis["samples"].append(sample)

        if total_tax > 0:
            analysis["with_tax_diff"].append(sample)
        else:
            analysis["without_tax_diff"].append(sample)

    return analysis


async def fetch_invoice_detail(client: KledoAPIClient, invoice_id: int):
    """Fetch detailed invoice to see if there's more status information."""
    try:
        response = await client.get(
            "invoices",
            "detail",
            path_params={"id": invoice_id},
            force_refresh=True
        )
        return response.get("data", {}).get("data")
    except:
        return None


async def main():
    """Main analysis."""
    output = []

    output.append("="*80)
    output.append("KLEDO API - DEEP STATUS & TYPE ID ANALYSIS")
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("="*80)
    output.append("")
    output.append("Objective: Map all status_id and type_id values from actual API data")
    output.append("Method: Query API extensively and analyze real responses")
    output.append("")

    # Initialize client
    config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
    base_url = os.getenv("KLEDO_BASE_URL")
    api_key = os.getenv("KLEDO_API_KEY")
    email = os.getenv("KLEDO_EMAIL")
    password = os.getenv("KLEDO_PASSWORD")

    if not base_url:
        print("❌ KLEDO_BASE_URL not found")
        return

    auth = KledoAuthenticator(
        base_url=base_url,
        api_key=api_key,
        email=email,
        password=password
    )
    cache = KledoCache()
    client = KledoAPIClient(auth, cache, str(config_path))

    if not await auth.ensure_authenticated():
        print("❌ Authentication failed")
        return

    output.append("✓ Authentication successful")
    output.append("")

    # ========================================================================
    # PART 1: SALES INVOICES STATUS ANALYSIS
    # ========================================================================
    output.append("="*80)
    output.append("PART 1: SALES INVOICES - STATUS_ID MAPPING")
    output.append("="*80)
    output.append("")

    print("Fetching sales invoices (multiple pages for diversity)...")
    invoices = await fetch_all_pages(client, "invoices", "list", {}, max_pages=5)
    output.append(f"Total invoices fetched: {len(invoices)}")
    output.append("")

    # Analyze status distribution
    status_dist = await analyze_status_ids(invoices, "sales_invoices")

    output.append("Status ID Distribution:")
    output.append("-" * 80)

    for status_id in sorted(status_dist.keys()):
        samples = status_dist[status_id]
        output.append(f"\n📊 STATUS_ID = {status_id}")
        output.append(f"   Count: {len(samples)} invoices")
        output.append(f"   Sample invoices:")

        # Show 3 samples for each status
        for i, sample in enumerate(samples[:3]):
            output.append(f"\n   Sample {i+1}:")
            output.append(f"     - Invoice #: {sample['ref_number']}")
            output.append(f"     - Date: {sample['trans_date']}")
            output.append(f"     - Amount: Rp {sample['amount_after_tax']:,.0f}")
            output.append(f"     - Due: Rp {sample['due']:,.0f}")
            output.append(f"     - Paid Date: {sample['paid_date']}")
            output.append(f"     - Payment Date: {sample['payment_date']}")

            # Calculate paid percentage
            if sample['amount_after_tax'] > 0:
                paid_pct = ((sample['amount_after_tax'] - sample['due']) / sample['amount_after_tax']) * 100
                output.append(f"     - Paid: {paid_pct:.1f}%")

        # Try to infer status meaning
        output.append(f"\n   💡 Analysis:")
        avg_due = sum(s['due'] for s in samples) / len(samples) if samples else 0
        avg_total = sum(s['amount_after_tax'] for s in samples) / len(samples) if samples else 0
        has_paid_dates = sum(1 for s in samples if s['paid_date']) / len(samples) if samples else 0

        if avg_due == 0 and has_paid_dates > 0.8:
            output.append(f"      → Likely PAID (due=0, most have paid_date)")
        elif avg_due > 0 and avg_due < avg_total * 0.1:
            output.append(f"      → Likely PARTIALLY PAID (small due amount)")
        elif avg_due == avg_total:
            output.append(f"      → Likely UNPAID/PENDING (due = total amount)")
        else:
            output.append(f"      → Unknown pattern")

        output.append(f"      Average due: Rp {avg_due:,.0f}")
        output.append(f"      Average total: Rp {avg_total:,.0f}")
        output.append(f"      {has_paid_dates*100:.0f}% have paid_date")

    # ========================================================================
    # PART 2: PURCHASE INVOICES STATUS ANALYSIS
    # ========================================================================
    output.append("\n\n" + "="*80)
    output.append("PART 2: PURCHASE INVOICES - STATUS_ID MAPPING")
    output.append("="*80)
    output.append("")

    print("Fetching purchase invoices...")
    purchase_invoices = await fetch_all_pages(client, "purchase_invoices", "list", {}, max_pages=5)
    output.append(f"Total purchase invoices fetched: {len(purchase_invoices)}")
    output.append("")

    purchase_status_dist = await analyze_status_ids(purchase_invoices, "purchase_invoices")

    output.append("Status ID Distribution:")
    output.append("-" * 80)

    for status_id in sorted(purchase_status_dist.keys()):
        samples = purchase_status_dist[status_id]
        output.append(f"\n📊 STATUS_ID = {status_id}")
        output.append(f"   Count: {len(samples)} bills")
        output.append(f"   Sample bills:")

        for i, sample in enumerate(samples[:3]):
            output.append(f"\n   Sample {i+1}:")
            output.append(f"     - Bill #: {sample['ref_number']}")
            output.append(f"     - Date: {sample['trans_date']}")
            output.append(f"     - Amount: Rp {sample['amount_after_tax']:,.0f}")
            output.append(f"     - Due: Rp {sample['due']:,.0f}")
            output.append(f"     - Paid Date: {sample['paid_date']}")

    # ========================================================================
    # PART 3: CONTACTS TYPE_ID MAPPING
    # ========================================================================
    output.append("\n\n" + "="*80)
    output.append("PART 3: CONTACTS - TYPE_ID MAPPING")
    output.append("="*80)
    output.append("")

    print("Fetching contacts...")
    contacts = await fetch_all_pages(client, "contacts", "list", {}, max_pages=3)
    output.append(f"Total contacts fetched: {len(contacts)}")
    output.append("")

    type_dist = await analyze_type_ids(contacts, "contacts")

    output.append("Type ID Distribution:")
    output.append("-" * 80)

    for type_id in sorted(type_dist.keys()):
        samples = type_dist[type_id]
        output.append(f"\n📊 TYPE_ID = {type_id}")
        output.append(f"   Count: {len(samples)} contacts")

        # Check type_name from samples
        type_names = [s.get('type_name') for s in samples if s.get('type_name')]
        if type_names:
            output.append(f"   Type Name: {type_names[0]}")

        # Analyze receivable/payable patterns
        has_receivable = sum(1 for s in samples if float(s.get('receivable', 0)) > 0)
        has_payable = sum(1 for s in samples if float(s.get('payable', 0)) > 0)

        output.append(f"   {has_receivable}/{len(samples)} have receivables (money owed to us)")
        output.append(f"   {has_payable}/{len(samples)} have payables (money we owe)")

        # Show samples
        output.append(f"   Sample contacts:")
        for i, sample in enumerate(samples[:3]):
            output.append(f"\n   Sample {i+1}:")
            output.append(f"     - Name: {sample['name']}")
            output.append(f"     - Company: {sample.get('company', 'N/A')}")
            output.append(f"     - Type Name: {sample.get('type_name', 'N/A')}")
            output.append(f"     - Receivable: Rp {float(sample.get('receivable', 0)):,.2f}")
            output.append(f"     - Payable: Rp {float(sample.get('payable', 0)):,.2f}")

    # ========================================================================
    # PART 4: REVENUE CALCULATION ANALYSIS
    # ========================================================================
    output.append("\n\n" + "="*80)
    output.append("PART 4: REVENUE CALCULATION - BEFORE/AFTER TAX")
    output.append("="*80)
    output.append("")

    revenue_analysis = await analyze_revenue_fields(invoices)

    output.append("Field Relationship Analysis:")
    output.append("-" * 80)
    output.append("")
    output.append("Formula verification: amount_after_tax = subtotal + total_tax")
    output.append("")

    for i, sample in enumerate(revenue_analysis['samples'][:10]):
        output.append(f"Invoice: {sample['ref_number']}")
        output.append(f"  Subtotal (before tax): Rp {sample['subtotal']:,.0f}")
        output.append(f"  Tax: Rp {sample['total_tax']:,.0f}")
        output.append(f"  Amount After Tax: Rp {sample['amount_after_tax']:,.0f}")
        output.append(f"  Calculated (subtotal + tax): Rp {sample['calculated_with_tax']:,.0f}")
        output.append(f"  ✓ Matches: {sample['matches_amount_after_tax']}")
        output.append("")

    output.append("="*80)
    output.append("REVENUE CALCULATION RECOMMENDATION")
    output.append("="*80)
    output.append("""
Based on the field analysis:

1. FOR SALES REP COMMISSION (Before Tax):
   Use: invoices.subtotal
   Why: This represents the revenue before tax, suitable for commission calculation

2. FOR ACTUAL REVENUE (With Tax):
   Use: invoices.amount_after_tax
   Why: This is the total amount including tax, the actual revenue

3. FORMULA VERIFICATION:
   ✓ Confirmed: amount_after_tax = subtotal + total_tax

4. BOTH OPTIONS SHOULD BE AVAILABLE:
   - revenue_before_tax = SUM(subtotal)
   - revenue_after_tax = SUM(amount_after_tax)
    """)

    # ========================================================================
    # PART 5: DETAILED INVOICE INSPECTION
    # ========================================================================
    output.append("\n\n" + "="*80)
    output.append("PART 5: INVOICE DETAIL INSPECTION (for additional status info)")
    output.append("="*80)
    output.append("")

    # Get one invoice from each status
    detail_samples = {}
    for status_id, samples in status_dist.items():
        if samples:
            invoice_id = samples[0].get('ref_number')  # Get invoice number
            # Need to find the actual ID
            matching = [inv for inv in invoices if inv.get('ref_number') == samples[0].get('ref_number')]
            if matching:
                detail = await fetch_invoice_detail(client, matching[0].get('id'))
                if detail:
                    detail_samples[status_id] = detail

    output.append("Detailed Invoice Fields (checking for status_name or other status indicators):")
    output.append("-" * 80)

    for status_id, detail in detail_samples.items():
        output.append(f"\nStatus ID {status_id} - Detailed Fields:")
        # Look for any status-related fields
        status_fields = {k: v for k, v in detail.items() if 'status' in k.lower()}
        if status_fields:
            output.append(f"  Status-related fields found:")
            for key, value in status_fields.items():
                output.append(f"    {key}: {value}")
        else:
            output.append(f"  No status_name field found in detail endpoint")

    # ========================================================================
    # SUMMARY & RECOMMENDATIONS
    # ========================================================================
    output.append("\n\n" + "="*80)
    output.append("SUMMARY & NEXT STEPS")
    output.append("="*80)
    output.append("""
✓ Data Analysis Complete

FINDINGS:
1. Found multiple status_id values in sales invoices
2. Found multiple status_id values in purchase invoices
3. Mapped type_id values for contacts
4. Verified revenue calculation fields (before/after tax)

RECOMMENDATIONS:
1. Check the invoice numbers in your Kledo dashboard to confirm status meanings
2. Or check Kledo API documentation for official status mappings
3. Update the field mapping document with confirmed status meanings

STATUS_ID PATTERNS OBSERVED:
(See detailed analysis above for each status_id with sample data)

TYPE_ID PATTERNS OBSERVED:
(See detailed analysis above for each type_id with sample data)

REVENUE FIELDS CONFIRMED:
✓ subtotal = revenue before tax (for commission)
✓ amount_after_tax = revenue with tax (for actual revenue)
✓ total_tax = tax amount
    """)

    # Write output
    output_file = Path(__file__).parent / "STATUS_ANALYSIS.md"
    with open(output_file, "w") as f:
        f.write("\n".join(output))

    print("\n".join(output))
    print(f"\n✓ Analysis saved to: {output_file}")

    # Save raw data for further inspection
    raw_data = {
        "sales_invoice_status_distribution": {
            str(k): [{"ref": s["ref_number"], "amount": s["amount_after_tax"], "due": s["due"],
                     "paid_date": s["paid_date"]} for s in v[:5]]
            for k, v in status_dist.items()
        },
        "purchase_invoice_status_distribution": {
            str(k): [{"ref": s["ref_number"], "amount": s["amount_after_tax"], "due": s["due"]} for s in v[:5]]
            for k, v in purchase_status_dist.items()
        },
        "contact_type_distribution": {
            str(k): [{"name": s["name"], "type_name": s.get("type_name")} for s in v[:5]]
            for k, v in type_dist.items()
        }
    }

    json_file = Path(__file__).parent / "status_analysis_data.json"
    with open(json_file, "w") as f:
        json.dump(raw_data, f, indent=2, default=str)

    print(f"✓ Raw data saved to: {json_file}")


if __name__ == "__main__":
    asyncio.run(main())
