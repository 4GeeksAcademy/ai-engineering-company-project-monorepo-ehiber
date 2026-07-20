"""MCP Auth (https://mcp-auth.dev/) integration — JWT bearer via mcpauth 0.1.x."""

from __future__ import annotations

import os
import time
from typing import Any

import jwt
from mcpauth import MCPAuth
from mcpauth.config import AuthServerType, AuthorizationServerMetadata, AuthServerConfig
from mcpauth.exceptions import (
    BearerAuthExceptionCode,
    MCPAuthBearerAuthException,
    MCPAuthTokenVerificationException,
    MCPAuthTokenVerificationExceptionCode,
)
from mcpauth.types import AuthInfo
from mcpauth.utils import fetch_server_config

from .scopes import SCOPES_SUPPORTED

DEFAULT_RESOURCE = "http://localhost:8002/mcp"
DEFAULT_ISSUER = "http://localhost:8002/oidc"
DEFAULT_JWT_SECRET = "trackflow-mcp-dev-secret-change-me"


def resource_identifier() -> str:
    return os.getenv("MCP_AUTH_RESOURCE", DEFAULT_RESOURCE).rstrip("/")


def auth_issuer() -> str:
    return os.getenv("MCP_AUTH_ISSUER", DEFAULT_ISSUER).rstrip("/")


def jwt_secret() -> str:
    return os.getenv("MCP_AUTH_JWT_SECRET", DEFAULT_JWT_SECRET)


def auth_mode() -> str:
    """local = HS256 shared secret | oidc = fetch provider metadata + JWKS JWT mode."""
    return os.getenv("MCP_AUTH_MODE", "local").strip().lower()


def _local_auth_server() -> AuthServerConfig:
    issuer = auth_issuer()
    return AuthServerConfig(
        type=AuthServerType.OIDC,
        metadata=AuthorizationServerMetadata(
            issuer=issuer,
            authorization_endpoint=f"{issuer}/auth",
            token_endpoint=f"{issuer}/token",
            jwks_uri=f"{issuer}/jwks",
            response_types_supported=["code"],
            code_challenge_methods_supported=["S256"],
            scope_supported=list(SCOPES_SUPPORTED),
        ),
    )


def build_mcp_auth() -> MCPAuth:
    """Configure MCP Auth against an authorization server (mcpauth 0.1.x API)."""
    mode = auth_mode()
    if mode == "oidc":
        issuer = os.environ["MCP_AUTH_ISSUER"]
        server = fetch_server_config(issuer, AuthServerType.OIDC)
    else:
        server = _local_auth_server()
    return MCPAuth(server=server)


def verify_local_jwt(token: str) -> AuthInfo:
    """HS256 JWT verifier for local/dev (no external OIDC required)."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            jwt_secret(),
            algorithms=["HS256"],
            audience=resource_identifier(),
            issuer=auth_issuer(),
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError as exc:
        raise MCPAuthTokenVerificationException(
            MCPAuthTokenVerificationExceptionCode.INVALID_TOKEN,
            cause=exc,
        ) from exc

    raw_scope = payload.get("scope") or payload.get("scopes") or ""
    if isinstance(raw_scope, list):
        scopes = [str(s) for s in raw_scope]
    else:
        scopes = [s for s in str(raw_scope).split() if s]

    return AuthInfo(
        token=token,
        issuer=str(payload.get("iss") or auth_issuer()),
        subject=str(payload.get("sub")),
        client_id=payload.get("client_id") or payload.get("azp"),
        scopes=scopes,
        audience=payload.get("aud"),
        claims=payload,
    )


def bearer_verify_callable():
    """Return the verify function or ``\"jwt\"`` mode for MCP Auth middleware."""
    if auth_mode() == "oidc":
        return "jwt"
    return verify_local_jwt


def require_scopes(mcp_auth: MCPAuth, *required: str) -> AuthInfo:
    """Enforce scopes inside a tool handler (403 insufficient_scope)."""
    auth_info = mcp_auth.auth_info
    if auth_info is None:
        raise MCPAuthBearerAuthException(BearerAuthExceptionCode.MISSING_BEARER_TOKEN)
    missing = [scope for scope in required if scope not in (auth_info.scopes or [])]
    if missing:
        raise MCPAuthBearerAuthException(BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES)
    return auth_info


def mint_local_access_token(
    *,
    subject: str = "trackflow-agent",
    scopes: list[str] | None = None,
    expires_in_seconds: int = 3600,
    client_id: str = "trackflow-mcp-client",
) -> str:
    """Mint a local HS256 access token (dev / agent / tests)."""
    now = int(time.time())
    scope_list = scopes if scopes is not None else list(SCOPES_SUPPORTED)
    payload = {
        "sub": subject,
        "iss": auth_issuer(),
        "aud": resource_identifier(),
        "iat": now,
        "exp": now + expires_in_seconds,
        "client_id": client_id,
        "scope": " ".join(scope_list),
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def protected_resource_metadata() -> dict[str, Any]:
    """RFC 9728-style protected resource metadata (scopes for MCP clients)."""
    return {
        "resource": resource_identifier(),
        "authorization_servers": [auth_issuer()],
        "scopes_supported": list(SCOPES_SUPPORTED),
        "bearer_methods_supported": ["header"],
    }
