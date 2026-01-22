# Kledo MCP Server Documentation

MCP Server for Kledo accounting software API, enabling AI agents to query business data.

## Overview

This MCP (Model Context Protocol) server provides AI agents with structured access to Kledo accounting data including:

- **Contacts** - Customers and vendors
- **Products** - Product catalog with inventory tracking
- **Invoices** - Sales and purchase invoices
- **Orders** - Sales and purchase orders
- **Deliveries** - Shipment tracking
- **Accounts** - Bank and cash accounts

## Quick Start

### Using with Claude Desktop

Add the server to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "kledo": {
      "command": "python",
      "args": ["-m", "src.main"],
      "env": {
        "KLEDO_API_URL": "https://api.kledo.com",
        "KLEDO_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Documentation Sections

- [Entity Registry](entities/index.md) - Business entity models and relationships
- [Tools Catalog](tools/index.md) - Available MCP tools for querying data
