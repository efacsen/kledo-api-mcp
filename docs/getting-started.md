# Getting Started

Quick start guide for using the Kledo MCP Server with AI agents.

## Prerequisites

- Python 3.11+
- Kledo API credentials
- Claude Desktop (or other MCP-compatible client)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/kledo-api-mcp.git
   cd kledo-api-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Kledo API credentials
   ```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `KLEDO_API_URL` | Your Kledo API base URL | Yes |
| `KLEDO_API_TOKEN` | API authentication token | Yes |
| `KLEDO_COMPANY_ID` | Your company ID in Kledo | Yes |

## Claude Desktop Configuration

Add to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "kledo": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/kledo-api-mcp",
      "env": {
        "KLEDO_API_URL": "https://api.kledo.com",
        "KLEDO_API_TOKEN": "your-token-here",
        "KLEDO_COMPANY_ID": "your-company-id"
      }
    }
  }
}
```

## Quick Examples

### List recent invoices
Ask Claude: "Show me the last 10 sales invoices"

### Find a customer
Ask Claude: "Find customer named 'Acme Corp'"

### Check inventory
Ask Claude: "What's the stock level for product SKU ABC123?"

### Financial summary
Ask Claude: "What's our total outstanding receivables?"

### Sales report
Ask Claude: "Show me sales by customer for this month"

### Pending shipments
Ask Claude: "What orders are waiting to be shipped?"

## Tool Discovery

For AI agents: The `llms.txt` file in the project root provides AI-optimized tool discovery with natural language hints for each tool.

For developers: Browse the [Tool Catalog](tools/index.md) for complete API documentation.

## Entity Reference

See [Entity Registry](entities/index.md) for data model documentation and ERD diagrams.

## Troubleshooting

### Connection Issues

1. Test the API connection:
   Ask Claude: "Test the Kledo API connection"

2. Check your credentials in `.env`

3. Verify your Kledo API token is active

### Stale Data

If data seems outdated:
Ask Claude: "Clear the cache and refresh"

### Missing Data

Ensure your Kledo user has appropriate permissions for the data you're querying.
