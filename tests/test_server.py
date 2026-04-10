"""
Tests for the Kledo MCP Server FastMCP shell (Phase 3+).

This file replaces the pre-1.0 module-level-function test suite. After Phase 3,
`src.server` no longer exposes `list_tools()`, `call_tool()`, `initialize_client()`,
or a module-level `client` variable — the new surface is `mcp` (FastMCP instance),
`AppContext`, `lifespan`, `_build_client`, and `_recovery_hint`.
"""
import asyncio
import inspect
import os
from dataclasses import is_dataclass
from unittest.mock import AsyncMock, Mock, patch

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

import src.server as server_module
from src.server import AppContext, _build_client, _recovery_hint, _scrub_secrets, lifespan, mcp


EXPECTED_PREFIXES = [
    "financial_", "invoice_", "order_", "product_", "contact_",
    "delivery_", "utility_", "sales_rep_", "revenue_",
    "analytics_", "commission_",
]


class TestFastMCPSetup:
    """Verifies SDK-01 + SDK-02 shell: FastMCP instance, AppContext, _build_client, lifespan."""

    def test_mcp_instance_is_fastmcp(self):
        """mcp must be a FastMCP instance."""
        assert isinstance(mcp, FastMCP)

    def test_mcp_name_is_kledo_crm(self):
        """mcp.name must be 'kledo-crm' (or env override)."""
        import os
        expected_name = os.getenv("MCP_SERVER_NAME", "kledo-crm")
        assert mcp.name == expected_name

    def test_app_context_dataclass_exists(self):
        """AppContext must be a dataclass."""
        assert is_dataclass(AppContext)

    def test_build_client_is_async(self):
        """_build_client must be an async coroutine function."""
        assert asyncio.iscoroutinefunction(_build_client)

    def test_lifespan_is_async_context_manager(self):
        """lifespan must be an async generator function (asynccontextmanager)."""
        # asynccontextmanager wraps the function — inspect the underlying generator
        assert inspect.isasyncgenfunction(lifespan.__wrapped__) or asyncio.iscoroutinefunction(lifespan)


class TestInstructions:
    """Verifies SDK-03: mcp.instructions contains required domain facts."""

    def test_instructions_non_empty(self):
        """mcp.instructions must be a non-empty string longer than 50 chars."""
        assert mcp.instructions and len(mcp.instructions) > 50

    def test_instructions_contains_status_codes(self):
        """Instructions must reference status codes 1, Paid, and Unpaid."""
        assert "1" in mcp.instructions and "Paid" in mcp.instructions and "Unpaid" in mcp.instructions

    def test_instructions_contains_commission_formula(self):
        """Instructions must mention commission and the pre-tax subtotal formula."""
        assert "commission" in mcp.instructions.lower() and (
            "subtotal" in mcp.instructions.lower() or "pre-tax" in mcp.instructions.lower()
        )

    def test_instructions_contains_idr(self):
        """Instructions must mention IDR or Rupiah."""
        assert "IDR" in mcp.instructions or "Rupiah" in mcp.instructions

    def test_instructions_contains_bilingual(self):
        """Instructions must include Indonesian term 'Lunas' (bilingual per CLAUDE.md)."""
        assert "Lunas" in mcp.instructions

    def test_instructions_contains_id_lookup_guidance(self):
        """Instructions must mention 'list' and 'detail' to guide ID lookup order."""
        assert "list" in mcp.instructions.lower() and "detail" in mcp.instructions.lower()


