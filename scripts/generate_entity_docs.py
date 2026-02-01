#!/usr/bin/env python
"""Generate entity documentation (YAML schema and ERD)."""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.entities import export_yaml_schema


def main():
    """Generate YAML schema and ERD diagram."""
    # Generate YAML schema
    yaml_path = Path("src/entities/schemas/entities.yaml")
    export_yaml_schema(yaml_path)
    print(f"Generated: {yaml_path}")

    # Generate ERD (if erdantic available)
    try:
        import erdantic as erd
        from src.entities.models import (
            Contact,
            Product,
            Invoice,
            Order,
            Delivery,
            Account,
        )

        erd_path = Path("docs/erd.png")
        erd_path.parent.mkdir(parents=True, exist_ok=True)
        diagram = erd.create(Contact, Product, Invoice, Order, Delivery, Account)
        diagram.draw(str(erd_path))
        print(f"Generated: {erd_path}")
    except ImportError:
        print("Warning: erdantic not installed. Run: pip install erdantic")
    except Exception as e:
        print(f"Warning: Could not generate ERD: {e}")
        print("Ensure graphviz is installed: brew install graphviz (macOS)")


if __name__ == "__main__":
    main()
