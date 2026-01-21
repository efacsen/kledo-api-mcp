"""Kledo Entity Registry - Machine-readable entity definitions."""

from .models import (
    BaseEntity,
    Contact,
    Product,
    Warehouse,
    Invoice,
    InvoiceItem,
    Order,
    OrderItem,
    Delivery,
    DeliveryItem,
    Account,
)
from .loader import (
    get_entity_class,
    get_all_entities,
    get_entity_schema,
    get_all_schemas,
    export_yaml_schema,
    ENTITY_REGISTRY,
    EMBEDDED_TYPES,
)

__all__ = [
    # Models
    "BaseEntity",
    "Contact",
    "Product",
    "Warehouse",
    "Invoice",
    "InvoiceItem",
    "Order",
    "OrderItem",
    "Delivery",
    "DeliveryItem",
    "Account",
    # Loader functions
    "get_entity_class",
    "get_all_entities",
    "get_entity_schema",
    "get_all_schemas",
    "export_yaml_schema",
    "ENTITY_REGISTRY",
    "EMBEDDED_TYPES",
]
