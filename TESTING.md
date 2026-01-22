# Testing Your Kledo MCP Server

This guide explains how to test and run your Kledo MCP server.

## Understanding MCP Servers

**MCP servers are NOT traditional web servers:**
- They run as **stdio-based processes** (JSON-RPC over stdin/stdout)
- Launched on-demand by MCP clients (like Claude Desktop)
- Communication happens through standard input/output streams
- Think of them as "command-line tools for AI agents"

## Testing Methods

### Method 1: MCP Inspector (Recommended) 🔍

The official testing tool with a web UI.

**Start the inspector:**
```bash
./test_with_inspector.sh
```

Or manually:
```bash
source .venv/bin/activate
npx @modelcontextprotocol/inspector python -m src.server
```

**What happens:**
1. Opens browser at `http://localhost:5173`
2. Shows all available tools
3. Lets you test each tool with arguments
4. Displays real responses from your Kledo API

**Example tests to try:**
- Click on `utility_test_connection` → Execute (no arguments needed)
- Click on `financial_bank_balances` → Execute
- Click on `contact_list` → Add parameters → Execute
- Click on `product_list` → Execute

### Method 2: Claude Desktop (Production Use) 💬

Use your MCP server with Claude Desktop app.

**1. Create config file:**

Location: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "kledo-crm": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/kevinzakaria/developers/kledo-api-mcp",
      "env": {
        "KLEDO_API_KEY": "kledo_pat_YOUR_KEY_HERE"
      }
    }
  }
}
```

**2. Get your API key from .env:**
```bash
grep KLEDO_API_KEY .env
```

**3. Restart Claude Desktop**

**4. Test with queries:**
- "What's my total bank balance?"
- "Show me unpaid invoices"
- "List all customers"
- "What products are in stock?"

### Method 3: Python Test Client

For programmatic testing, create a test client:

**Create `test_mcp_client.py`:**
```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test MCP server programmatically."""

    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server"],
        env=None  # Uses .env file
    )

    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {len(tools.tools)}")

            # Call a tool
            result = await session.call_tool(
                "utility_test_connection",
                arguments={}
            )

            print("\nConnection test result:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

### Method 4: Direct Server Run (Debug Mode) 🐛

For debugging server startup:

```bash
source .venv/bin/activate
python -m src.server
```

**What you'll see:**
- Server starts and waits for JSON-RPC messages on stdin
- No HTTP server, no port binding
- Use Ctrl+C to stop

**To test manually (advanced):**
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python -m src.server
```

## Common Testing Scenarios

### Test 1: Connection
```bash
./test_with_inspector.sh
# → Click "utility_test_connection"
# → Click "Execute"
```

Expected: Authentication status and API connection test results

### Test 2: Bank Balances
```bash
# In Inspector or Claude:
# Tool: financial_bank_balances
# No parameters needed
```

Expected: List of all bank accounts with current balances

### Test 3: List Invoices
```bash
# In Inspector:
# Tool: invoice_list_sales
# Parameters: {"per_page": 5, "page": 1}
```

Expected: First 5 sales invoices

### Test 4: Search Product
```bash
# Tool: product_search_by_sku
# Parameters: {"sku": "YOUR-SKU-CODE"}
```

Expected: Product details with price and stock

### Test 5: Contact Transactions
```bash
# Tool: contact_get_transactions
# Parameters: {"contact_id": 123}
```

Expected: Transaction history for that contact

## Troubleshooting

### "Server won't start"
```bash
# Check Python version (needs 3.10+)
python --version

# Check dependencies
pip list | grep mcp

# Check .env file
cat .env | grep KLEDO
```

### "Authentication failed"
```bash
# Test API key directly
python test_connection.py

# Verify API key format
# Should start with: kledo_pat_
grep KLEDO_API_KEY .env
```

### "Tool returns error"
```bash
# Check logs (if LOG_FILE is set)
tail -f logs/kledo-mcp.log

# Test specific endpoint
python test_data_retrieval.py
```

### "Inspector won't open"
```bash
# Check if port 5173 is available
lsof -i :5173

# Try different port (if needed)
npx @modelcontextprotocol/inspector --port 5174 python -m src.server
```

## Monitoring Server in Production

When running with Claude Desktop:

**Check if server is running:**
```bash
# macOS
ps aux | grep "src.server"

# Check Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

**View Claude Desktop MCP logs:**
- Open Claude Desktop
- Go to Settings → Developer
- View MCP Server Logs

## Performance Tips

1. **Cache is enabled by default** - Check `.env`:
   ```bash
   CACHE_ENABLED=true
   ```

2. **Clear cache when needed:**
   - Use `utility_clear_cache` tool
   - Or restart the server

3. **Monitor cache stats:**
   - Use `utility_get_cache_stats` tool
   - Shows hit rate and performance

4. **Adjust cache TTLs:**
   - Edit `config/cache_config.yaml`
   - Restart server to apply changes

## Next Steps

1. ✅ Test with Inspector to verify all tools work
2. ✅ Configure Claude Desktop for daily use
3. ✅ Try the smart routing with natural language queries
4. ✅ Monitor performance with cache stats

## Need Help?

- Check server logs: `logs/kledo-mcp.log`
- Test API directly: `python test_connection.py`
- View data samples: `python test_data_retrieval.py`
- Read architecture: `docs/ARCHITECTURE.md`
