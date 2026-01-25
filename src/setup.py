"""
Interactive setup wizard for Kledo MCP Server.

Provides first-run detection and guided configuration setup.
"""
import asyncio
import sys
from typing import Optional
from pathlib import Path
from loguru import logger

from src.config_manager import ConfigManager
from src.auth import KledoAuthenticator


# ANSI color codes for terminal output
class Colors:
    """Terminal color codes."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class SetupWizard:
    """Interactive setup wizard for first-time configuration."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize SetupWizard.

        Args:
            config_manager: ConfigManager instance. Creates new one if None.
        """
        self.config_manager = config_manager or ConfigManager()

    def detect_first_run(self) -> bool:
        """
        Detect if this is the first run (no valid .env configuration).

        Returns:
            True if first run (needs setup), False if already configured
        """
        return not self.config_manager.env_file_exists()

    def prompt_api_key(self) -> str:
        """
        Prompt user for API key with helpful guidance.

        Returns:
            API key string from user input
        """
        print(f"\n{Colors.CYAN}{Colors.BOLD}Step 1: API Key{Colors.RESET}")
        print(f"{Colors.CYAN}─────────────────{Colors.RESET}\n")

        print("To get your API key:")
        print(f"  1. Visit {Colors.BLUE}https://app.kledo.com{Colors.RESET}")
        print("  2. Go to: Settings → Integration → API")
        print("  3. Create a new API key")
        print()

        while True:
            api_key = input(f"{Colors.BOLD}Enter your Kledo API key:{Colors.RESET} ").strip()

            if not api_key:
                print(f"{Colors.RED}✗{Colors.RESET} API key cannot be empty. Please try again.\n")
                continue

            # Validate format
            is_valid, error_msg = self.config_manager.validate_api_key(api_key)
            if not is_valid:
                print(f"{Colors.RED}✗{Colors.RESET} {error_msg}")
                print("  Please enter a valid API key.\n")
                continue

            print(f"{Colors.GREEN}✓{Colors.RESET} API key format looks good!\n")
            return api_key

    def prompt_base_url(self) -> str:
        """
        Prompt user for base URL with default option.

        Returns:
            Base URL string
        """
        print(f"\n{Colors.CYAN}{Colors.BOLD}Step 2: API Base URL{Colors.RESET}")
        print(f"{Colors.CYAN}─────────────────────{Colors.RESET}\n")

        default_url = "https://api.kledo.com/api/v1"
        print(f"Default URL: {Colors.BLUE}{default_url}{Colors.RESET}")
        print("Press Enter to use default, or enter a different URL.")
        print()

        while True:
            user_input = input(f"{Colors.BOLD}Base URL [{default_url}]:{Colors.RESET} ").strip()

            # Use default if empty
            base_url = user_input if user_input else default_url

            # Validate URL
            is_valid, error_msg = self.config_manager.validate_base_url(base_url)
            if not is_valid:
                print(f"{Colors.RED}✗{Colors.RESET} {error_msg}")
                print("  Please enter a valid HTTPS URL.\n")
                continue

            print(f"{Colors.GREEN}✓{Colors.RESET} Base URL accepted!\n")
            return base_url

    async def test_connection(self, api_key: str, base_url: str) -> tuple[bool, str]:
        """
        Test connection to Kledo API with provided credentials.

        Args:
            api_key: API key to test
            base_url: Base URL to test against

        Returns:
            Tuple of (success, message)
        """
        print(f"\n{Colors.CYAN}{Colors.BOLD}Testing connection...{Colors.RESET}\n")

        try:
            # Create authenticator with API key
            auth = KledoAuthenticator(base_url=base_url, api_key=api_key)

            # Try to login (for API key, this just validates it's set)
            login_success = await auth.login()

            if not login_success:
                return False, "Authentication failed - API key may be invalid"

            # Try a simple authenticated request to verify it works
            # We'll make a minimal request to check authentication
            import httpx
            async with httpx.AsyncClient() as client:
                headers = auth.get_auth_headers()
                response = await client.get(
                    f"{base_url}/contact",
                    headers=headers,
                    params={"page": 1, "per_page": 1},
                    timeout=10.0
                )

                if response.status_code == 401:
                    return False, "Authentication failed - Invalid API key"
                elif response.status_code == 403:
                    return False, "Access forbidden - Check API key permissions"
                elif response.status_code >= 400:
                    return False, f"API error: HTTP {response.status_code}"

                response.raise_for_status()

            return True, "Connection successful!"

        except Exception as e:
            logger.debug(f"Connection test error: {str(e)}")
            return False, f"Connection failed: {str(e)}"

    def save_configuration(self, config: dict) -> bool:
        """
        Save configuration to .env file.

        Args:
            config: Configuration dictionary

        Returns:
            True if saved successfully, False otherwise
        """
        print(f"\n{Colors.CYAN}{Colors.BOLD}Saving configuration...{Colors.RESET}\n")

        success = self.config_manager.create_env_file(config)

        if success:
            print(f"{Colors.GREEN}✓{Colors.RESET} Configuration saved to .env file")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.RESET} Failed to save configuration")
            return False

    async def run(self) -> bool:
        """
        Run the complete setup wizard flow.

        Returns:
            True if setup completed successfully, False otherwise
        """
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}{Colors.CYAN}Kledo MCP Server - First Time Setup{Colors.RESET}")
        print("=" * 60)
        print()
        print("Welcome! Let's get your Kledo MCP server configured.")
        print("This will only take a minute.\n")

        # Step 1: Get API key
        api_key = self.prompt_api_key()

        # Step 2: Get base URL
        base_url = self.prompt_base_url()

        # Step 3: Test connection
        test_success, test_message = await self.test_connection(api_key, base_url)

        if not test_success:
            print(f"{Colors.RED}✗{Colors.RESET} {test_message}")
            print()
            print("Please check your credentials and try again.")
            return False

        print(f"{Colors.GREEN}✓{Colors.RESET} {test_message}")

        # Step 4: Save configuration
        config = {
            "api_key": api_key,
            "base_url": base_url,
        }

        if not self.save_configuration(config):
            return False

        # Success!
        print()
        print("=" * 60)
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Setup Complete!{Colors.RESET}")
        print("=" * 60)
        print()
        print("Your Kledo MCP server is now configured and ready to use.")
        print()
        print("Next steps:")
        print(f"  • Test the connection: {Colors.CYAN}kledo-mcp --test{Colors.RESET}")
        print(f"  • View configuration: {Colors.CYAN}kledo-mcp --show-config{Colors.RESET}")
        print(f"  • Start the server: {Colors.CYAN}kledo-mcp{Colors.RESET}")
        print()

        return True


def run_setup_wizard() -> int:
    """
    Run the setup wizard.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    wizard = SetupWizard()

    # Check if already configured
    if not wizard.detect_first_run():
        print(f"{Colors.YELLOW}⚠{Colors.RESET} Configuration already exists (.env file found)")
        print()
        response = input("Do you want to reconfigure? (yes/no) [no]: ").strip().lower()

        if response not in ["yes", "y"]:
            print("Setup cancelled. Existing configuration preserved.")
            return 0

        print("\nReconfiguring...\n")

    # Run the wizard
    try:
        success = asyncio.run(wizard.run())
        return 0 if success else 1
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠{Colors.RESET} Setup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}✗{Colors.RESET} Setup failed: {str(e)}")
        logger.exception("Setup wizard error")
        return 1


if __name__ == "__main__":
    sys.exit(run_setup_wizard())
