"""
CLI argument parser and command handlers for Kledo MCP Server.

Provides command-line interface for setup, testing, and configuration management.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

from src.config_manager import ConfigManager
from src.auth import KledoAuthenticator
from src.setup import run_setup_wizard, Colors


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: List of command-line arguments

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="kledo-mcp",
        description="Kledo MCP Server - AI-powered access to Kledo accounting data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kledo-mcp --setup              Run interactive setup wizard
  kledo-mcp --test               Test connection to Kledo API
  kledo-mcp --show-config        Display Claude Desktop configuration JSON
  kledo-mcp --init               Force first-run setup (re-initialize)
  kledo-mcp --version            Show version information
  kledo-mcp                      Start MCP server (auto-setup on first run)

For more information, visit: https://github.com/efacsen/kledo-api-mcp
        """
    )

    # Commands (mutually exclusive)
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive setup wizard"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test connection to Kledo API"
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Display Claude Desktop configuration JSON"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Force first-run setup (re-initialize configuration)"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    return parser.parse_args(argv)


def handle_setup() -> int:
    """
    Run the interactive setup wizard.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    return run_setup_wizard()


def handle_test() -> int:
    """
    Test connection to Kledo API.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    print(f"\n{Colors.CYAN}{Colors.BOLD}Testing Kledo API Connection{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 40}{Colors.RESET}\n")

    # Load configuration from .env
    config_manager = ConfigManager()

    if not config_manager.env_file_exists():
        print(f"{Colors.RED}✗{Colors.RESET} No configuration found (.env file missing)")
        print(f"  Run {Colors.CYAN}kledo-mcp --setup{Colors.RESET} to configure the server.\n")
        return 1

    # Load environment variables
    env_path = config_manager.env_path
    load_dotenv(env_path, override=True)

    api_key = os.getenv("KLEDO_API_KEY")
    base_url = os.getenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")

    if not api_key:
        print(f"{Colors.RED}✗{Colors.RESET} KLEDO_API_KEY not found in .env file")
        print(f"  Run {Colors.CYAN}kledo-mcp --setup{Colors.RESET} to configure the server.\n")
        return 1

    # Create authenticator and test connection
    try:
        auth = KledoAuthenticator(base_url=base_url, api_key=api_key)

        # Run async test
        success = asyncio.run(_test_connection(auth, base_url))

        if success:
            print(f"\n{Colors.GREEN}✓ Connection successful! API key is valid.{Colors.RESET}")
            print(f"  Base URL: {Colors.BLUE}{base_url}{Colors.RESET}\n")
            return 0
        else:
            print(f"\n{Colors.RED}✗ Connection failed. Please check your API key.{Colors.RESET}")
            print(f"  Run {Colors.CYAN}kledo-mcp --setup{Colors.RESET} to reconfigure.\n")
            return 1

    except Exception as e:
        print(f"{Colors.RED}✗ Error testing connection:{Colors.RESET} {str(e)}\n")
        logger.exception("Connection test error")
        return 1


async def _test_connection(auth: KledoAuthenticator, base_url: str) -> bool:
    """
    Test API connection asynchronously.

    Args:
        auth: KledoAuthenticator instance
        base_url: Base URL to test against

    Returns:
        True if connection successful, False otherwise
    """
    import httpx

    try:
        # Login (for API key, this is a no-op)
        login_success = await auth.login()

        if not login_success:
            print(f"{Colors.RED}✗{Colors.RESET} Authentication failed")
            return False

        print(f"{Colors.GREEN}✓{Colors.RESET} Authentication successful")

        # Make a test request to verify API access
        print(f"{Colors.CYAN}Testing API access...{Colors.RESET}")

        async with httpx.AsyncClient() as client:
            headers = auth.get_auth_headers()
            response = await client.get(
                f"{base_url}/contact",
                headers=headers,
                params={"page": 1, "per_page": 1},
                timeout=10.0
            )

            if response.status_code == 401:
                print(f"{Colors.RED}✗{Colors.RESET} Authentication failed - Invalid API key")
                return False
            elif response.status_code == 403:
                print(f"{Colors.RED}✗{Colors.RESET} Access forbidden - Check API key permissions")
                return False
            elif response.status_code >= 400:
                print(f"{Colors.RED}✗{Colors.RESET} API error: HTTP {response.status_code}")
                return False

            response.raise_for_status()
            print(f"{Colors.GREEN}✓{Colors.RESET} API access verified")

        return True

    except httpx.TimeoutException:
        print(f"{Colors.RED}✗{Colors.RESET} Connection timeout - Check network connection")
        return False
    except httpx.HTTPStatusError as e:
        print(f"{Colors.RED}✗{Colors.RESET} HTTP error: {e.response.status_code}")
        logger.debug(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.RESET} Connection failed: {str(e)}")
        logger.debug(f"Test connection error: {str(e)}")
        return False


