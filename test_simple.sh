#!/bin/bash
# Simple MCP Inspector without OAuth authentication
# This makes testing much easier

echo "=========================================="
echo "  Starting Kledo MCP Server (Simple Mode)"
echo "=========================================="
echo ""
echo "Opening web UI without OAuth..."
echo ""

# Activate virtual environment
source .venv/bin/activate

# Set environment variable to disable OAuth requirement
export DANGEROUSLY_OMIT_AUTH=true

# Run the MCP inspector
npx @modelcontextprotocol/inspector python -m src.server
