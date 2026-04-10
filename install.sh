#!/usr/bin/env bash
# Kledo MCP Server — One-command installer
# Usage:
#   ./install.sh                    # install + setup + patch Claude Desktop config
#   ./install.sh --no-claude        # install + setup only (skip Claude Desktop patch)
#
# To run directly from GitHub:
#   curl -sSL https://raw.githubusercontent.com/efacsen/kledo-api-mcp/main/install.sh | bash

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
RESET="\033[0m"

ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET} $*"; }
die()  { echo -e "${RED}✗ Error:${RESET} $*" >&2; exit 1; }

# ── Args ──────────────────────────────────────────────────────────────────────
PATCH_CLAUDE=true
for arg in "$@"; do
  [[ "$arg" == "--no-claude" ]] && PATCH_CLAUDE=false
done

echo ""
echo -e "${BOLD}Kledo MCP Server — Installer${RESET}"
echo -e "${CYAN}────────────────────────────────────────${RESET}"
echo ""

# ── 1. Determine install directory ────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# If script was piped via curl, SCRIPT_DIR will be /tmp or similar — clone fresh
if [[ ! -f "$SCRIPT_DIR/pyproject.toml" ]]; then
  INSTALL_DIR="$HOME/kledo-api-mcp"
  info "Cloning repository to $INSTALL_DIR..."
  if [[ -d "$INSTALL_DIR" ]]; then
    warn "Directory already exists — pulling latest..."
    git -C "$INSTALL_DIR" pull --ff-only
  else
    git clone https://github.com/efacsen/kledo-api-mcp.git "$INSTALL_DIR"
  fi
  cd "$INSTALL_DIR"
else
  INSTALL_DIR="$SCRIPT_DIR"
  cd "$INSTALL_DIR"
  info "Installing from $INSTALL_DIR"
fi

ok "Project directory: $INSTALL_DIR"

# ── 2. Check Python 3.11+ ─────────────────────────────────────────────────────
PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3; do
  if command -v "$cmd" &>/dev/null; then
    VERSION=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    MAJOR="${VERSION%%.*}"
    MINOR="${VERSION##*.}"
    if [[ "$MAJOR" -ge 3 && "$MINOR" -ge 11 ]]; then
      PYTHON="$cmd"
      break
    fi
  fi
done

[[ -z "$PYTHON" ]] && die "Python 3.11+ not found. Install from https://python.org/downloads"
ok "Python: $("$PYTHON" --version)"

# ── 3. Install package ────────────────────────────────────────────────────────
echo ""
info "Installing Kledo MCP Server..."

USE_UV=false
if command -v uv &>/dev/null; then
  ok "Using uv (fast)"
  uv pip install -e . --quiet
  USE_UV=true
elif command -v pip3 &>/dev/null; then
  ok "Using pip3"
  pip3 install -e . --quiet
else
  ok "Using pip"
  "$PYTHON" -m pip install -e . --quiet
fi

ok "Package installed"

# ── 4. Verify kledo-mcp CLI is available ──────────────────────────────────────
# When installed via uv, the binary lives in the uv-managed venv — use `uv run`.
# Also set PYTHONPATH to include the project root so that kledo_mcp.py (at root)
# is importable — the editable .pth only adds src/, not the project root.
if [[ "$USE_UV" == "true" ]]; then
  export PYTHONPATH="$INSTALL_DIR${PYTHONPATH:+:$PYTHONPATH}"
  KLEDO_MCP_CMD=(uv run kledo-mcp)
  ok "CLI: uv run kledo-mcp (PYTHONPATH includes project root)"
elif command -v kledo-mcp &>/dev/null; then
  KLEDO_MCP_CMD=(kledo-mcp)
  ok "CLI: $(command -v kledo-mcp)"
else
  # Last resort: find via pip scripts dir
  KMC="$("$PYTHON" -c "import sysconfig; print(sysconfig.get_path('scripts'))")/kledo-mcp"
  [[ -f "$KMC" ]] || die "kledo-mcp CLI not found after install. Run: pip install -e . manually."
  KLEDO_MCP_CMD=("$KMC")
  ok "CLI: $KMC"
fi

# ── 5. Setup wizard ───────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Step 1: Configure your Kledo API connection${RESET}"
echo -e "${CYAN}────────────────────────────────────────${RESET}"
info "Get your API key: Kledo → Settings → Integration → API → Personal Access Token"
echo ""

"${KLEDO_MCP_CMD[@]}" --setup

# ── 6. Patch Claude Desktop config ───────────────────────────────────────────
if [[ "$PATCH_CLAUDE" == "true" ]]; then
  echo ""
  echo -e "${BOLD}Step 2: Configure Claude Desktop${RESET}"
  echo -e "${CYAN}────────────────────────────────────────${RESET}"

  # Determine Claude Desktop config path (macOS / Linux / Windows via WSL)
  case "$(uname -s)" in
    Darwin)  CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
    Linux)   CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json" ;;
    MINGW*|MSYS*|CYGWIN*)
             CLAUDE_CONFIG="$APPDATA/Claude/claude_desktop_config.json" ;;
    *)       CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json" ;;
  esac

  # Use Python to generate MCP entry and merge into existing config
  "$PYTHON" - <<PYEOF
import json, os, sys, shutil
from pathlib import Path

install_dir = "$INSTALL_DIR"
config_path = Path("$CLAUDE_CONFIG")
config_path.parent.mkdir(parents=True, exist_ok=True)

# Build the MCP server entry (mirrors what kledo-mcp --show-config does)
uv = shutil.which("uv")
if uv:
    server_entry = {
        "command": uv,
        "args": ["--directory", install_dir, "run", "python", "-m", "src.server"],
    }
    method = f"uv at {uv}"
else:
    server_entry = {
        "command": sys.executable,
        "args": ["-m", "src.server"],
        "cwd": install_dir,
    }
    method = f"Python at {sys.executable}"

# Load ~/.kledo/.env to get env vars for the MCP entry
env_file = Path.home() / ".kledo" / ".env"
env_block = {}
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env_block[k.strip()] = v.strip()

if env_block:
    server_entry["env"] = {
        "KLEDO_API_KEY": env_block.get("KLEDO_API_KEY", ""),
        "KLEDO_BASE_URL": env_block.get("KLEDO_BASE_URL", "https://api.kledo.com/api/v1"),
        "CACHE_ENABLED": env_block.get("CACHE_ENABLED", "true"),
        "LOG_LEVEL": env_block.get("LOG_LEVEL", "INFO"),
    }

# Load existing Claude Desktop config (if any) and merge
existing = {}
if config_path.exists():
    try:
        existing = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        pass  # start fresh if malformed

existing.setdefault("mcpServers", {})
existing["mcpServers"]["kledo-crm"] = server_entry

config_path.write_text(json.dumps(existing, indent=2))
print(f"  Patched: {config_path}")
print(f"  Method:  {method}")
PYEOF

  echo ""
  ok "Claude Desktop config updated: $CLAUDE_CONFIG"
  warn "Restart Claude Desktop to activate the MCP server"
fi

# ── 7. Done ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}Installation complete!${RESET}"
echo ""
echo -e "  Test connection:  ${CYAN}kledo-mcp --test${RESET}"
echo -e "  View config:      ${CYAN}kledo-mcp --show-config${RESET}"
echo -e "  Re-run setup:     ${CYAN}kledo-mcp --setup${RESET}"
echo ""