class TestLifespanContext:
    """Verifies SDK-02 runtime behavior: lifespan yields AppContext with client."""

    @pytest.mark.asyncio
    async def test_lifespan_yields_app_context_with_client(self):
        """Lifespan must yield an AppContext whose .client is the built KledoAPIClient."""
        mock_client = Mock(spec_set=["_http_client"])
        mock_client._http_client = None  # skip teardown branch
        with patch("src.server._build_client", AsyncMock(return_value=mock_client)):
            async with lifespan(mcp) as ctx:
                assert isinstance(ctx, AppContext)
                assert ctx.client is mock_client

    @pytest.mark.asyncio
    async def test_lifespan_teardown_closes_http_client(self):
        """Lifespan teardown must await _http_client.aclose() when client has an HTTP session."""
        mock_http = AsyncMock()
        mock_client = Mock()
        mock_client._http_client = mock_http
        with patch("src.server._build_client", AsyncMock(return_value=mock_client)):
            async with lifespan(mcp) as ctx:
                pass
            mock_http.aclose.assert_awaited_once()


class TestErrorReturns:
    """Verifies SDK-04: ToolError is importable and _recovery_hint returns safe hints."""

    def test_tool_error_is_importable(self):
        """ToolError must be importable from mcp.server.fastmcp.exceptions (SDK sanity check)."""
        # Already imported at module level — if we reach here, the import succeeded
        assert ToolError is not None

    def test_recovery_hint_helper_exists(self):
        """_recovery_hint must be a callable exported from src.server."""
        assert callable(_recovery_hint)

    def test_recovery_hint_401_mentions_api_key(self):
        """A 401 error hint must tell the user to check KLEDO_API_KEY."""
        assert "KLEDO_API_KEY" in _recovery_hint("invoice_list", Exception("HTTP 401 Unauthorized"))

    def test_recovery_hint_404_mentions_list_first(self):
        """A 404 error hint must suggest calling a list tool first."""
        hint = _recovery_hint("invoice_detail", Exception("404 not found"))
        assert "list" in hint.lower()

    def test_recovery_hint_timeout_mentions_network(self):
        """A timeout error hint must reference KLEDO_BASE_URL or network."""
        hint = _recovery_hint("revenue_summary", Exception("connect timeout"))
        assert "KLEDO_BASE_URL" in hint or "network" in hint.lower()

    def test_recovery_hint_does_not_leak_api_key(self):
        """_recovery_hint must NOT include raw credential strings from the exception message."""
        hint = _recovery_hint("x", Exception("401 unauthorized key=sk_live_abc123"))
        assert "sk_live_abc123" not in hint


class TestToolRegistration:
    """Verifies SDK-02 tool count: dispatch bridge registers all legacy tools."""

    @pytest.mark.asyncio
    async def test_mcp_has_all_legacy_tools(self):
        """mcp.list_tools() must return at least 24 tools."""
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert len(names) >= 24, f"Expected >=24 tools, got {len(names)}: {sorted(names)}"

    @pytest.mark.asyncio
    async def test_tools_include_expected_prefixes(self):
        """At least one tool must exist for each of the 11 expected category prefixes."""
        tools = await mcp.list_tools()
        names = [t.name for t in tools]
        for prefix in EXPECTED_PREFIXES:
            assert any(n.startswith(prefix) for n in names), (
                f"No tool found with prefix {prefix!r} — names seen: {sorted(names)}"
            )


