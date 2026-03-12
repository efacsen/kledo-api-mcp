# Kledo MCP Server

Model Context Protocol (MCP) server for Kledo accounting software API - enables AI assistants to interact with your Kledo data for financial reporting, analytics, customer management, and business intelligence.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What is this?

An MCP server that connects AI assistants (like Claude) to the Kledo accounting API, enabling natural language queries for financial data, customer analytics, and business reporting.

## 🎯 Key Features

- **24 Production-Ready Tools** - Complete coverage of Kledo API endpoints
- **Revenue & Financial Analytics** - Invoice tracking, revenue reporting, receivables management
- **Customer Intelligence** - Customer ranking, transaction history, contact management
- **Product & Inventory** - Product lookup, SKU search, inventory insights
- **Order & Delivery Tracking** - Sales orders, purchase orders, delivery status
- **Bilingual Support** - Understands Indonesian and English queries
- **Smart Caching** - Configurable caching for optimal performance
- **Type-Safe** - Comprehensive type hints throughout

## 🚀 Quick Start in 2 Minutes

**First time setup:**

1. **Clone and install:**

   With `uv` (recommended):
   ```bash
   git clone https://github.com/efacsen/kledo-api-mcp.git
   cd kledo-api-mcp
   uv pip install -e .
   ```

   With `pip`:
   ```bash
   git clone https://github.com/efacsen/kledo-api-mcp.git
   cd kledo-api-mcp
   pip install -e .
   ```

   > Don't have `uv`? Install it: `curl -LsSf https://astral.sh/uv/install.sh | sh`

2. **Run the setup wizard:**
   ```bash
   kledo-mcp --setup
   ```
   The interactive wizard will:
   - ✓ Prompt for your Kledo API key
   - ✓ Validate your connection live against the Kledo API
   - ✓ Save config to `~/.kledo/.env` (persistent across projects)

3. **Get your Claude Desktop config:**
   ```bash
   kledo-mcp --show-config
   ```
   This outputs the exact JSON to paste into your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

4. **Restart Claude Desktop** - Done! 🎉

**To get your Kledo API key:**
1. Login to [app.kledo.com](https://app.kledo.com)
2. Go to **Settings → Integration → API**
3. Create a new Personal Access Token

**Need help?** See [Troubleshooting](#-troubleshooting) below.

## 🛠️ Available Tools (24 Total)

### Revenue (3 tools)
- `revenue_summary` - Revenue for any period (paid invoices, with tax breakdown)
- `revenue_receivables` - Outstanding invoices: list / aging buckets / Pareto concentration
- `revenue_ranking` - Revenue ranked by customer or by day

### Invoices (3 tools)
- `invoice_list` - List sales or purchase invoices (`type: sales|purchase`)
- `invoice_get` - Detailed invoice information by ID
- `invoice_summarize` - Invoice totals or outstanding breakdown by customer/vendor

### Orders (2 tools)
- `order_list` - List sales or purchase orders (`type: sales|purchase`)
- `order_get` - Order details by ID

### Products (2 tools)
- `product_list` - List products with optional search and inventory
- `product_get` - Product detail by ID or by SKU/code

### Customers/Contacts (2 tools)
- `contact_list` - List customers and vendors
- `contact_get` - Contact profile or transaction history (`view: detail|transactions`)

### Deliveries (2 tools)
- `delivery_list` - List deliveries with date/status filters
- `delivery_get` - Delivery detail or pending shipments (`view: detail|pending`)

### Financial (3 tools)
- `financial_summary` - Sales or purchase summary by customer, sales rep, or vendor
- `financial_balances` - Current bank account balances
- `financial_activity` - Team activity report for a date range

### Analytics & Commission (3 tools)
- `analytics_compare` - Compare revenue or outstanding across periods or sales reps
- `analytics_targets` - Sales targets: report / underperformers / set target
- `commission_report` - Commission calculation (tiered or flat rate) per rep or all reps

### Sales (2 tools)
- `sales_rep_report` - Sales rep revenue breakdown for a period
- `sales_rep_list` - List all sales representatives

### Utilities (2 tools)
- `utility_cache` - Cache stats or clear (`action: stats|clear`)
- `utility_test_connection` - Test Kledo API connection and auth status

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- Kledo account with API access
- Claude Desktop, or any AI IDE that supports MCP

### Standard Install

With `uv` (recommended):
```bash
git clone https://github.com/efacsen/kledo-api-mcp.git
cd kledo-api-mcp
uv pip install -e .
```

With `pip`:
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

# Install with dev dependencies (uv recommended)
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"

# Run tests
uv run pytest tests/

# Run linters
uv run ruff check src/
uv run mypy src/
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
