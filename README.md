# Kledo MCP Server

Model Context Protocol (MCP) server for Kledo accounting software API - enables Claude AI to interact with your Kledo data for revenue reporting, sales analytics, customer management, and commission calculation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Key Features

- **28 Production-Ready Tools** - Complete coverage of Kledo API endpoints
- **100% Verified Field Mappings** - All status codes and fields verified from real API data (1,300+ records analyzed)
- **Dual Revenue Calculation** - Both before-tax (commission) and after-tax (actual) amounts
- **Paid-Only Commission** - Automatically filters by status_id=3 (Lunas/Paid) for accurate commission calculation
- **Bilingual Support** - Understands Indonesian and English queries
- **Smart Caching** - Configurable caching for optimal performance
- **Type-Safe** - Comprehensive type hints throughout

## 🚀 Quick Start in 2 Minutes

**First time setup:**

1. **Install the package:**
   ```bash
   git clone https://github.com/efacsen/kledo-api-mcp.git
   cd kledo-api-mcp
   pip install -e .
   ```

2. **Run the setup wizard:**
   ```bash
   kledo-mcp
   ```
   The interactive wizard will:
   - ✓ Prompt for your Kledo API key
   - ✓ Validate your connection
   - ✓ Create your `.env` configuration
   - ✓ Show you the Claude Desktop config to copy

3. **Copy the config to Claude Desktop:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

4. **Restart Claude Desktop** - Done! 🎉

**Every time after:**
```bash
kledo-mcp  # Just works - no setup needed
```

