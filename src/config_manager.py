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
        if env_path is None:
            # Find .env in project root (parent of src/)
            self.env_path = Path(__file__).parent.parent / ".env"
        else:
            self.env_path = Path(env_path)

        self.env_example_path = self.env_path.parent / ".env.example"

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

    def env_file_exists(self) -> bool:
        """
        Check if .env file exists and has KLEDO_API_KEY set.

        Returns:
            True if .env exists with KLEDO_API_KEY, False otherwise
        """
        if not self.env_path.exists():
            return False

        # Load and check for KLEDO_API_KEY
        load_dotenv(self.env_path)
        api_key = os.getenv("KLEDO_API_KEY")

        return api_key is not None and len(api_key.strip()) > 0

    def load_current_config(self) -> Optional[dict]:
        """
        Load current configuration from .env file.

        Returns:
            Dictionary of configuration values, or None if .env doesn't exist
        """
        if not self.env_path.exists():
            return None

        load_dotenv(self.env_path)

        config = {
            "api_key": os.getenv("KLEDO_API_KEY", ""),
            "base_url": os.getenv("KLEDO_BASE_URL", ""),
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
