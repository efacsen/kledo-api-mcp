"""
Unit tests for SetupWizard and ConfigManager.

Tests first-run detection, validation logic, and configuration management.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from src.config_manager import ConfigManager
from src.setup import SetupWizard


class TestConfigManager:
    """Test ConfigManager validation and file operations."""

    def test_validate_api_key_valid_kledo_pat(self):
        """Test that valid kledo_pat_ keys are accepted."""
        cm = ConfigManager()

        # Valid kledo_pat_ key (30+ chars)
        is_valid, error = cm.validate_api_key("kledo_pat_1234567890123456789012345")
        assert is_valid is True
        assert error == ""

    def test_validate_api_key_valid_generic(self):
        """Test that generic long keys are accepted."""
        cm = ConfigManager()

        # Valid generic key (20+ chars)
        is_valid, error = cm.validate_api_key("generic_api_key_1234567890")
        assert is_valid is True
        assert error == ""

    def test_validate_api_key_invalid_short(self):
        """Test that short strings are rejected."""
        cm = ConfigManager()

        # Too short
        is_valid, error = cm.validate_api_key("short")
        assert is_valid is False
        assert "at least 20 characters" in error

    def test_validate_api_key_invalid_empty(self):
        """Test that empty strings are rejected."""
        cm = ConfigManager()

        is_valid, error = cm.validate_api_key("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_api_key_invalid_kledo_pat_short(self):
        """Test that kledo_pat_ keys must be 30+ chars."""
        cm = ConfigManager()

        # kledo_pat_ but too short (20+ but <30)
        is_valid, error = cm.validate_api_key("kledo_pat_12345678901")
        assert is_valid is False
        assert "at least 30 characters" in error

    def test_validate_base_url_valid_https(self):
        """Test that HTTPS URLs are accepted."""
        cm = ConfigManager()

        is_valid, error = cm.validate_base_url("https://api.kledo.com/api/v1")
        assert is_valid is True
        assert error == ""

    def test_validate_base_url_invalid_http(self):
        """Test that HTTP URLs are rejected."""
        cm = ConfigManager()

        is_valid, error = cm.validate_base_url("http://api.kledo.com")
        assert is_valid is False
        assert "HTTPS" in error

    def test_validate_base_url_invalid_no_protocol(self):
        """Test that URLs without protocol are rejected."""
        cm = ConfigManager()

        is_valid, error = cm.validate_base_url("api.kledo.com")
        assert is_valid is False
        assert "protocol" in error

    def test_validate_base_url_invalid_empty(self):
        """Test that empty URLs are rejected."""
        cm = ConfigManager()

        is_valid, error = cm.validate_base_url("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_env_file_exists_no_file(self, tmp_path, monkeypatch):
        """Test env_file_exists returns False when .env missing."""
        # Clear environment variables so test is isolated
        monkeypatch.delenv("KLEDO_API_KEY", raising=False)
        monkeypatch.delenv("KLEDO_BASE_URL", raising=False)

        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)

        assert cm.env_file_exists() is False

    def test_env_file_exists_empty_file(self, tmp_path, monkeypatch):
        """Test env_file_exists returns False for empty .env."""
        # Clear environment variables so test is isolated
        monkeypatch.delenv("KLEDO_API_KEY", raising=False)
        monkeypatch.delenv("KLEDO_BASE_URL", raising=False)

        env_path = tmp_path / ".env"
        env_path.write_text("")
        cm = ConfigManager(env_path=env_path)

        assert cm.env_file_exists() is False

    def test_env_file_exists_with_api_key(self, tmp_path):
        """Test env_file_exists returns True when API key present."""
        env_path = tmp_path / ".env"
        env_path.write_text("KLEDO_API_KEY=test_key_1234567890\n")
        cm = ConfigManager(env_path=env_path)

        assert cm.env_file_exists() is True

    def test_create_env_file_success(self, tmp_path):
        """Test creating .env file with valid config."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)

        config = {
            "api_key": "kledo_pat_1234567890123456789012345",
            "base_url": "https://api.kledo.com/api/v1",
        }

        result = cm.create_env_file(config)
        assert result is True
        assert env_path.exists()

        # Verify content
        content = env_path.read_text()
        assert "KLEDO_API_KEY=kledo_pat_1234567890123456789012345" in content
        assert "KLEDO_BASE_URL=https://api.kledo.com/api/v1" in content

    def test_create_env_file_invalid_api_key(self, tmp_path):
        """Test creating .env file fails with invalid API key."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)

        config = {
            "api_key": "short",  # Too short
            "base_url": "https://api.kledo.com/api/v1",
        }

        result = cm.create_env_file(config)
        assert result is False
        assert not env_path.exists()

    def test_create_env_file_invalid_url(self, tmp_path):
        """Test creating .env file fails with invalid URL."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)

        config = {
            "api_key": "kledo_pat_1234567890123456789012345",
            "base_url": "http://api.kledo.com",  # HTTP not allowed
        }

        result = cm.create_env_file(config)
        assert result is False
        assert not env_path.exists()

    def test_create_env_file_missing_required_fields(self, tmp_path):
        """Test creating .env file fails without required fields."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)

        config = {
            "api_key": "kledo_pat_1234567890123456789012345",
            # Missing base_url
        }

        result = cm.create_env_file(config)
        assert result is False

    def test_load_current_config_no_file(self, tmp_path, monkeypatch):
        """Test load_current_config returns None when .env missing."""
        # Clear environment variables so test is isolated
        monkeypatch.delenv("KLEDO_API_KEY", raising=False)
        monkeypatch.delenv("KLEDO_BASE_URL", raising=False)

        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)

        config = cm.load_current_config()
        assert config is None

    def test_load_current_config_with_file(self, tmp_path, monkeypatch):
        """Test load_current_config reads existing .env."""
        # Clear environment variables so they don't override file values
        monkeypatch.delenv("KLEDO_API_KEY", raising=False)
        monkeypatch.delenv("KLEDO_BASE_URL", raising=False)

        env_path = tmp_path / ".env"
        env_path.write_text("""KLEDO_API_KEY=test_key_123
