"""
Tests for CLI argument parsing and command handlers.
"""
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest

from src.cli import (
    parse_args,
    handle_setup,
    handle_test,
    handle_show_config,
    handle_version,
    dispatch_command,
)


class TestParseArgs:
    """Test argument parsing."""

    def test_parse_args_setup(self):
        """Test --setup flag is parsed correctly."""
        args = parse_args(["--setup"])
        assert args.setup is True
        assert args.test is False
        assert args.show_config is False
        assert args.init is False
        assert args.version is False

    def test_parse_args_test(self):
        """Test --test flag is parsed correctly."""
        args = parse_args(["--test"])
        assert args.setup is False
        assert args.test is True
        assert args.show_config is False
        assert args.init is False
        assert args.version is False

    def test_parse_args_show_config(self):
        """Test --show-config flag is parsed correctly."""
        args = parse_args(["--show-config"])
        assert args.setup is False
        assert args.test is False
        assert args.show_config is True
        assert args.init is False
        assert args.version is False

    def test_parse_args_init(self):
        """Test --init flag is parsed correctly."""
        args = parse_args(["--init"])
        assert args.setup is False
        assert args.test is False
        assert args.show_config is False
        assert args.init is True
        assert args.version is False

    def test_parse_args_version(self):
        """Test --version flag is parsed correctly."""
        args = parse_args(["--version"])
        assert args.setup is False
        assert args.test is False
        assert args.show_config is False
        assert args.init is False
        assert args.version is True

    def test_parse_args_no_args(self):
        """Test parsing with no arguments."""
        args = parse_args([])
        assert args.setup is False
        assert args.test is False
        assert args.show_config is False
        assert args.init is False
        assert args.version is False


class TestHandleSetup:
    """Test setup command handler."""

    def test_handle_setup_success(self, monkeypatch):
        """Test successful setup."""
        # Mock run_setup_wizard to return success
        mock_run_setup = Mock(return_value=0)
        monkeypatch.setattr("src.cli.run_setup_wizard", mock_run_setup)

        result = handle_setup()

        assert result == 0
        mock_run_setup.assert_called_once()

    def test_handle_setup_failure(self, monkeypatch):
        """Test failed setup."""
        # Mock run_setup_wizard to return failure
        mock_run_setup = Mock(return_value=1)
        monkeypatch.setattr("src.cli.run_setup_wizard", mock_run_setup)

        result = handle_setup()

        assert result == 1
        mock_run_setup.assert_called_once()


class TestHandleTest:
    """Test connection test command handler."""

    def test_handle_test_no_config(self, monkeypatch, capsys):
        """Test when .env file doesn't exist."""
        # Mock ConfigManager to return no config
        mock_config_manager = Mock()
        mock_config_manager.env_file_exists.return_value = False

        mock_config_class = Mock(return_value=mock_config_manager)
        monkeypatch.setattr("src.cli.ConfigManager", mock_config_class)

        result = handle_test()

        assert result == 1
        captured = capsys.readouterr()
        assert "No configuration found" in captured.out
        assert "kledo-mcp --setup" in captured.out

    def test_handle_test_no_api_key(self, monkeypatch, capsys):
        """Test when KLEDO_API_KEY is missing from .env."""
        # Mock ConfigManager
        mock_config_manager = Mock()
        mock_config_manager.env_file_exists.return_value = True
        mock_config_manager.env_path = Path(".env")

        mock_config_class = Mock(return_value=mock_config_manager)
        monkeypatch.setattr("src.cli.ConfigManager", mock_config_class)

        # Mock load_dotenv
        monkeypatch.setattr("src.cli.load_dotenv", Mock())

        # Mock os.getenv to return None for KLEDO_API_KEY
        def mock_getenv(key, default=None):
            if key == "KLEDO_API_KEY":
                return None
            return default

        monkeypatch.setattr("os.getenv", mock_getenv)

        result = handle_test()

        assert result == 1
        captured = capsys.readouterr()
        assert "KLEDO_API_KEY not found" in captured.out

    def test_handle_test_success(self, monkeypatch, capsys):
        """Test successful connection test."""
        # Mock ConfigManager
        mock_config_manager = Mock()
        mock_config_manager.env_file_exists.return_value = True
        mock_config_manager.env_path = Path(".env")

        mock_config_class = Mock(return_value=mock_config_manager)
        monkeypatch.setattr("src.cli.ConfigManager", mock_config_class)

        # Mock load_dotenv
        monkeypatch.setattr("src.cli.load_dotenv", Mock())

        # Mock os.getenv
        def mock_getenv(key, default=None):
            if key == "KLEDO_API_KEY":
                return "test_api_key_12345678901234567890"
            elif key == "KLEDO_BASE_URL":
                return "https://api.kledo.com/api/v1"
            return default

        monkeypatch.setattr("os.getenv", mock_getenv)

        # Mock KledoAuthenticator
        mock_auth = Mock()
        mock_auth_class = Mock(return_value=mock_auth)
        monkeypatch.setattr("src.cli.KledoAuthenticator", mock_auth_class)

        # Mock asyncio.run to return success
        async def mock_test_success(auth, base_url):
            return True

        monkeypatch.setattr("src.cli._test_connection", mock_test_success)
        monkeypatch.setattr("asyncio.run", lambda coro: True)

        result = handle_test()

        assert result == 0
        captured = capsys.readouterr()
        assert "Connection successful" in captured.out

    def test_handle_test_failure(self, monkeypatch, capsys):
        """Test failed connection test."""
        # Mock ConfigManager
        mock_config_manager = Mock()
        mock_config_manager.env_file_exists.return_value = True
        mock_config_manager.env_path = Path(".env")

        mock_config_class = Mock(return_value=mock_config_manager)
        monkeypatch.setattr("src.cli.ConfigManager", mock_config_class)

        # Mock load_dotenv
        monkeypatch.setattr("src.cli.load_dotenv", Mock())

        # Mock os.getenv
        def mock_getenv(key, default=None):
            if key == "KLEDO_API_KEY":
                return "test_api_key_12345678901234567890"
            elif key == "KLEDO_BASE_URL":
                return "https://api.kledo.com/api/v1"
            return default

        monkeypatch.setattr("os.getenv", mock_getenv)

        # Mock KledoAuthenticator
        mock_auth = Mock()
        mock_auth_class = Mock(return_value=mock_auth)
        monkeypatch.setattr("src.cli.KledoAuthenticator", mock_auth_class)

        # Mock asyncio.run to return failure
        monkeypatch.setattr("asyncio.run", lambda coro: False)

        result = handle_test()

        assert result == 1
        captured = capsys.readouterr()
        assert "Connection failed" in captured.out


