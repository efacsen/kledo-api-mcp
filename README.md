# Kledo CRM MCP Server

A Model Context Protocol (MCP) server that provides AI agents with read-only access to Kledo CRM/Finance API data. This enables natural language queries for financial reports, invoices, orders, products, contacts, and delivery tracking.

## Features

- **Read-only access** to Kledo CRM data
- **30+ MCP tools** for querying financial and operational data
- **Smart caching** with configurable TTL for optimal performance
- **Natural language queries** via AI agents
- **Comprehensive coverage** of core CRM entities:
  - Financial reports (P&L, sales/purchase summaries, bank balances)
  - Invoices (sales & purchase)
  - Orders (sales & purchase)
  - Products & inventory
  - Contacts (customers & vendors)
  - Delivery tracking

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Kledo account with API access
- An MCP-compatible AI agent (e.g., Claude Desktop)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/kledo-api-mcp.git
   cd kledo-api-mcp
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Kledo credentials:
   ```
   KLEDO_EMAIL=your-email@example.com
   KLEDO_PASSWORD=your-password
   KLEDO_BASE_URL=https://api.kledo.com/api/v1
   ```

### Running the Server

#### Standalone Mode
```bash
python -m src.server
```

#### With Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "kledo-crm": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/kledo-api-mcp",
      "env": {
        "KLEDO_EMAIL": "your-email@example.com",
        "KLEDO_PASSWORD": "your-password"
      }
    }
  }
}
```

Restart Claude Desktop and the Kledo CRM tools will be available.

## Usage Examples

### Natural Language Queries

With the MCP server connected to an AI agent, you can ask questions like:

- "Show me all unpaid invoices from last month"
- "What's our total sales revenue for October 2024?"
- "Who are my top 10 customers by revenue?"
- "What's the current stock level for product SKU-123?"
- "Which deliveries are still pending?"
- "Show me the profit from the distribution channel last month"

### Using Tools Directly

The server exposes 30+ tools organized by category:

#### Financial Reports
- `financial_activity_team_report` - Team activity summary
- `financial_sales_summary` - Sales by customer
- `financial_purchase_summary` - Purchases by vendor
- `financial_bank_balances` - Current bank balances

#### Invoices
- `invoice_list_sales` - List sales invoices
- `invoice_get_detail` - Get invoice details
- `invoice_get_totals` - Invoice totals summary
- `invoice_list_purchase` - List purchase invoices

#### Orders
- `order_list_sales` - List sales orders
- `order_get_detail` - Get order details
- `order_list_purchase` - List purchase orders

#### Products
- `product_list` - List products with prices
- `product_get_detail` - Get product details
- `product_search_by_sku` - Find product by SKU

#### Contacts
- `contact_list` - List customers/vendors
- `contact_get_detail` - Get contact details
- `contact_get_transactions` - Transaction history

#### Deliveries
- `delivery_list` - List deliveries
- `delivery_get_detail` - Get delivery details
- `delivery_get_pending` - Pending deliveries

#### Utilities
- `utility_clear_cache` - Clear all cached data
- `utility_get_cache_stats` - Cache performance stats
- `utility_test_connection` - Test API connection

## Configuration

### Cache Configuration

Cache TTLs are configured in `config/cache_config.yaml`:

```yaml
cache_tiers:
  master_data:
    products: 7200        # 2 hours
    contacts: 7200        # 2 hours
  transactional:
    invoices: 1800        # 30 minutes
    orders: 1800          # 30 minutes
  analytical:
    reports: 3600         # 1 hour
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KLEDO_EMAIL` | Kledo account email | (required) |
| `KLEDO_PASSWORD` | Kledo account password | (required) |
| `KLEDO_BASE_URL` | API base URL | `https://api.kledo.com/api/v1` |
| `KLEDO_APP_CLIENT` | Device type | `android` |
| `CACHE_ENABLED` | Enable caching | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Architecture

The server follows a layered architecture:

```
┌─────────────────────────────────────┐
│         AI Agent (Claude)           │
└────────────────┬────────────────────┘
                 │ MCP Protocol
┌────────────────▼────────────────────┐
│         MCP Server Layer            │
│  (Tool Registration & Routing)      │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│         Tool Handlers               │
│  (Financial, Invoice, Order, etc)   │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│       Kledo API Client              │
│  (Request Management & Caching)     │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│      Authentication Layer           │
│   (Token Management & Refresh)      │
└────────────────┬────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────┐
│          Kledo API                  │
└─────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Project Structure

```
kledo-api-mcp/
├── src/
│   ├── server.py          # Main MCP server
│   ├── kledo_client.py    # API client
│   ├── auth.py            # Authentication
│   ├── cache.py           # Caching mechanism
│   ├── tools/             # Tool implementations
│   │   ├── financial.py
│   │   ├── invoices.py
│   │   ├── orders.py
│   │   ├── products.py
│   │   ├── contacts.py
│   │   ├── deliveries.py
│   │   └── utilities.py
│   └── utils/             # Helper utilities
├── config/                # Configuration files
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Security Considerations

- Store credentials in `.env` file (never commit to git)
- Use a dedicated read-only Kledo account
- Enable logging to monitor API usage
- Review cache settings for sensitive data

## Troubleshooting

### Authentication Errors

If you see authentication failures:
1. Verify credentials in `.env` file
2. Check if your Kledo account is active
3. Ensure API access is enabled for your account

### Cache Issues

Clear cache if you see stale data:
- Use `utility_clear_cache` tool
- Or delete the cache manually and restart

### Connection Errors

Test connectivity:
- Use `utility_test_connection` tool
- Check firewall settings
- Verify `KLEDO_BASE_URL` is correct

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check [API_MAPPING.md](API_MAPPING.md) for endpoint details
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for design documentation

## Roadmap

- [ ] Add write operations (with explicit user confirmation)
- [ ] Support for webhooks
- [ ] Advanced reporting and analytics
- [ ] Multi-company support
- [ ] Export to Excel/CSV
- [ ] Dashboard generation

## Acknowledgments

- Built with [MCP (Model Context Protocol)](https://github.com/anthropics/mcp)
- Powered by [Kledo API](https://www.kledo.com/)