KLEDO_BASE_URL=https://api.kledo.com/api/v1
CACHE_ENABLED=false
LOG_LEVEL=DEBUG
""")
        # Change to tmp directory so dotenv reads the right file
        monkeypatch.chdir(tmp_path)

        cm = ConfigManager(env_path=env_path)

        config = cm.load_current_config()
        assert config is not None
        assert config["api_key"] == "test_key_123"
        assert config["base_url"] == "https://api.kledo.com/api/v1"
        assert config["cache_enabled"] == "false"
        assert config["log_level"] == "DEBUG"


class TestSetupWizard:
    """Test SetupWizard interactive setup flow."""

    def test_detect_first_run_no_env(self, tmp_path, monkeypatch):
        """Test detect_first_run returns True when .env missing."""
        # Clear environment variables so test is isolated
        monkeypatch.delenv("KLEDO_API_KEY", raising=False)
        monkeypatch.delenv("KLEDO_BASE_URL", raising=False)

        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        assert wizard.detect_first_run() is True

    def test_detect_first_run_with_env(self, tmp_path, monkeypatch):
        """Test detect_first_run returns False when .env exists."""
        # Clear environment variables so they don't interfere
        monkeypatch.delenv("KLEDO_API_KEY", raising=False)
        monkeypatch.delenv("KLEDO_BASE_URL", raising=False)

        env_path = tmp_path / ".env"
        env_path.write_text("KLEDO_API_KEY=test_key_1234567890\n")
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        assert wizard.detect_first_run() is False

    def test_save_configuration_success(self, tmp_path, monkeypatch):
        """Test save_configuration creates .env with correct content."""
        # Clear environment variables
        monkeypatch.delenv("KLEDO_API_KEY", raising=False)
        monkeypatch.delenv("KLEDO_BASE_URL", raising=False)

        # Use tmp_path for .kledo config directory to avoid writing to user home
        kledo_config_dir = tmp_path / ".kledo"
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        config = {
            "api_key": "kledo_pat_1234567890123456789012345",
            "base_url": "https://api.kledo.com/api/v1",
        }

        result = wizard.save_configuration(config)
        assert result is True

        # Check that config was saved to ~/.kledo/.env (which is tmp_path/.kledo/.env in test)
        kledo_env_path = kledo_config_dir / ".env"
        assert kledo_env_path.exists(), f"Expected config at {kledo_env_path}"

        # Verify content
        content = kledo_env_path.read_text()
        assert "KLEDO_API_KEY=kledo_pat_1234567890123456789012345" in content
        assert "KLEDO_BASE_URL=https://api.kledo.com/api/v1" in content

    def test_save_configuration_invalid_config(self, tmp_path):
        """Test save_configuration fails with invalid config."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        config = {
            "api_key": "short",  # Invalid
            "base_url": "https://api.kledo.com/api/v1",
        }

        result = wizard.save_configuration(config)
        assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_success(self, tmp_path):
        """Test connection test succeeds with valid credentials."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        # Mock KledoAuthenticator
        with patch("src.setup.KledoAuthenticator") as mock_auth_class:
            mock_auth = Mock()
            mock_auth.login = AsyncMock(return_value=True)
            mock_auth.get_auth_headers = Mock(return_value={"Authorization": "Bearer test"})
            mock_auth_class.return_value = mock_auth

            # Mock httpx module
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()

                mock_client_instance = Mock()
                mock_client_instance.get = AsyncMock(return_value=mock_response)
                mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
                mock_client_instance.__aexit__ = AsyncMock(return_value=None)

                mock_client_class.return_value = mock_client_instance

                success, message = await wizard.test_connection(
                    "kledo_pat_test123456789012345",
                    "https://api.kledo.com/api/v1"
                )

                assert success is True
                assert "successful" in message.lower()

    @pytest.mark.asyncio
    async def test_test_connection_invalid_key(self, tmp_path):
        """Test connection test fails with invalid API key."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        # Mock KledoAuthenticator
        with patch("src.setup.KledoAuthenticator") as mock_auth_class:
            mock_auth = Mock()
            mock_auth.login = AsyncMock(return_value=True)
            mock_auth.get_auth_headers = Mock(return_value={"Authorization": "Bearer test"})
            mock_auth_class.return_value = mock_auth

            # Mock httpx module - return 401
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = Mock()
                mock_response.status_code = 401

                mock_client_instance = Mock()
                mock_client_instance.get = AsyncMock(return_value=mock_response)
                mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
                mock_client_instance.__aexit__ = AsyncMock(return_value=None)

                mock_client_class.return_value = mock_client_instance

                success, message = await wizard.test_connection(
                    "kledo_pat_invalid",
                    "https://api.kledo.com/api/v1"
                )

                assert success is False
                assert "Invalid API key" in message

    @pytest.mark.asyncio
    async def test_test_connection_network_error(self, tmp_path):
        """Test connection test handles network errors."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        # Mock KledoAuthenticator
        with patch("src.setup.KledoAuthenticator") as mock_auth_class:
            mock_auth = Mock()
            mock_auth.login = AsyncMock(return_value=True)
            mock_auth.get_auth_headers = Mock(return_value={"Authorization": "Bearer test"})
            mock_auth_class.return_value = mock_auth

            # Mock httpx module - raise exception
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client_instance = Mock()
                mock_client_instance.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
                mock_client_instance.__aexit__ = AsyncMock(return_value=None)

                mock_client_class.return_value = mock_client_instance

                success, message = await wizard.test_connection(
                    "kledo_pat_test123456789012345",
                    "https://api.kledo.com/api/v1"
                )

                assert success is False
                assert "failed" in message.lower()

    def test_prompt_api_key_validation(self, tmp_path, monkeypatch):
        """Test prompt_api_key validates input before accepting."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        # Mock input: first short (invalid), then valid
        inputs = iter(["short", "kledo_pat_1234567890123456789012345"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        # Mock print to suppress output
        with patch("builtins.print"):
            api_key = wizard.prompt_api_key()

        assert api_key == "kledo_pat_1234567890123456789012345"

    def test_prompt_base_url_uses_default(self, tmp_path, monkeypatch):
        """Test prompt_base_url uses default when user presses Enter."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        # Mock input: empty string (use default)
        monkeypatch.setattr("builtins.input", lambda _: "")

        # Mock print to suppress output
        with patch("builtins.print"):
            base_url = wizard.prompt_base_url()

        assert base_url == "https://api.kledo.com/api/v1"

    def test_prompt_base_url_custom_value(self, tmp_path, monkeypatch):
        """Test prompt_base_url accepts custom valid URL."""
        env_path = tmp_path / ".env"
        cm = ConfigManager(env_path=env_path)
        wizard = SetupWizard(config_manager=cm)

        # Mock input: custom URL
        monkeypatch.setattr("builtins.input", lambda _: "https://custom.api.com/v2")

        # Mock print to suppress output
        with patch("builtins.print"):
            base_url = wizard.prompt_base_url()

        assert base_url == "https://custom.api.com/v2"
