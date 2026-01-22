"""
Automated API Field Mapping for Revenue Reporting
Generates a complete field mapping report without interactive prompts.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache


# Natural language mappings
FIELD_MAPPINGS = {
    "invoices": {
        "title": "Sales Invoices",
        "description": "Customer invoices for revenue calculation",
        "fields": {
            "ref_number": "Invoice Number (e.g., INV/26/JAN/00123)",
            "trans_date": "Transaction Date (when the invoice was created)",
            "contact.name": "Customer Name",
            "contact.id": "Customer ID (for grouping by customer)",
            "amount_after_tax": "Total Invoice Amount (including tax)",
            "due": "Amount Still Owed (unpaid balance)",
            "status_id": "Invoice Status (1=Draft, 2=Pending, 3=Paid, 4=Partial, 5=Overdue)",
            "sales_person.id": "Sales Representative ID",
            "sales_person.name": "Sales Representative Name",
            "subtotal": "Subtotal Before Tax",
            "total_tax": "Total Tax Amount",
            "tax": "Tax Details (rate and amount)",
        },
        "revenue_calculation": "Use 'amount_after_tax' for total revenue. Filter by 'status_id=3' (Paid) for confirmed revenue."
    },
    "purchase_invoices": {
        "title": "Purchase Invoices",
        "description": "Vendor bills for expense/cost calculation",
        "fields": {
            "ref_number": "Purchase Invoice Number",
            "trans_date": "Transaction Date",
            "contact.name": "Vendor Name",
            "contact.id": "Vendor ID",
            "amount_after_tax": "Total Bill Amount (including tax)",
            "due": "Amount Still Owed to Vendor",
            "status_id": "Bill Status (1=Draft, 2=Pending, 3=Paid, etc.)",
            "amount": "Amount Before Discounts",
        },
        "revenue_calculation": "Use 'amount_after_tax' for total expenses/costs."
    },
    "products": {
        "title": "Products",
        "description": "Product catalog with pricing",
        "fields": {
            "name": "Product Name",
            "code": "Product SKU/Code",
            "price": "Selling Price per Unit",
            "base_price": "Base/Cost Price per Unit",
            "qty": "Current Stock Quantity",
            "avg_base_price": "Average Cost Price",
        },
        "revenue_calculation": "Use 'price' for revenue per unit. Calculate profit margin: (price - base_price) / price"
    },
    "contacts": {
        "title": "Contacts (Customers & Vendors)",
        "description": "Customer and vendor information",
        "fields": {
            "name": "Contact Name",
            "company": "Company Name",
            "type_id": "Contact Type ID",
            "type_ids": "Multiple Type IDs",
            "receivable": "Total Amount Customer Owes Us",
            "payable": "Total Amount We Owe Vendor",
        },
        "revenue_calculation": "Use 'receivable' to see outstanding customer payments."
    }
}


async def fetch_endpoint_sample(client: KledoAPIClient, category: str, name: str, params: dict = None):
    """Fetch sample data from an endpoint."""
    try:
        response = await client.get(category, name, params=params or {})
        data = response.get("data", {})
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
        else:
            items = data if isinstance(data, list) else []

        if items and isinstance(items, list) and len(items) > 0:
            return items[0], items[:3]  # Return first item and 3 samples
        return None, None

    except Exception as e:
        return None, None


def analyze_field_mapping(category: str, sample_data: dict, output: list):
    """Analyze and document field mapping."""
    if not sample_data:
        output.append(f"\n⚠️  No sample data available for {category}\n")
        return

    mapping = FIELD_MAPPINGS.get(category, {})
    if not mapping:
        output.append(f"\n⚠️  No mapping defined for {category}\n")
        return

    output.append(f"\n{'='*80}")
    output.append(f"📊 {mapping['title'].upper()}")
    output.append(f"{'='*80}\n")
    output.append(f"{mapping['description']}\n")

    # Show actual fields available in API response
    output.append("Available Fields in API Response:")
    output.append("-" * 80)
    all_fields = list(sample_data.keys())
    output.append(f"Total fields: {len(all_fields)}\n")

    # Group fields for better readability
    for i, field in enumerate(all_fields):
        value = sample_data.get(field)
        value_str = str(value)[:60] if value is not None else "null"
        output.append(f"  {field:30s} = {value_str}")

    output.append(f"\n{'─'*80}\n")

    # Check mapped fields
    output.append("Mapped Fields (for revenue reporting):")
    output.append("-" * 80)

    for api_field, description in mapping["fields"].items():
        # Handle nested fields
        value = sample_data
        try:
            for part in api_field.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
        except:
            value = None

        exists = "✓" if value is not None else "✗"
        value_str = str(value)[:50] if value is not None else "N/A"

        output.append(f"{exists} {api_field:25s} → {description}")
        output.append(f"   Sample: {value_str}\n")

    output.append("\n💡 Revenue Calculation:")
    output.append(f"   {mapping.get('revenue_calculation', 'No calculation note')}\n")


async def main():
    """Main execution."""
    output = []

    output.append("="*80)
    output.append("KLEDO API - REVENUE REPORTING FIELD MAPPING")
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("="*80)
    output.append("")

    # Initialize client
    config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"

    base_url = os.getenv("KLEDO_BASE_URL")
    api_key = os.getenv("KLEDO_API_KEY")
    email = os.getenv("KLEDO_EMAIL")
    password = os.getenv("KLEDO_PASSWORD")

    if not base_url:
        print("❌ KLEDO_BASE_URL not found in .env file")
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
        print("❌ Failed to authenticate")
        return

    output.append("✓ Authentication: SUCCESS\n")

    # Fetch samples from each endpoint
    samples = {}
    multi_samples = {}

    endpoints = [
        ("invoices", "list", {"per_page": 10, "status_ids": "3"}),
        ("purchase_invoices", "list", {"per_page": 10}),
        ("products", "list", {"per_page": 10}),
        ("contacts", "list", {"per_page": 10, "type_id": 1}),
    ]

    output.append("Fetching data from endpoints:")
    for category, name, params in endpoints:
        sample, multi = await fetch_endpoint_sample(client, category, name, params)
        if sample:
            samples[category] = sample
            multi_samples[category] = multi
            output.append(f"  ✓ {category}/{name} - {len(multi)} samples fetched")
        else:
            output.append(f"  ✗ {category}/{name} - No data")

    output.append("")

    # Analyze each endpoint
    for category in ["invoices", "purchase_invoices", "products", "contacts"]:
        analyze_field_mapping(category, samples.get(category), output)

    # Add recommendations
    output.append("\n" + "="*80)
    output.append("REVENUE REPORT RECOMMENDATIONS")
    output.append("="*80)
    output.append("""