class TestHandleShowConfig:
    """Test show-config command handler."""

    def test_handle_show_config_with_existing_config(self, monkeypatch, capsys):
        """Test show-config with existing .env file."""
        # Mock ConfigManager
        mock_config_manager = Mock()
        mock_config_manager.load_current_config.return_value = {
            "api_key": "test_api_key_123456789012345678901234567890",
            "base_url": "https://api.kledo.com/api/v1",
            "cache_enabled": "true",
            "log_level": "INFO"
        }

        mock_config_class = Mock(return_value=mock_config_manager)
        monkeypatch.setattr("src.cli.ConfigManager", mock_config_class)

        # Mock platform.system to return known OS
        monkeypatch.setattr("platform.system", lambda: "Darwin")

        result = handle_show_config()

        assert result == 0
        captured = capsys.readouterr()

        # Verify JSON output
        assert "mcpServers" in captured.out
        assert "kledo-crm" in captured.out
        assert "KLEDO_API_KEY" in captured.out
        assert "Loaded configuration from .env" in captured.out

        # Verify macOS path in output
        assert "Library/Application Support/Claude" in captured.out

    def test_handle_show_config_without_config(self, monkeypatch, capsys):
        """Test show-config without existing .env file."""
        # Mock ConfigManager
        mock_config_manager = Mock()
        mock_config_manager.load_current_config.return_value = None

        mock_config_class = Mock(return_value=mock_config_manager)
        monkeypatch.setattr("src.cli.ConfigManager", mock_config_class)

        # Mock platform.system
        monkeypatch.setattr("platform.system", lambda: "Linux")

        result = handle_show_config()

        assert result == 0
        captured = capsys.readouterr()

        # Verify warning message
        assert "No configuration found" in captured.out
        assert "YOUR_API_KEY_HERE" in captured.out

        # Verify Linux path in output
        assert ".config/Claude" in captured.out

    def test_handle_show_config_windows(self, monkeypatch, capsys):
        """Test show-config on Windows."""
        # Mock ConfigManager
        mock_config_manager = Mock()
        mock_config_manager.load_current_config.return_value = {
            "api_key": "test_key",
            "base_url": "https://api.kledo.com/api/v1"
        }

        mock_config_class = Mock(return_value=mock_config_manager)
        monkeypatch.setattr("src.cli.ConfigManager", mock_config_class)

        # Mock platform.system to return Windows
        monkeypatch.setattr("platform.system", lambda: "Windows")

        result = handle_show_config()

        assert result == 0
        captured = capsys.readouterr()

        # Verify Windows path in output
        assert "AppData/Roaming/Claude" in captured.out


