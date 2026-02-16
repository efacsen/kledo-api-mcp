# Kledo MCP Server

Model Context Protocol (MCP) server for Kledo accounting software API - enables AI assistants to interact with your Kledo data for financial reporting, analytics, customer management, and business intelligence.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What is this?

An MCP server that connects AI assistants (like Claude) to the Kledo accounting API, enabling natural language queries for financial data, customer analytics, and business reporting.

## 🎯 Key Features

- **28 Production-Ready Tools** - Complete coverage of Kledo API endpoints
- **Revenue & Financial Analytics** - Invoice tracking, revenue reporting, receivables management
- **Customer Intelligence** - Customer ranking, transaction history, contact management
- **Product & Inventory** - Product lookup, SKU search, inventory insights
- **Order & Delivery Tracking** - Sales orders, purchase orders, delivery status
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

## 🛠️ Available Tools (28 Total)

### Revenue & Analytics (8 tools)
- `revenue_summary` - Revenue for any time period (with tax breakdown)
- `outstanding_receivables` - Track unpaid invoices
- `customer_revenue_ranking` - Identify top customers by revenue
- `sales_rep_revenue_report` - Sales representative performance analysis
- `sales_rep_list` - List all sales representatives
- `invoice_list_sales` - List sales invoices with filters
- `invoice_get_detail` - Detailed invoice information
- `invoice_get_totals` - Invoice totals and summary

### Purchase/Expenses (1 tool)
- `invoice_list_purchase` - List purchase invoices

### Products (3 tools)
- `product_list` - List all products
- `product_get_detail` - Detailed product information
- `product_search_by_sku` - Search products by SKU

### Customers/Contacts (3 tools)
- `contact_list` - List customers and vendors
- `contact_get_detail` - Contact details and information
- `contact_get_transactions` - Contact transaction history

### Orders (4 tools)
- `order_list_sales` - List sales orders
- `order_get_detail` - Sales order details
- `order_list_purchase` - List purchase orders
- `order_get_purchase_detail` - Purchase order details

### Deliveries (4 tools)
- `delivery_list` - List all deliveries
- `delivery_get_detail` - Delivery details
- `delivery_list_pending` - Pending deliveries
- `delivery_get_by_order` - Deliveries for specific order

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
- Claude Desktop, or any AI IDE that supports MCP

### Standard Install

```bash
git clone https://github.com/efacsen/kledo-api-mcp.git
cd kledo-api-mcp
pip install -e .
```

**The `kledo-mcp` command is now available!**

### Getting Your Kledo API Key

