"""Entity loader utilities for programmatic access to Kledo entity definitions."""
from pathlib import Path
from typing import Type, TypeVar

import yaml
from pydantic import BaseModel

from .models import (
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

T = TypeVar("T", bound=BaseModel)

# Registry mapping entity names to their model classes
ENTITY_REGISTRY: dict[str, Type[BaseModel]] = {
    "contact": Contact,
    "product": Product,
    "invoice": Invoice,
    "order": Order,
    "delivery": Delivery,
    "account": Account,
}

# Embedded types (not top-level entities but used within entities)
EMBEDDED_TYPES: dict[str, Type[BaseModel]] = {
    "warehouse": Warehouse,
    "invoice_item": InvoiceItem,
    "order_item": OrderItem,
    "delivery_item": DeliveryItem,
}


def get_entity_class(entity_name: str) -> Type[BaseModel]:
    """Get the Pydantic model class for an entity by name.

    Args:
        entity_name: Entity name (case-insensitive), e.g., 'contact', 'invoice'

    Returns:
        The Pydantic model class

    Raises:
        KeyError: If entity name not found
    """
    name_lower = entity_name.lower()
    if name_lower in ENTITY_REGISTRY:
        return ENTITY_REGISTRY[name_lower]
    if name_lower in EMBEDDED_TYPES:
        return EMBEDDED_TYPES[name_lower]
    raise KeyError(
        f"Unknown entity: {entity_name}. Available: {list(ENTITY_REGISTRY.keys())}"
    )


def get_all_entities() -> dict[str, Type[BaseModel]]:
    """Get all top-level entity classes.

    Returns:
        Dict mapping entity names to their Pydantic model classes
    """
    return ENTITY_REGISTRY.copy()


def get_entity_schema(entity_name: str) -> dict:
    """Get JSON schema for an entity.

    Args:
        entity_name: Entity name

    Returns:
        JSON Schema dict for the entity
    """
    model_class = get_entity_class(entity_name)
    return model_class.model_json_schema()


def get_all_schemas() -> dict[str, dict]:
    """Get JSON schemas for all entities.

    Returns:
        Dict mapping entity names to their JSON schemas
    """
    schemas = {}
    for name, model_class in ENTITY_REGISTRY.items():
        schemas[name] = model_class.model_json_schema()
    return schemas


def export_yaml_schema(output_path: Path | str | None = None) -> str:
    """Export all entity schemas to YAML format.

    Args:
        output_path: Optional path to write YAML file

    Returns:
        YAML string of all schemas
    """
    schemas = get_all_schemas()

    # Add metadata header
    output = {
        "_meta": {
            "description": "Kledo Entity Schema Definitions",
            "version": "1.0.0",
            "entities": list(schemas.keys()),
        },
        **schemas,
    }

    yaml_str = yaml.dump(
        output, default_flow_style=False, sort_keys=False, allow_unicode=True
    )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml_str, encoding="utf-8")

    return yaml_str