class TestScrubSecrets:
    """Verifies _scrub_secrets removes API key values from error messages."""

    def test_scrub_secrets_redacts_api_key_in_message(self):
        """_scrub_secrets must replace a long API key value with ***REDACTED***."""
        with patch.dict(os.environ, {"KLEDO_API_KEY": "sk_live_test_abc123xyz"}):
            result = _scrub_secrets("error with sk_live_test_abc123xyz inside")
            assert "sk_live_test_abc123xyz" not in result
            assert "***REDACTED***" in result

    def test_scrub_secrets_passthrough_when_key_absent(self):
        """_scrub_secrets must not modify message when KLEDO_API_KEY is unset."""
        env = {k: v for k, v in os.environ.items() if k != "KLEDO_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            msg = "some error without a key"
            assert _scrub_secrets(msg) == msg

    def test_scrub_secrets_passthrough_when_key_not_in_message(self):
        """_scrub_secrets must not modify message when key value is absent from it."""
        with patch.dict(os.environ, {"KLEDO_API_KEY": "sk_live_xyz999888777"}):
            msg = "HTTP 500 internal server error"
            assert _scrub_secrets(msg) == msg

    def test_scrub_secrets_ignores_short_key(self):
        """_scrub_secrets must not redact keys shorter than 8 chars (avoids common words)."""
        with patch.dict(os.environ, {"KLEDO_API_KEY": "short"}):
            msg = "error mentioning short word"
            assert _scrub_secrets(msg) == msg


class TestBuildClientErrors:
    """Verifies _build_client raises ValueError for missing credentials."""

    @pytest.mark.asyncio
    async def test_build_client_raises_without_credentials(self):
        """_build_client must raise ValueError when no API key or email/password set."""
        env = {k: v for k, v in os.environ.items() if k not in ("KLEDO_API_KEY", "KLEDO_EMAIL", "KLEDO_PASSWORD")}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="KLEDO_API_KEY"):
                await _build_client()

    @pytest.mark.asyncio
    async def test_build_client_raises_on_failed_login(self):
        """_build_client must raise ValueError when auth.login() returns False."""
        with patch.dict(os.environ, {"KLEDO_API_KEY": "sk_live_test_abc123"}, clear=False):
            mock_auth = AsyncMock()
            mock_auth.login = AsyncMock(return_value=False)
            with patch("src.server.KledoAuthenticator", return_value=mock_auth):
                with pytest.raises(ValueError, match="Failed to authenticate"):
                    await _build_client()

    @pytest.mark.asyncio
    async def test_build_client_email_password_path(self):
        """_build_client must succeed via email/password when API key absent."""
        env = {k: v for k, v in os.environ.items() if k not in ("KLEDO_API_KEY",)}
        env["KLEDO_EMAIL"] = "test@example.com"
        env["KLEDO_PASSWORD"] = "testpassword"
        with patch.dict(os.environ, env, clear=True):
            mock_auth = AsyncMock()
            mock_auth.login = AsyncMock(return_value=True)
            mock_client = Mock()
            with patch("src.server.KledoAuthenticator", return_value=mock_auth):
                with patch("src.server.KledoAPIClient", return_value=mock_client):
                    with patch("src.server.KledoCache"):
                        result = await _build_client()
            assert result is mock_client


class TestRecoveryHintBranches:
    """Covers additional _recovery_hint branches for complete hint coverage."""

    def test_recovery_hint_403_mentions_permission(self):
        """A 403 error hint must mention API key permission/scopes."""
        hint = _recovery_hint("product_list", Exception("403 Forbidden"))
        assert "permission" in hint.lower() or "scopes" in hint.lower()

    def test_recovery_hint_rate_limit(self):
        """A rate-limit error hint must suggest waiting and retrying."""
        hint = _recovery_hint("invoice_list", Exception("rate limit exceeded"))
        assert "wait" in hint.lower() or "retry" in hint.lower()

    def test_recovery_hint_default_fallback(self):
        """Unknown errors must return the default kledo-mcp --test hint."""
        hint = _recovery_hint("analytics_summary", Exception("some unknown error XYZ"))
        assert "kledo-mcp" in hint


class TestLifespanTeardownErrorPath:
    """Covers the aclose() exception path in lifespan teardown."""

    @pytest.mark.asyncio
    async def test_lifespan_teardown_handles_aclose_error_gracefully(self):
        """Lifespan teardown must not propagate exceptions raised by _http_client.aclose()."""
        mock_http = AsyncMock()
        mock_http.aclose.side_effect = RuntimeError("connection already closed")
        mock_client = Mock()
        mock_client._http_client = mock_http
        with patch("src.server._build_client", AsyncMock(return_value=mock_client)):
            # Should not raise even though aclose() raises
            async with lifespan(mcp) as ctx:
                assert isinstance(ctx, AppContext)
        # If we get here, teardown error was handled gracefully
