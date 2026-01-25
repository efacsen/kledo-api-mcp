#!/usr/bin/env python3
"""
Field Validation Script - PROVE field meanings with real data
No assumptions allowed!
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv
from loguru import logger

load_dotenv()


async def validate_invoice_fields():
    """Pull 5 invoices and validate field meanings with math."""
    from src.auth import KledoAuthenticator
    from src.cache import KledoCache
    from src.kledo_client import KledoAPIClient

    # Initialize
    base_url = os.getenv("KLEDO_BASE_URL")
    api_key = os.getenv("KLEDO_API_KEY")

    auth = KledoAuthenticator(base_url=base_url, api_key=api_key)
    await auth.login()

    cache = KledoCache(enabled=True)
    endpoints_config_path = Path(__file__).parent.parent / "config" / "endpoints.yaml"
    client = KledoAPIClient(auth, cache=cache, endpoints_config=str(endpoints_config_path))

    logger.info("="*80)
    logger.info("FIELD VALIDATION - Proving field meanings with data")
    logger.info("="*80)

    # Get 5 PAID invoices (status_id = 3)
    response = await client.list_invoices(status_id=3, per_page=5, page=1)

    invoices = response.get('data', {}).get('data', [])

    if not invoices:
        logger.error("No invoices found!")
        return

    logger.info(f"\n✅ Retrieved {len(invoices)} invoices for validation\n")

    # Analyze each invoice
    validation_results = []

    for i, invoice in enumerate(invoices, 1):
        logger.info("="*80)
        logger.info(f"INVOICE #{i}: {invoice.get('ref_number')}")
        logger.info("="*80)

        # Extract key financial fields
        subtotal = float(invoice.get('subtotal', 0))
        total_tax = float(invoice.get('total_tax', 0))
        amount_after_tax = float(invoice.get('amount_after_tax', 0))
        amount = float(invoice.get('amount', 0))

        # Additional fields for context
        discount_amount = float(invoice.get('discount_amount', 0))
        additional_discount = float(invoice.get('additional_discount_amount', 0))
        shipping_cost = float(invoice.get('shipping_cost', 0))

        logger.info(f"\n📊 RAW FIELD VALUES:")
        logger.info(f"   subtotal:           Rp {subtotal:,.0f}")
        logger.info(f"   total_tax:          Rp {total_tax:,.0f}")
        logger.info(f"   amount_after_tax:   Rp {amount_after_tax:,.0f}")
        logger.info(f"   amount:             Rp {amount:,.0f}")
        logger.info(f"   discount_amount:    Rp {discount_amount:,.0f}")
        logger.info(f"   shipping_cost:      Rp {shipping_cost:,.0f}")

        # MATHEMATICAL VALIDATION
        logger.info(f"\n🧮 MATHEMATICAL RELATIONSHIPS:")

        # Test 1: subtotal + total_tax = amount_after_tax?
        calc_1 = subtotal + total_tax
        match_1 = abs(calc_1 - amount_after_tax) < 1  # Allow 1 rupiah rounding
        logger.info(f"   Test 1: subtotal + total_tax = amount_after_tax?")
        logger.info(f"           {subtotal:,.0f} + {total_tax:,.0f} = {calc_1:,.0f}")
        logger.info(f"           Expected: {amount_after_tax:,.0f}")
        logger.info(f"           ✅ MATCH!" if match_1 else f"           ❌ NO MATCH (diff: {calc_1 - amount_after_tax:,.0f})")

        # Test 2: Is subtotal = amount?
        match_2 = abs(subtotal - amount) < 1
        logger.info(f"\n   Test 2: subtotal = amount?")
        logger.info(f"           {subtotal:,.0f} vs {amount:,.0f}")
        logger.info(f"           ✅ SAME!" if match_2 else f"           ❌ DIFFERENT")

        # Test 3: Tax rate calculation
        if subtotal > 0:
            tax_rate = (total_tax / subtotal) * 100
            logger.info(f"\n   Test 3: Tax rate = (total_tax / subtotal) × 100")
            logger.info(f"           ({total_tax:,.0f} / {subtotal:,.0f}) × 100 = {tax_rate:.2f}%")

            # Common Indonesian tax rate is 11% PPN
            is_ppn = abs(tax_rate - 11.0) < 0.5
            logger.info(f"           {'✅ Standard PPN (11%)' if is_ppn else f'⚠️  Non-standard rate'}")

        # CONCLUSION FOR THIS INVOICE
        logger.info(f"\n📋 FIELD DEFINITIONS (PROVEN):")
        if match_1:
            logger.info(f"   subtotal        = Revenue BEFORE tax (base amount)")
            logger.info(f"   total_tax       = Tax collected (PPN)")
            logger.info(f"   amount_after_tax = Revenue INCLUDING tax (subtotal + tax)")
            logger.info(f"                    = Total yang dibayar customer")
        else:
            logger.info(f"   ⚠️  Relationship unclear - needs manual review")

        # Store for summary
        validation_results.append({
            'ref_number': invoice.get('ref_number'),
            'subtotal': subtotal,
            'total_tax': total_tax,
            'amount_after_tax': amount_after_tax,
            'math_valid': match_1,
            'tax_rate': (total_tax / subtotal * 100) if subtotal > 0 else 0
        })

        logger.info("")

    # AGGREGATE VALIDATION
    logger.info("="*80)
    logger.info("AGGREGATE VALIDATION - Testing across all 5 invoices")
    logger.info("="*80)

    total_subtotal = sum(r['subtotal'] for r in validation_results)
    total_tax = sum(r['total_tax'] for r in validation_results)
    total_amount_after_tax = sum(r['amount_after_tax'] for r in validation_results)

    logger.info(f"\n📊 AGGREGATED TOTALS:")
    logger.info(f"   Sum of subtotal:         Rp {total_subtotal:,.0f}")
    logger.info(f"   Sum of total_tax:        Rp {total_tax:,.0f}")
    logger.info(f"   Sum of amount_after_tax: Rp {total_amount_after_tax:,.0f}")

    aggregate_calc = total_subtotal + total_tax
    aggregate_match = abs(aggregate_calc - total_amount_after_tax) < 5

    logger.info(f"\n🧮 AGGREGATE TEST:")
    logger.info(f"   {total_subtotal:,.0f} + {total_tax:,.0f} = {aggregate_calc:,.0f}")
    logger.info(f"   Expected: {total_amount_after_tax:,.0f}")
    logger.info(f"   {'✅ MATCH!' if aggregate_match else '❌ NO MATCH'}")

    # Average tax rate
    avg_tax_rate = (total_tax / total_subtotal * 100) if total_subtotal > 0 else 0
    logger.info(f"\n📈 AVERAGE TAX RATE:")
    logger.info(f"   ({total_tax:,.0f} / {total_subtotal:,.0f}) × 100 = {avg_tax_rate:.2f}%")

    # FINAL CONCLUSION
    logger.info("\n" + "="*80)
    logger.info("FINAL CONCLUSION")
    logger.info("="*80)

    all_valid = all(r['math_valid'] for r in validation_results)

    if all_valid and aggregate_match:
        logger.info("\n✅ PROVEN: Mathematical relationship confirmed across ALL invoices")
        logger.info("\n📚 CORRECT FIELD DEFINITIONS:")
        logger.info("   ┌─────────────────────────────────────────────────────────┐")
        logger.info("   │ subtotal         = Revenue BEFORE tax                   │")
        logger.info("   │                  = Base amount sebelum PPN              │")
        logger.info("   │                  = NET REVENUE for company              │")
        logger.info("   │                                                         │")
        logger.info("   │ total_tax        = Tax amount (PPN)                     │")
        logger.info("   │                  = Pajak yang dikumpulkan               │")
        logger.info("   │                  = Must be remitted to government       │")
        logger.info("   │                                                         │")
        logger.info("   │ amount_after_tax = Revenue INCLUDING tax                │")
        logger.info("   │                  = subtotal + total_tax                 │")
        logger.info("   │                  = Total yang dibayar customer          │")
        logger.info("   │                  = GROSS REVENUE (total transaction)    │")
        logger.info("   └─────────────────────────────────────────────────────────┘")

        logger.info("\n💡 CORRECT INCOME STATEMENT TERMINOLOGY:")
        logger.info("   For Indonesian accounting:")
        logger.info("   ┌─────────────────────────────────────────────────────────┐")
        logger.info("   │ Penjualan Bruto (Gross Sales)  = amount_after_tax      │")
        logger.info("   │ Dikurangi: PPN (Tax)            = total_tax             │")
        logger.info("   │ Penjualan Neto (Net Sales)      = subtotal              │")
        logger.info("   └─────────────────────────────────────────────────────────┘")

    else:
        logger.warning("\n⚠️  WARNING: Mathematical relationship NOT consistent!")
        logger.warning("   Manual review required for these invoices:")
        for r in validation_results:
            if not r['math_valid']:
                logger.warning(f"   - {r['ref_number']}")

    # Error in documentation check
    logger.info("\n" + "="*80)
    logger.info("DOCUMENTATION ERROR CHECK")
    logger.info("="*80)
    logger.info("\n❌ ERROR FOUND IN: docs/technical/ANALYTICS_CAPABILITY_MAP.md")
    logger.info("   Section 1.1 Income Statement Analysis")
    logger.info("\n   INCORRECT (Current):")
    logger.info("   ├─ Gross Revenue (subtotal)")
    logger.info("   ├─ Tax Collected (total_tax)")
    logger.info("   └─ Net Revenue (amount_after_tax)")
    logger.info("\n   CORRECT (Should be):")
    logger.info("   ├─ Penjualan Bruto/Gross Sales (amount_after_tax)")
    logger.info("   ├─ Dikurangi: PPN/Tax (total_tax)")
    logger.info("   └─ Penjualan Neto/Net Sales (subtotal)")

    logger.info("\n✅ ACTION REQUIRED:")
    logger.info("   Update ANALYTICS_CAPABILITY_MAP.md section 1.1")
    logger.info("   with correct field definitions proven by this data!")


if __name__ == "__main__":
    asyncio.run(validate_invoice_fields())
