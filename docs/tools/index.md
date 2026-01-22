# Tool Catalog

This page provides a complete catalog of all MCP tools available in the Kledo MCP Server. Tools are organized by business domain for easy discovery.

## Overview

The Kledo MCP Server exposes **23 tools** across **6 business domains**:

| Domain | Tools | Description |
|--------|-------|-------------|
| [Sales](sales/invoices.md) | 5 | Sales invoices and orders |
| [Purchases](purchases/invoices.md) | 2 | Purchase invoices and orders |
| [Inventory](inventory/products.md) | 6 | Products and deliveries |
| [Finance](finance/reports.md) | 4 | Financial reports and bank balances |
| [CRM](crm/contacts.md) | 3 | Customer and vendor management |
| [System](system/utilities.md) | 3 | Cache and connection utilities |

## Complete Tool List

| Tool | Domain | Description | Entity |
|------|--------|-------------|--------|
| [invoice_list_sales](sales/invoices.md#invoice_list_sales) | Sales | List sales invoices with optional filtering | [Invoice](../entities/invoice.md) |
| [invoice_get_detail](sales/invoices.md#invoice_get_detail) | Sales | Get detailed information about a specific invoice | [Invoice](../entities/invoice.md) |
| [invoice_get_totals](sales/invoices.md#invoice_get_totals) | Sales | Get summary totals for sales invoices | [Invoice](../entities/invoice.md) |
| [order_list_sales](sales/orders.md#order_list_sales) | Sales | List sales orders with optional filtering | [Order](../entities/order.md) |
| [order_get_detail](sales/orders.md#order_get_detail) | Sales | Get detailed information about a specific sales order | [Order](../entities/order.md) |
| [invoice_list_purchase](purchases/invoices.md#invoice_list_purchase) | Purchases | List purchase invoices (bills from vendors) | [Invoice](../entities/invoice.md) |
| [order_list_purchase](purchases/orders.md#order_list_purchase) | Purchases | List purchase orders with optional filtering | [Order](../entities/order.md) |
| [product_list](inventory/products.md#product_list) | Inventory | List products with prices and inventory | [Product](../entities/product.md) |
| [product_get_detail](inventory/products.md#product_get_detail) | Inventory | Get detailed information about a specific product | [Product](../entities/product.md) |
| [product_search_by_sku](inventory/products.md#product_search_by_sku) | Inventory | Search for a product by its SKU/code | [Product](../entities/product.md) |
| [delivery_list](inventory/deliveries.md#delivery_list) | Inventory | List deliveries/shipments | [Delivery](../entities/delivery.md) |
| [delivery_get_detail](inventory/deliveries.md#delivery_get_detail) | Inventory | Get detailed information about a specific delivery | [Delivery](../entities/delivery.md) |
| [delivery_get_pending](inventory/deliveries.md#delivery_get_pending) | Inventory | Get list of pending/undelivered orders | [Delivery](../entities/delivery.md) |
| [financial_activity_team_report](finance/reports.md#financial_activity_team_report) | Finance | Get team activity report for a date range | - |
| [financial_sales_summary](finance/reports.md#financial_sales_summary) | Finance | Get sales summary by contact for a period | - |
| [financial_purchase_summary](finance/reports.md#financial_purchase_summary) | Finance | Get purchase summary by vendor for a period | - |
| [financial_bank_balances](finance/reports.md#financial_bank_balances) | Finance | Get current balances for all bank accounts | [Account](../entities/account.md) |
| [contact_list](crm/contacts.md#contact_list) | CRM | List customers and vendors | [Contact](../entities/contact.md) |
| [contact_get_detail](crm/contacts.md#contact_get_detail) | CRM | Get detailed information about a contact | [Contact](../entities/contact.md) |
| [contact_get_transactions](crm/contacts.md#contact_get_transactions) | CRM | Get transaction history for a contact | [Contact](../entities/contact.md) |
| [utility_clear_cache](system/utilities.md#utility_clear_cache) | System | Clear all cached data | - |
| [utility_get_cache_stats](system/utilities.md#utility_get_cache_stats) | System | Get cache statistics and performance metrics | - |
| [utility_test_connection](system/utilities.md#utility_test_connection) | System | Test connection to Kledo API | - |

## Domain Pages

### Sales Domain

Tools for managing sales transactions:

- [Sales Invoices](sales/invoices.md) - Create, list, and view sales invoices
- [Sales Orders](sales/orders.md) - Manage sales orders

### Purchases Domain

Tools for managing procurement:

- [Purchase Invoices](purchases/invoices.md) - Vendor bills and purchase invoices
- [Purchase Orders](purchases/orders.md) - Purchase order management

### Inventory Domain

Tools for product and delivery management:

- [Products](inventory/products.md) - Product catalog and inventory levels
- [Deliveries](inventory/deliveries.md) - Shipment tracking and pending deliveries

### Finance Domain

Tools for financial reporting:

- [Reports](finance/reports.md) - Activity reports, sales/purchase summaries, bank balances

### CRM Domain

Tools for customer relationship management:

- [Contacts](crm/contacts.md) - Customer and vendor information

### System Domain

Utility tools for server management:

- [Utilities](system/utilities.md) - Cache management and connection testing

## Tool Introspection

The tool catalog is maintained through code introspection. To regenerate:

```bash
python scripts/extract_tools.py
```

This extracts tool metadata directly from the MCP tool definitions, ensuring documentation stays in sync with the implementation.
