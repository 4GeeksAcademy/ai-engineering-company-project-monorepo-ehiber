import pytest

from trackflow_api.core.config import INSECURE_MCP_JWT_SECRET, get_settings


def test_production_rejects_default_mcp_jwt_secret(monkeypatch):
    monkeypatch.setenv("TRACKFLOW_APP_ENV", "production")
    monkeypatch.setenv("MCP_AUTH_JWT_SECRET", INSECURE_MCP_JWT_SECRET)
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="MCP_AUTH_JWT_SECRET"):
        get_settings()
    monkeypatch.setenv("TRACKFLOW_APP_ENV", "development")
    get_settings.cache_clear()


def test_development_allows_placeholder_mcp_jwt_secret(monkeypatch):
    monkeypatch.setenv("TRACKFLOW_APP_ENV", "development")
    monkeypatch.setenv("MCP_AUTH_JWT_SECRET", INSECURE_MCP_JWT_SECRET)
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.mcp_auth_jwt_secret == INSECURE_MCP_JWT_SECRET
