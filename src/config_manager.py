"""
Configuration manager for Kledo MCP Server.

Handles .env file creation, validation, and configuration management.
"""
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from dotenv import load_dotenv, set_key, find_dotenv
from loguru import logger


class ConfigManager:
    """Manages configuration validation and .env file operations."""

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize ConfigManager.

        Args:
            env_path: Path to .env file. Defaults to project root/.env
        """
        self._is_default_path = env_path is None

        if env_path is None:
            # Find .env in project root (parent of src/)
            self.env_path = Path(__file__).parent.parent / ".env"
        else:
            self.env_path = Path(env_path)

        self.env_example_path = self.env_path.parent / ".env.example"

    def get_config_file_locations(self) -> list[Path]:
        """
        Get list of config file locations to check in priority order.

        Returns:
            List of Path objects to check for .env files
        """
        locations = [
            # 1. Current directory (project root)
            Path(__file__).parent.parent / ".env",
            # 2. User's kledo config directory (for persistent config)
            Path.home() / ".kledo" / ".env",
            # 3. XDG config directory (Unix/Linux standard)
            Path.home() / ".config" / "kledo" / ".env",
            # 4. System-wide config (if running as service)
            Path("/etc/kledo/.env"),
        ]
        return locations

    def has_env_vars_configured(self) -> bool:
        """
        Check if KLEDO_API_KEY and KLEDO_BASE_URL are set via environment.

        Returns:
            True if both env vars are set, False otherwise
        """
        api_key = os.getenv("KLEDO_API_KEY", "").strip()
        base_url = os.getenv("KLEDO_BASE_URL", "").strip()
        return bool(api_key and base_url)

    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        """
        Validate API key format.

        Args:
            api_key: API key to validate

        Returns:
            Tuple of (is_valid, error_message). error_message is empty if valid.
        """
        if not api_key or not isinstance(api_key, str):
            return False, "API key cannot be empty"

        api_key = api_key.strip()

        # Check minimum length (at least 20 characters for security)
        if len(api_key) < 20:
            return False, "API key must be at least 20 characters long"

        # Optional: Check for recommended format (kledo_pat_*)
        # But accept any key >= 20 chars for flexibility
        if api_key.startswith("kledo_pat_") and len(api_key) < 30:
            return False, "kledo_pat_ keys should be at least 30 characters"

        return True, ""

    def validate_base_url(self, url: str) -> tuple[bool, str]:
        """
        Validate base URL format.

        Args:
            url: Base URL to validate

        Returns:
            Tuple of (is_valid, error_message). error_message is empty if valid.
        """
        if not url or not isinstance(url, str):
            return False, "Base URL cannot be empty"

        url = url.strip()

        try:
            parsed = urlparse(url)

            # Must have scheme
            if not parsed.scheme:
                return False, "URL must include protocol (https://)"

            # Must be HTTPS for security
            if parsed.scheme != "https":
                return False, "Base URL must use HTTPS protocol for security"

            # Must have a valid netloc (domain)
            if not parsed.netloc:
                return False, "URL must include a valid domain"

            # Should not have query or fragment
            if parsed.query or parsed.fragment:
                return False, "Base URL should not contain query parameters or fragments"

            return True, ""

        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"

    def _file_has_api_key(self, file_path: Path) -> bool:
        """
        Check if a .env file contains KLEDO_API_KEY without loading it into environment.

        Args:
            file_path: Path to .env file to check

        Returns:
            True if file contains KLEDO_API_KEY, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            content = file_path.read_text()
            return "KLEDO_API_KEY=" in content
        except Exception as e:
            logger.debug(f"Error reading {file_path}: {str(e)}")
            return False

    def find_config_file(self) -> Optional[Path]:
        """
        Find the first existing config file from standard locations.

        Checks self.env_path first (for tests and custom paths), then standard locations.
        Does NOT load environment variables during search to avoid pollution.

        Returns:
            Path to existing config file, or None if not found
        """
        # First check the configured env_path (important for tests)
        if self._file_has_api_key(self.env_path):
            logger.debug(f"Found config file at: {self.env_path}")
            return self.env_path

        # Then check standard locations
        for location in self.get_config_file_locations():
            if location != self.env_path and self._file_has_api_key(location):
                logger.debug(f"Found config file at: {location}")
                return location

        return None

    def env_file_exists(self) -> bool:
        """
        Check if configuration exists (env vars or .env file).

        Returns:
            True if configured via env vars OR .env file exists with KLEDO_API_KEY
        """
        # First check environment variables (highest priority)
        if self.has_env_vars_configured():
            logger.debug("Configuration found via environment variables")
            return True

        # Only search standard locations if using default path
        # (for tests with custom paths, only check the specified path)
        if self._is_default_path:
            config_file = self.find_config_file()
            if config_file:
                # Update env_path to the found location for consistency
                self.env_path = config_file
                return True
        else:
            # Custom path: only check that specific path
            if self._file_has_api_key(self.env_path):
                return True

        return False

    def load_current_config(self) -> Optional[dict]:
        """
        Load current configuration from environment variables or .env file.

        Priority:
        1. Environment variables (KLEDO_API_KEY, KLEDO_BASE_URL)
        2. .env file in standard locations (or specified path for custom env_path)
        3. Return None if not configured

        Returns:
            Dictionary of configuration values, or None if not configured
        """
        # First check environment variables
        api_key = os.getenv("KLEDO_API_KEY", "").strip()
        base_url = os.getenv("KLEDO_BASE_URL", "").strip()

        # If not in env vars, check .env files
        if not api_key or not base_url:
            config_file = None

            if self._is_default_path:
                # Default path: search standard locations
                config_file = self.find_config_file()
            else:
                # Custom path: only check specified path
                if self._file_has_api_key(self.env_path):
                    config_file = self.env_path

            if config_file:
                load_dotenv(config_file, override=True)
                api_key = os.getenv("KLEDO_API_KEY", "").strip()
                base_url = os.getenv("KLEDO_BASE_URL", "").strip()

        # If still not configured, return None
        if not api_key or not base_url:
            return None

        config = {
            "api_key": api_key,
            "base_url": base_url,
            "cache_enabled": os.getenv("CACHE_ENABLED", "true"),
            "cache_ttl": os.getenv("CACHE_DEFAULT_TTL", "1800"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_file": os.getenv("LOG_FILE", "logs/kledo-mcp.log"),
            "mcp_server_name": os.getenv("MCP_SERVER_NAME", "kledo-crm"),
            "mcp_server_version": os.getenv("MCP_SERVER_VERSION", "1.0.0"),
        }

        return config

    def create_env_file(self, config: dict) -> bool:
        """
        Create .env file with provided configuration.

        Args:
            config: Dictionary with configuration values
                   Required keys: api_key, base_url
                   Optional keys: cache_enabled, cache_ttl, log_level, log_file

        Returns:
            True if file created successfully, False otherwise
        """
        try:
            # Validate required fields
            if "api_key" not in config or "base_url" not in config:
                logger.error("Missing required configuration: api_key and base_url")
                return False

            is_valid_key, key_error = self.validate_api_key(config["api_key"])
            if not is_valid_key:
                logger.error(f"Invalid API key: {key_error}")
                return False

            is_valid_url, url_error = self.validate_base_url(config["base_url"])
            if not is_valid_url:
                logger.error(f"Invalid base URL: {url_error}")
                return False

            # Ensure parent directory exists
            self.env_path.parent.mkdir(parents=True, exist_ok=True)

            # Build .env content with helpful comments
            env_content = self._build_env_content(config)

            # Write to file
            with open(self.env_path, "w") as f:
                f.write(env_content)

            logger.info(f"Created .env file at: {self.env_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create .env file: {str(e)}")
            return False

    def _build_env_content(self, config: dict) -> str:
        """
        Build .env file content from configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Formatted .env file content as string
        """
        # Get values with defaults
        api_key = config["api_key"]
        base_url = config["base_url"]
        cache_enabled = config.get("cache_enabled", "true")
        cache_ttl = config.get("cache_ttl", "1800")
        log_level = config.get("log_level", "INFO")
        log_file = config.get("log_file", "logs/kledo-mcp.log")
        mcp_name = config.get("mcp_server_name", "kledo-crm")
        mcp_version = config.get("mcp_server_version", "1.0.0")

        content = f"""# Kledo API Authentication
# Generated by setup wizard on {Path(__file__).parent.parent}

# API Key (RECOMMENDED for security)
# Your personal API key from Kledo dashboard
KLEDO_API_KEY={api_key}

# API Configuration
KLEDO_BASE_URL={base_url}

# Cache Configuration
# Enable caching to reduce API calls and improve performance
CACHE_ENABLED={cache_enabled}
CACHE_DEFAULT_TTL={cache_ttl}  # 30 minutes in seconds

# Logging
# LOG_LEVEL options: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL={log_level}
LOG_FILE={log_file}

# MCP Server Configuration
MCP_SERVER_NAME={mcp_name}
MCP_SERVER_VERSION={mcp_version}
"""
        return content

    def update_env_value(self, key: str, value: str) -> bool:
        """
        Update a single value in the .env file.

        Args:
            key: Environment variable key
            value: New value

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not self.env_path.exists():
                logger.error("Cannot update: .env file does not exist")
                return False

            set_key(str(self.env_path), key, value)
            logger.debug(f"Updated {key} in .env file")
            return True

        except Exception as e:
            logger.error(f"Failed to update .env file: {str(e)}")
            return False