**Need help?** See [Troubleshooting](#-troubleshooting) below.

## 📊 Revenue & Commission Features

### Commission Calculation (Verified ✓)

Commission is calculated using **revenue BEFORE tax** (subtotal) from **PAID invoices only** (status_id=3):

```python
commission_base = SUM(subtotal WHERE status_id=3 AND date_range)
```

### Status Codes (Verified from Dashboard)

- **Status 1**: Belum Dibayar (Unpaid) - Not counted in commission
- **Status 2**: Dibayar Sebagian (Partially Paid) - Not counted in commission
- **Status 3**: Lunas (Paid) - **USE FOR COMMISSION CALCULATION**

### Revenue Formula (100% Verified)

```python
amount_after_tax = subtotal + total_tax
```

All tools show BOTH revenue calculations:
- **Before Tax** (subtotal) - For commission
- **After Tax** (amount_after_tax) - Actual revenue

## 🛠️ Available Tools (28 Total)

### Revenue & Analytics (8 tools)
- `revenue_summary` - Quick revenue for period (before/after tax)
- `outstanding_receivables` - Unpaid invoices tracking (piutang)
- `customer_revenue_ranking` - Top customers by revenue
- `sales_rep_revenue_report` - Sales rep performance with commission
- `sales_rep_list` - List all sales reps with revenue
- `invoice_list_sales` - Sales invoices list
- `invoice_get_detail` - Invoice details
- `invoice_get_totals` - Invoice totals summary

### Purchase/Expenses (1 tool)
- `invoice_list_purchase` - Purchase invoices

### Products (3 tools)
- `product_list` - List products
- `product_get_detail` - Product details
- `product_search_by_sku` - Search by SKU

### Customers/Contacts (3 tools)
- `contact_list` - List customers/vendors
- `contact_get_detail` - Contact details
- `contact_get_transactions` - Contact transaction history

### Orders (4 tools)
- `order_list_sales` - Sales orders
- `order_get_detail` - Order details
- `order_list_purchase` - Purchase orders
- `order_get_purchase_detail` - Purchase order details

### Deliveries (4 tools)
- `delivery_list` - List deliveries
- `delivery_get_detail` - Delivery details
- `delivery_list_pending` - Pending deliveries
- `delivery_get_by_order` - Deliveries by order

### Financial (1 tool)
- `financial_get_account_list` - Chart of accounts

### Utilities (4 tools)
- `utility_cache_clear` - Clear cache
- `utility_cache_stats` - Cache statistics
- `utility_test_connection` - Test API connection
- `utility_get_business_info` - Business information

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- Kledo account with API access
- Claude Code CLI, Claude Desktop, or any AI IDE that supports MCP

### Quick Install

1. **Clone and install:**
   ```bash
   git clone https://github.com/efacsen/kledo-api-mcp.git
   cd kledo-api-mcp
   pip install -e .
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Kledo credentials
   ```

3. **Your MCP server is now available as `kledo-mcp` command!**

### Configuration Options

**For Claude Desktop/CLI (Recommended):**
```json
{
  "mcpServers": {
    "kledo-crm": {
      "command": "kledo-mcp",
      "env": {
        "KLEDO_API_KEY": "your_api_key_here",
        "KLEDO_BASE_URL": "https://api.kledo.com/api/v1",
        "CACHE_ENABLED": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**For Other IDEs (like VS Code Copilot, etc.):**
Simply use `"command": "kledo-mcp"` with the environment variables above.

**Legacy Configuration (still works):**
If you prefer the old approach:
```json
{
  "mcpServers": {
    "kledo-crm": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/kledo-api-mcp",
      "env": {
        "KLEDO_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Manual Testing

You can test the server directly from anywhere:
```bash
# Start the MCP server
kledo-mcp

# Or use the old way (still works)
python -m src.server
```

### Getting Your Kledo API Key

1. Log in to your Kledo account at https://kledo.com
2. Go to **Settings** → **Integration** → **API**
3. Generate a new API key
4. Copy the key and add it to your `.env` file

**Security Note**: Never commit your `.env` file to version control. The `.gitignore` file already excludes it.

## 🚀 Usage Examples

### Get Monthly Revenue (with Commission Base)

Ask Claude:
```
"Berapa revenue bulan ini?"
"What's this month's revenue?"
```

Claude will use `revenue_summary` tool and return:
```
Revenue Summary (PAID INVOICES ONLY)
Period: 2026-01-01 to 2026-01-31
Paid Invoices: 45

Revenue Calculation:
Revenue Before Tax (for commission): Rp 96,373,250
Tax (PPN): Rp 9,068,950
Revenue After Tax (actual): Rp 105,442,200
```

### Sales Rep Commission Report

Ask Claude:
```
"Show sales rep performance for January"
"Siapa sales rep dengan revenue tertinggi bulan ini?"
```

Claude will use `sales_rep_revenue_report` tool showing:
- Revenue Before Tax (Commission base)
- Revenue After Tax (Actual revenue)
- Only PAID invoices (status_id=3)
- Monthly breakdown per rep
- Top deals sorted by commission amount

### Outstanding Receivables (Piutang)

Ask Claude:
```
"Siapa yang belum bayar?"
"Show outstanding invoices"
```

Claude will use `outstanding_receivables` tool showing:
- Belum Dibayar (Unpaid) - status_id=1
- Dibayar Sebagian (Partially Paid) - status_id=2
- Customer names, amounts, dates

### Top Customers by Revenue

Ask Claude:
```
"Who are our top 10 customers this month?"
"Customer dengan revenue tertinggi?"
```

Claude will use `customer_revenue_ranking` tool showing:
- Both before-tax and after-tax revenue
- Number of invoices
- Average invoice value
- Only PAID invoices

## 🔧 Configuration

### Cache Configuration

The server uses intelligent caching to reduce API calls. Configure in `config/cache_config.yaml`:

```yaml
default:
  ttl: 300
  max_size: 1000

categories:
  invoices:
    ttl: 60
  products:
    ttl: 3600
  contacts:
    ttl: 1800
```

### Endpoint Configuration

API endpoints are configured in `config/endpoints.yaml`. All endpoints are pre-configured for the Kledo API v1.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KLEDO_API_KEY` | Your Kledo API key (recommended) | - |
| `KLEDO_EMAIL` | Your Kledo email (legacy) | - |
| `KLEDO_PASSWORD` | Your Kledo password (legacy) | - |
| `KLEDO_BASE_URL` | Kledo API base URL | `https://api.kledo.com/api/v1` |
| `MCP_SERVER_NAME` | MCP server name | `kledo-crm` |
| `CACHE_ENABLED` | Enable/disable caching | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FILE` | Log file path (optional) | - |

## 📖 Documentation

- **[MCP_SERVER_UPDATES.md](MCP_SERVER_UPDATES.md)** - Complete changelog and update details
- **[tests/FINAL_FIELD_MAPPING.md](tests/FINAL_FIELD_MAPPING.md)** - Complete field reference (100% verified)
- **[tests/STATUS_ANALYSIS.md](tests/STATUS_ANALYSIS.md)** - Deep status code analysis from 1,300+ records
- **[.planning/phases/](./planning/phases/)** - Development phases and planning documents

## 🧪 Testing

### Run Verification Tests

All field mappings have been verified with real API data:

```bash
cd tests
python test_field_mappings.py
```

**Test Results**: 7/7 tests passed (100%)
- ✅ Status ID mappings (1=Unpaid, 2=Partial, 3=Paid)
- ✅ Revenue formula (amount_after_tax = subtotal + total_tax)
- ✅ Revenue calculation (before/after tax)
- ✅ Sales rep performance tracking
- ✅ Customer revenue analysis
- ✅ Outstanding receivables calculation
- ✅ Profit margin calculation

### Test API Connection

Ask Claude:
```
"Test connection to Kledo API"
```

Claude will use `utility_test_connection` to verify authentication and API access.

## 🐛 Troubleshooting

### MCP Server Not Showing in Claude

1. **Check configuration file location:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Verify JSON syntax** - Use a JSON validator to check for errors

3. **Check absolute path** - Ensure `cwd` points to the correct absolute path

4. **Restart Claude** completely (not just refresh)

5. **Check logs:**
   ```bash
   # macOS/Linux
   tail -f ~/Library/Logs/Claude/mcp*.log

   # Windows
   # Check %LOCALAPPDATA%\Claude\Logs\
   ```

### Authentication Errors

1. **Verify API key** in `.env` file
2. **Check API key permissions** in Kledo dashboard
3. **Test with curl:**
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.kledo.com/api/v1/finance/account
   ```

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Reinstall in development mode
pip install -e .

# Or install dependencies manually
pip install -r requirements.txt
```

### Cache Issues

Clear the cache if you see stale data:

Ask Claude:
```
"Clear Kledo cache"
```

Or disable caching in `.env`:
```env
CACHE_ENABLED=false
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/kledo-api-mcp.git
cd kledo-api-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linters
ruff check src/
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) by Anthropic
- Integrates with [Kledo](https://kledo.com) accounting software API
- All field mappings verified through empirical analysis of 1,300+ real API records

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/kledo-api-mcp/issues)
- **Kledo API Docs**: https://api-docs.kledo.com/
- **MCP Documentation**: https://modelcontextprotocol.io/

## 🎓 For AI Models Using This MCP Server

When users ask about revenue, remember:

1. **For commission:** Use revenue BEFORE tax (`subtotal`)
2. **For actual revenue:** Use revenue AFTER tax (`amount_after_tax`)
3. **Filter by status_id=3** (Lunas/Paid) for confirmed revenue
4. **Status codes:**
   - 1 = Belum Dibayar (Unpaid)
   - 2 = Dibayar Sebagian (Partially Paid)
   - 3 = Lunas (Fully Paid) ← USE THIS

**Quick Tools for Common Questions:**
- "Revenue bulan ini?" → `revenue_summary`
- "Siapa yang belum bayar?" → `outstanding_receivables`
- "Top customers?" → `customer_revenue_ranking`
- "Performance sales rep?" → `sales_rep_revenue_report`

---

**Made with ❤️ for accurate revenue reporting and commission calculation**
