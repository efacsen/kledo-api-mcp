"""
Interactive API Field Mapping for Revenue Reporting
This script fetches real data from Kledo API and creates natural language mappings.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache


# Natural language mappings we'll validate with the user
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
            "tax_amount": "Tax Amount",
        },
        "revenue_calculation": "Use 'amount_after_tax' for total revenue. Filter by 'status_id=3' (Paid) for confirmed revenue."
    },
    "purchase_invoices": {
        "title": "Purchase Invoices",
        "description": "Vendor bills for expense/cost calculation",
        "fields": {
            "ref_number": "Purchase Invoice Number (e.g., BILL/26/JAN/00123)",
            "trans_date": "Transaction Date",
            "contact.name": "Vendor Name",
            "contact.id": "Vendor ID",
            "amount_after_tax": "Total Bill Amount (including tax)",
            "due": "Amount Still Owed to Vendor",
            "status_id": "Bill Status (1=Draft, 2=Pending, 3=Paid, etc.)",
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
            "buy_price": "Cost Price per Unit (for profit calculation)",
            "qty": "Current Stock Quantity",
            "category_name": "Product Category",
        },
        "revenue_calculation": "Use 'price' for revenue per unit. Calculate profit margin: (price - buy_price) / price"
    },
    "contacts": {
        "title": "Contacts (Customers & Vendors)",
        "description": "Customer and vendor information",
        "fields": {
            "name": "Contact Name",
            "company": "Company Name",
            "type_name": "Contact Type (Customer/Vendor/Both)",
            "type_id": "Type ID (1=Customer, 2=Vendor, 3=Both)",
            "email": "Email Address",
            "phone": "Phone Number",
            "total_receivable": "Total Amount Customer Owes Us",
            "total_payable": "Total Amount We Owe Vendor",
        },
        "revenue_calculation": "Use 'total_receivable' to see outstanding customer payments."
    }
}


async def fetch_endpoint_sample(client: KledoAPIClient, category: str, name: str, params: dict = None):
    """Fetch sample data from an endpoint."""
    try:
        print(f"\n{'='*60}")
        print(f"Fetching: {category} / {name}")
        print(f"{'='*60}")

        response = await client.get(category, name, params=params or {})

        # Extract the actual data
        data = response.get("data", {})
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
        else:
            items = data if isinstance(data, list) else []

        if items:
            print(f"✓ Found {len(items)} items")
            # Show first item structure
            if isinstance(items, list) and len(items) > 0:
                sample = items[0]
                print(f"\nSample item keys: {list(sample.keys())}")
                return items[0]
            else:
                print(f"\nData structure: {type(items)}")
                return items
        else:
            print("✗ No items found")
            return None

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


async def analyze_field_mapping(category: str, sample_data: dict):
    """Analyze and display field mapping for user validation."""
    if not sample_data:
        print(f"\n⚠️  No sample data available for {category}")
        return

    mapping = FIELD_MAPPINGS.get(category, {})
    if not mapping:
        print(f"\n⚠️  No mapping defined for {category}")
        return

    print(f"\n" + "="*80)
    print(f"📊 {mapping['title'].upper()}")
    print(f"="*80)
    print(f"\n{mapping['description']}\n")

    print("Field Mappings (API Field → Natural Language):")
    print("-" * 80)

    # Check each mapped field
    for api_field, description in mapping["fields"].items():
        # Handle nested fields (e.g., "contact.name")
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

        print(f"{exists} {api_field:25s} → {description}")
        print(f"   Sample value: {value_str}")
        print()

    print("\n💡 Revenue Calculation Note:")
    print(f"   {mapping.get('revenue_calculation', 'No calculation note')}")
    print()


async def main():
    """Main execution."""
    print("="*80)
    print("KLEDO API - REVENUE REPORTING FIELD MAPPING ANALYSIS")
    print("="*80)
    print("\nThis script will:")
    print("1. Fetch sample data from key API endpoints")
    print("2. Show you the actual API response structure")
    print("3. Map API fields to natural language descriptions")
    print("4. Ask you to confirm if the mappings are correct")
    print()

    # Initialize client
    print("Initializing Kledo API client...")

    config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"

    # Get credentials from environment
    base_url = os.getenv("KLEDO_BASE_URL")
    api_key = os.getenv("KLEDO_API_KEY")
    email = os.getenv("KLEDO_EMAIL")
    password = os.getenv("KLEDO_PASSWORD")

    if not base_url:
        print("❌ KLEDO_BASE_URL not found in .env file")
        return

    # Initialize authenticator (prefer API key over email/password)
    auth = KledoAuthenticator(
        base_url=base_url,
        api_key=api_key,
        email=email,
        password=password
    )
    cache = KledoCache()
    client = KledoAPIClient(auth, cache, str(config_path))

    # Authenticate
    if not await auth.ensure_authenticated():
        print("❌ Failed to authenticate with Kledo API")
        return

    print("✓ Authenticated successfully\n")

    # Fetch samples from each endpoint
    samples = {}

    # 1. Sales Invoices
    samples["invoices"] = await fetch_endpoint_sample(
        client, "invoices", "list",
        {"per_page": 5, "status_ids": "3"}  # Get paid invoices
    )

    # 2. Purchase Invoices
    samples["purchase_invoices"] = await fetch_endpoint_sample(
        client, "purchase_invoices", "list",
        {"per_page": 5}
    )

    # 3. Products
    samples["products"] = await fetch_endpoint_sample(
        client, "products", "list",
        {"per_page": 5}
    )

    # 4. Contacts
    samples["contacts"] = await fetch_endpoint_sample(
        client, "contacts", "list",
        {"per_page": 5, "type_id": 1}  # Customers
    )

    # Now analyze and present mappings
    print("\n\n" + "="*80)
    print("FIELD MAPPING ANALYSIS")
    print("="*80)

    for category in ["invoices", "purchase_invoices", "products", "contacts"]:
        await analyze_field_mapping(category, samples.get(category))

        # Interactive confirmation
        print("\n" + "─"*80)
        user_input = input(f"Are these field mappings correct for {category}? (yes/no/skip): ").lower().strip()

        if user_input == "no":
            print("\n📝 Please describe what's incorrect:")
            feedback = input("> ")
            print(f"\n✓ Feedback recorded: {feedback}\n")
        elif user_input == "yes":
            print("✓ Mappings confirmed!\n")
        else:
            print("⊘ Skipped\n")

    # Summary
    print("\n" + "="*80)
    print("REVENUE REPORTING RECOMMENDATIONS")
    print("="*80)
    print("""
For Annual Revenue Report:
- Fetch all invoices where status_id=3 (Paid) for the year
- Sum the 'amount_after_tax' field
- Group by 'trans_date' to get monthly breakdown
- Group by 'sales_person.id' to see revenue per sales rep

For Monthly Revenue Report:
- Same as annual, but filter date_from and date_to to specific month
- Use 'trans_date' to group by day if needed

For Weekly Revenue Report:
- Filter date_from and date_to to 7-day period
- Group by 'trans_date' for daily breakdown within the week

For Profit Analysis:
- Revenue: Sum of invoices 'amount_after_tax'
- Costs: Sum of purchase_invoices 'amount_after_tax'
- Profit: Revenue - Costs

For Product Revenue:
- Join invoice line items with products
- Multiply product 'price' × quantity sold
- Calculate margin: (price - buy_price) / price
    """)

    print("\n✓ Analysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
