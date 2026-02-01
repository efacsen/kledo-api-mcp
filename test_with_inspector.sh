#!/bin/bash
# Test Kledo MCP Server with MCP Inspector
# The inspector provides a web UI to test your MCP server

echo "=========================================="
echo "  Starting MCP Inspector for Kledo Server"
echo "=========================================="
echo ""
echo "This will:"
echo "  1. Launch your MCP server"
echo "  2. Open a web UI at http://localhost:5173"
echo "  3. Let you test all tools interactively"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Activate virtual environment and run inspector
source .venv/bin/activate

# Run the MCP inspector
npx @modelcontextprotocol/inspector python -m src.server
