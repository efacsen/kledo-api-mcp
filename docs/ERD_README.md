# Entity Relationship Diagram

## Generating the ERD

The ERD diagram (`erd.png`) is generated from Pydantic entity models using `erdantic`.

### Prerequisites

1. **Install Graphviz** (system binary required):
   ```bash
   # macOS
   brew install graphviz

   # Ubuntu/Debian
   sudo apt install graphviz

   # Windows (via chocolatey)
   choco install graphviz
   ```

2. **Install erdantic** (Python package):
   ```bash
   pip install erdantic
   ```

### Generate the Diagram

Run the generation script:

```bash
python scripts/generate_entity_docs.py
```

Or directly via Python:

```python
import erdantic as erd
from src.entities.models import Contact, Product, Invoice, Order, Delivery, Account

diagram = erd.create(Contact, Product, Invoice, Order, Delivery, Account)
diagram.draw("docs/erd.png")
```

## Entity Overview

The Kledo entity registry includes 6 main entities:

| Entity   | Description                        | Key Relationships       |
|----------|------------------------------------|-------------------------|
| Contact  | Customer or Vendor                 | Referenced by invoices  |
| Product  | Inventory item                     | Used in line items      |
| Invoice  | Sales/Purchase document            | Contains InvoiceItems   |
| Order    | Sales/Purchase order               | Contains OrderItems     |
| Delivery | Shipment document                  | Contains DeliveryItems  |
| Account  | Chart of accounts entry            | Used for GL posting     |

### Embedded Types

- `Warehouse` - Storage location for products
- `InvoiceItem` - Line item within an Invoice
- `OrderItem` - Line item within an Order
- `DeliveryItem` - Line item within a Delivery