class TestHandleVersion:
    """Test version command handler."""

    def test_handle_version(self, monkeypatch, capsys):
        """Test version command output."""
        result = handle_version()

        assert result == 0
        captured = capsys.readouterr()

        # Verify version output
        assert "Kledo MCP Server" in captured.out
        assert "v0.1.0" in captured.out or "v1.0.0" in captured.out
        assert "github.com/efacsen/kledo-api-mcp" in captured.out

    def test_handle_version_reads_from_pyproject(self, monkeypatch, capsys):
        """Test that version is read from pyproject.toml."""
        # Mock pyproject.toml reading
        mock_pyproject = 'version = "0.1.0"'

        # Create a mock Path object
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.parent.parent = Path(__file__).parent.parent

        mock_file = MagicMock()
        mock_file.read.return_value = mock_pyproject
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = None

        with patch("builtins.open", return_value=mock_file):
            result = handle_version()

        assert result == 0
        captured = capsys.readouterr()
        assert "0.1.0" in captured.out or "v" in captured.out


class TestDispatchCommand:
    """Test command dispatching."""

    def test_dispatch_setup(self, monkeypatch):
        """Test dispatching --setup command."""
        mock_handle = Mock(return_value=0)
        monkeypatch.setattr("src.cli.handle_setup", mock_handle)

        args = parse_args(["--setup"])
        result = dispatch_command(args)

        assert result == 0
        mock_handle.assert_called_once()

    def test_dispatch_test(self, monkeypatch):
        """Test dispatching --test command."""
        mock_handle = Mock(return_value=0)
        monkeypatch.setattr("src.cli.handle_test", mock_handle)

        args = parse_args(["--test"])
        result = dispatch_command(args)

        assert result == 0
        mock_handle.assert_called_once()

    def test_dispatch_show_config(self, monkeypatch):
        """Test dispatching --show-config command."""
        mock_handle = Mock(return_value=0)
        monkeypatch.setattr("src.cli.handle_show_config", mock_handle)

        args = parse_args(["--show-config"])
        result = dispatch_command(args)

        assert result == 0
        mock_handle.assert_called_once()

    def test_dispatch_init(self, monkeypatch):
        """Test dispatching --init command (same as setup)."""
        mock_handle = Mock(return_value=0)
        monkeypatch.setattr("src.cli.handle_setup", mock_handle)

        args = parse_args(["--init"])
        result = dispatch_command(args)

        assert result == 0
        mock_handle.assert_called_once()

    def test_dispatch_version(self, monkeypatch):
        """Test dispatching --version command."""
        mock_handle = Mock(return_value=0)
        monkeypatch.setattr("src.cli.handle_version", mock_handle)

        args = parse_args(["--version"])
        result = dispatch_command(args)

        assert result == 0
        mock_handle.assert_called_once()

    def test_dispatch_no_command(self):
        """Test dispatching with no command specified."""
        args = parse_args([])
        result = dispatch_command(args)

        # Should return 1 for no command
        assert result == 1


class TestCommandIdempotency:
    """Test that commands are idempotent (safe to run multiple times)."""

    def test_setup_is_idempotent(self, monkeypatch):
        """Test that setup command can be run multiple times."""
        # Mock run_setup_wizard to succeed
        call_count = 0

        def mock_run_setup():
            nonlocal call_count
            call_count += 1
            return 0

        monkeypatch.setattr("src.cli.run_setup_wizard", mock_run_setup)

        # Run setup multiple times
        result1 = handle_setup()
        result2 = handle_setup()

        assert result1 == 0
        assert result2 == 0
        assert call_count == 2  # Both calls went through

    def test_test_is_idempotent(self, monkeypatch):
        """Test that test command can be run multiple times."""
        # Mock all dependencies
        mock_config_manager = Mock()
        mock_config_manager.env_file_exists.return_value = True
        mock_config_manager.env_path = Path(".env")

        monkeypatch.setattr("src.cli.ConfigManager", Mock(return_value=mock_config_manager))
        monkeypatch.setattr("src.cli.load_dotenv", Mock())
        monkeypatch.setattr("os.getenv", lambda k, d=None: "test_key_12345678901234567890" if k == "KLEDO_API_KEY" else d)
        monkeypatch.setattr("src.cli.KledoAuthenticator", Mock())
        monkeypatch.setattr("asyncio.run", lambda coro: True)

        # Run test multiple times
        result1 = handle_test()
        result2 = handle_test()

        assert result1 == 0
        assert result2 == 0

    def test_show_config_is_idempotent(self, monkeypatch):
        """Test that show-config command can be run multiple times."""
        mock_config_manager = Mock()
        mock_config_manager.load_current_config.return_value = {
            "api_key": "test_key",
            "base_url": "https://api.kledo.com/api/v1"
        }

        monkeypatch.setattr("src.cli.ConfigManager", Mock(return_value=mock_config_manager))
        monkeypatch.setattr("platform.system", lambda: "Darwin")

        # Run show-config multiple times
        result1 = handle_show_config()
        result2 = handle_show_config()

        assert result1 == 0
        assert result2 == 0
