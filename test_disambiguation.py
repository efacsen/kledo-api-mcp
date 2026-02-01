#!/usr/bin/env python3
"""
Test improved disambiguation UI
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.invoices import parse_invoice_selection

def test_parser():
    """Test invoice selection parser."""
    print("=" * 60)
    print("INVOICE SELECTION PARSER TEST")
    print("=" * 60)
    
    test_cases = [
        ("1", 10, "Single selection"),
        ("3", 10, "Single selection (3rd item)"),
        ("1,2,3", 10, "Multiple comma-separated"),
        ("1, 2, 3", 10, "Multiple with spaces"),
        ("1-5", 10, "Range selection"),
        ("all", 10, "All items"),
        ("semua", 10, "All items (Indonesian)"),
        ("summary", 10, "Summary/aggregate"),
        ("total", 10, "Summary (alternative)"),
        ("99", 10, "Out of range"),
        ("abc", 10, "Invalid input"),
    ]
    
    for selection, max_count, description in test_cases:
        action_type, indices = parse_invoice_selection(selection, max_count)
        
        print(f"\nInput: '{selection}' (max: {max_count})")
        print(f"Description: {description}")
        print(f"Result: action={action_type}, indices={indices}")
        
        if action_type == "single":
            print(f"→ Will show invoice #{indices[0] + 1}")
        elif action_type == "multiple":
            nums = [i + 1 for i in indices]
            print(f"→ Will show invoices: {nums}")
        elif action_type == "all":
            print(f"→ Will show all {len(indices)} invoices")
        elif action_type == "summary":
            print(f"→ Will show aggregate summary")
        elif action_type == "invalid":
            print(f"→ Invalid selection")
    
    print("\n" + "=" * 60)
    print("✓ All tests complete")
    print("=" * 60)

if __name__ == "__main__":
    test_parser()