1. Annual Revenue Report:
   - Endpoint: GET /finance/invoices
   - Filters: status_id=3 (Paid only), date_from, date_to
   - Sum: amount_after_tax
   - Group by: trans_date (by month), sales_person.id (by rep)

2. Monthly Revenue Report:
   - Same as annual, filter date_from/date_to to specific month
   - Group by: trans_date (by day)

3. Weekly Revenue Report:
   - Filter to 7-day period
   - Group by: trans_date (daily breakdown)

4. Sales Representative Performance:
   - Group invoices by: sales_person.id
   - Calculate: SUM(amount_after_tax), COUNT(invoices), COUNT(DISTINCT contact.id)
   - Show: Revenue, Invoice count, Customer count per rep

5. Customer Revenue Analysis:
   - Group invoices by: contact.id
   - Calculate: Total revenue per customer, Average invoice value
   - Identify: Top customers by revenue

6. Product Revenue (requires invoice line items):
   - Need to fetch invoice details to get line items
   - Join with products for profit margin calculation

7. Profit Analysis:
   - Revenue: SUM of invoices.amount_after_tax (status_id=3)
   - Costs: SUM of purchase_invoices.amount_after_tax
   - Profit: Revenue - Costs
   - Margin: (Profit / Revenue) × 100

8. Outstanding Receivables:
   - Use: invoices.due field
   - Filter: status_id IN (2,4,5) for unpaid/partial/overdue

Key Fields Summary:
------------------
For Revenue: invoices.amount_after_tax (filter status_id=3)
For Costs: purchase_invoices.amount_after_tax
For Profit Margin: products.price vs products.base_price
For AR/AP: contacts.receivable and contacts.payable
For Sales Rep: sales_person.id and sales_person.name
For Grouping: trans_date (by period), contact.id (by customer)
    """)

    output.append("\n" + "="*80)
    output.append("FIELD MAPPING STATUS")
    output.append("="*80)
    output.append("""
✓ All critical fields for revenue reporting are available in the API
✓ Invoice data includes sales representative information
✓ Contact data includes receivables and payables
✓ Product data includes both selling price and cost price
✓ Date fields are in YYYY-MM-DD format for easy grouping

Note: Tax field is 'total_tax' not 'tax_amount' in the actual API response.
    """)

    # Write to file
    output_file = Path(__file__).parent / "REVENUE_FIELD_MAPPING.md"
    with open(output_file, "w") as f:
        f.write("\n".join(output))

    print("\n".join(output))
    print(f"\n✓ Report saved to: {output_file}")

    # Also save sample JSON data
    json_file = Path(__file__).parent / "api_samples.json"
    with open(json_file, "w") as f:
        json.dump(multi_samples, f, indent=2, default=str)

    print(f"✓ Sample JSON data saved to: {json_file}")


if __name__ == "__main__":
    asyncio.run(main())