def handle_show_config() -> int:
    """
    Display Claude Desktop configuration JSON.

    Returns:
        Exit code: 0 for success
    """
    print(f"\n{Colors.CYAN}{Colors.BOLD}Claude Desktop Configuration{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 40}{Colors.RESET}\n")

    # Get current working directory absolute path
    cwd = Path.cwd()

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_current_config()

    if config is None:
        print(f"{Colors.YELLOW}⚠{Colors.RESET} No configuration found (.env file missing)")
        print(f"  Run {Colors.CYAN}kledo-mcp --setup{Colors.RESET} to configure the server first.\n")
        print("Example configuration format:\n")
        config = {
            "api_key": "YOUR_API_KEY_HERE",
            "base_url": "https://api.kledo.com/api/v1",
            "cache_enabled": "true",
            "log_level": "INFO"
        }
    else:
        print(f"{Colors.GREEN}✓{Colors.RESET} Loaded configuration from .env file\n")

    # Generate Claude Desktop config JSON
    claude_config = {
        "mcpServers": {
            "kledo-crm": {
                "command": "kledo-mcp",
                "env": {
                    "KLEDO_API_KEY": config.get("api_key", "YOUR_API_KEY_HERE"),
                    "KLEDO_BASE_URL": config.get("base_url", "https://api.kledo.com/api/v1"),
                    "CACHE_ENABLED": config.get("cache_enabled", "true"),
                    "LOG_LEVEL": config.get("log_level", "INFO")
                }
            }
        }
    }

    # Print JSON configuration
    print(f"{Colors.BOLD}Configuration JSON:{Colors.RESET}")
    print(json.dumps(claude_config, indent=2))
    print()

    # Print OS-specific installation instructions
    print(f"{Colors.BOLD}Installation Instructions:{Colors.RESET}\n")

    # Detect OS
    import platform
    os_name = platform.system()

    if os_name == "Darwin":  # macOS
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        print(f"1. Open Claude Desktop configuration file:")
        print(f"   {Colors.BLUE}{config_path}{Colors.RESET}")
        print()
        print(f"2. Add the JSON above to the {Colors.CYAN}mcpServers{Colors.RESET} section")
        print()
        print(f"3. Restart Claude Desktop")
    elif os_name == "Windows":
        config_path = Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        print(f"1. Open Claude Desktop configuration file:")
        print(f"   {Colors.BLUE}{config_path}{Colors.RESET}")
        print()
        print(f"2. Add the JSON above to the {Colors.CYAN}mcpServers{Colors.RESET} section")
        print()
        print(f"3. Restart Claude Desktop")
    else:  # Linux
        config_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
        print(f"1. Open Claude Desktop configuration file:")
        print(f"   {Colors.BLUE}{config_path}{Colors.RESET}")
        print()
        print(f"2. Add the JSON above to the {Colors.CYAN}mcpServers{Colors.RESET} section")
        print()
        print(f"3. Restart Claude Desktop")

    print()
    print(f"{Colors.YELLOW}Note:{Colors.RESET} Make sure to replace YOUR_API_KEY_HERE with your actual API key")
    print(f"      if you haven't run {Colors.CYAN}kledo-mcp --setup{Colors.RESET} yet.\n")

    return 0


def handle_version() -> int:
    """
    Display version information.

    Returns:
        Exit code: 0 for success
    """
    # Try to read version from pyproject.toml
    version = "0.1.0"  # Default version

    try:
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            import re
            with open(pyproject_path, "r") as f:
                content = f.read()
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    version = match.group(1)
    except Exception as e:
        logger.debug(f"Could not read version from pyproject.toml: {e}")

    print(f"\n{Colors.BOLD}Kledo MCP Server{Colors.RESET} v{version}")
    print(f"AI-powered access to Kledo accounting data\n")
    print(f"Project: {Colors.BLUE}https://github.com/efacsen/kledo-api-mcp{Colors.RESET}")
    print(f"Documentation: {Colors.BLUE}https://efacsen.github.io/kledo-api-mcp/{Colors.RESET}\n")

    return 0


def dispatch_command(args: argparse.Namespace) -> int:
    """
    Route to appropriate command handler based on parsed arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code from command handler
    """
    if args.setup:
        return handle_setup()
    elif args.test:
        return handle_test()
    elif args.show_config:
        return handle_show_config()
    elif args.init:
        # --init is same as --setup but with forced reconfiguration
        return handle_setup()
    elif args.version:
        return handle_version()
    else:
        # No command specified - this shouldn't happen with current argparse setup
        # but handle gracefully
        print("No command specified. Use --help for usage information.")
        return 1


if __name__ == "__main__":
    # Allow running as python -m src.cli for testing
    sys.exit(dispatch_command(parse_args(sys.argv[1:])))