1. Log in to your Kledo account at [https://kledo.com](https://kledo.com)
2. Navigate to **Settings** → **Integration** → **API**
3. Click **Generate New API Key**
4. Copy the key (it starts with `kledo_pat_`)

The setup wizard will prompt you for this key when you run `kledo-mcp` for the first time.

### Claude Desktop Configuration

The easiest way is to run the setup wizard:

```bash
kledo-mcp --show-config
```

This displays your Claude Desktop configuration with the correct paths. Just copy and paste!

**Manual Configuration (Advanced):**

If you prefer to configure manually, edit your Claude Desktop config file:

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

**Config file locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Security Note**: Never commit your API key to version control.

## 🚀 Deployment & Production Setup

The MCP server supports multiple deployment scenarios with flexible configuration:

### Environment Variables (Recommended for Production)

For Docker, Kubernetes, and Infrastructure-as-Code deployments:

```bash
export KLEDO_API_KEY="your_api_key_here"
export KLEDO_BASE_URL="https://api.kledo.com/api/v1"
kledo-mcp  # Starts immediately, skips setup wizard
```

**Perfect for:**
- Docker containers
- Kubernetes deployments
- Terraform/CloudFormation
- CI/CD pipelines
- Non-interactive deployments

### Configuration File Locations

The server checks for configuration in this priority order:

1. **Environment variables** (highest priority)
   - `KLEDO_API_KEY`
   - `KLEDO_BASE_URL`

2. **User config directory** (persistent)
   - `~/.kledo/.env` - Persists across projects/clones

3. **XDG config directory** (Unix/Linux standard)
   - `~/.config/kledo/.env`

4. **System config directory**
   - `/etc/kledo/.env`

5. **Project directory** (fallback)
   - `./.env` - Project root

### Deployment Scenarios

**Scenario A: Interactive Server (SSH)**
```bash
ssh ubuntu@your-server
cd ~/kledo-api-mcp
kledo-mcp
# Wizard prompts for API key
# Saves to ~/.kledo/.env automatically
```

**Scenario B: Docker Container**
```dockerfile
FROM python:3.11-slim
RUN pip install kledo-api-mcp
ENV KLEDO_API_KEY=your_key_here
ENV KLEDO_BASE_URL=https://api.kledo.com/api/v1
CMD ["kledo-mcp"]
```

**Scenario C: Kubernetes Pod**
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kledo-mcp
    image: kledo-mcp:latest
    env:
    - name: KLEDO_API_KEY
      valueFrom:
        secretKeyRef:
          name: kledo-secrets
          key: api_key
    - name: KLEDO_BASE_URL
      value: https://api.kledo.com/api/v1
```

**Scenario D: Pre-configured VM Image**
```bash
# During image creation
mkdir -p ~/.kledo
cat > ~/.kledo/.env << EOF
KLEDO_API_KEY=your_key
KLEDO_BASE_URL=https://api.kledo.com/api/v1
EOF

# Later, on cloned instances
kledo-mcp  # Automatically finds ~/.kledo/.env
```

### Configuration Priority

The server uses this decision tree:

```
Does environment variables have KLEDO_API_KEY?
  ├─ YES → Use environment variables
  └─ NO → Check ~/.kledo/.env
           ├─ YES → Use ~/.kledo/.env
           └─ NO → Check ~/.config/kledo/.env
                    ├─ YES → Use ~/.config/kledo/.env
                    └─ NO → Check /etc/kledo/.env
                             ├─ YES → Use /etc/kledo/.env
                             └─ NO → Run interactive setup wizard
```

This means:
- Environment variables always override .env files
- Once configured, the wizard is skipped
- Config persists across reinstalls (in ~/.kledo/)
- Non-interactive deployments are fully supported

## 🚀 Usage Examples

### Get Monthly Revenue

Ask your AI assistant:
```
"What's this month's revenue?"
"Berapa revenue bulan ini?"
```

The assistant will use the `revenue_summary` tool and return revenue data with tax breakdown.

### Sales Representative Performance

Ask:
```
"Show sales rep performance for January"
"Siapa sales rep dengan revenue tertinggi bulan ini?"
```

Get detailed performance metrics including revenue, invoice counts, and top deals per representative.

### Outstanding Invoices

Ask:
```
"Show outstanding invoices"
"Siapa yang belum bayar?"
```

View all unpaid and partially paid invoices with customer details and amounts.

### Top Customers

Ask:
```
"Who are our top 10 customers this month?"
"Customer dengan revenue tertinggi?"
```

Get customer rankings by revenue, invoice count, and average invoice value.

### Product Search

Ask:
```
"Find product with SKU ABC123"
"Show all products in category Paint"
```

Search and filter products by SKU, name, or category.

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

## 🐛 Troubleshooting

### Setup & First-Run Issues

**Setup wizard won't start:**

```bash
# Verify installation
pip install -e .

# Try explicit setup
kledo-mcp --setup
```

**"Invalid API key" error:**

1. Verify your API key starts with `kledo_pat_`
2. Check for extra spaces when copying
3. Test the key directly:
   ```bash
   kledo-mcp --test
   ```
4. Generate a new key from Kledo dashboard if needed

**Configuration not saved:**

```bash
# Check .env was created
ls -la .env

# Force re-initialization
kledo-mcp --init
```

**"Connection failed" during setup:**

1. Verify your internet connection
2. Check Kledo API status: [https://status.kledo.com](https://status.kledo.com)
3. Test with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.kledo.com/api/v1/finance/account
   ```

**Claude Desktop doesn't show the server:**

1. Run `kledo-mcp --show-config` and copy the output
2. Verify JSON syntax (use [jsonlint.com](https://jsonlint.com))
3. Check config file location:
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Linux
   cat ~/.config/Claude/claude_desktop_config.json
   ```
4. Restart Claude Desktop completely (quit and reopen)
5. Check Claude logs:
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

**Still stuck?**

Open an issue with:
- Output of `kledo-mcp --version`
- Output of `kledo-mcp --test`
- Any error messages from the setup wizard

---

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

Ask your AI assistant:
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

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/efacsen/kledo-api-mcp/issues)
- **Kledo API Docs**: https://api-docs.kledo.com/
- **MCP Documentation**: https://modelcontextprotocol.io/

---

**Made with ❤️ for intelligent business analytics**
