"""MCP client bridge via langchain-mcp-adapters (no direct service imports in agent tools)."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import jwt

from ...core.config import get_settings

# Default scopes the knowledge agent needs (read-only; writes stay on HITL routes).
_DEFAULT_SCOPES = ("incidents:read", "inventory:read")


def _mint_token_if_needed() -> str:
    settings = get_settings()
    if settings.mcp_auth_token:
        return settings.mcp_auth_token
    now = int(time.time())
    payload = {
        "sub": "trackflow-knowledge-agent",
        "iss": settings.mcp_auth_issuer,
        "aud": settings.mcp_auth_resource,
        "iat": now,
        "exp": now + 3600,
        "client_id": "trackflow-api-agent",
        "scope": " ".join(_DEFAULT_SCOPES),
    }
    return jwt.encode(payload, settings.mcp_auth_jwt_secret, algorithm="HS256")


def _normalize_tool_payload(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            return {"ok": True, "data": parsed}
        except json.JSONDecodeError:
            return {"ok": True, "message": raw}
    if isinstance(raw, list):
        # LangChain tool content blocks
        texts: list[str] = []
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(str(block.get("text") or ""))
            else:
                texts.append(str(block))
        joined = "\n".join(texts).strip()
        return _normalize_tool_payload(joined)
    return {"ok": True, "data": raw}


async def _ainvoke_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    settings = get_settings()
    token = _mint_token_if_needed()
    client = MultiServerMCPClient(
        {
            "trackflow": {
                "transport": "streamable_http",
                "url": settings.mcp_server_url,
                "headers": {"Authorization": f"Bearer {token}"},
            }
        }
    )
    tools = await client.get_tools()
    tool = next((item for item in tools if item.name == tool_name), None)
    if tool is None:
        available = [item.name for item in tools]
        return {
            "ok": False,
            "error": "service_unavailable",
            "message": f"MCP tool '{tool_name}' not found.",
            "detail": f"available={available}",
        }
    result = await tool.ainvoke(arguments)
    return _normalize_tool_payload(result)


def call_mcp_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Synchronous entry point used by LangGraph tool nodes."""
    args = arguments or {}
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Nested event loop (e.g. already inside async) — run in a fresh thread.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, _ainvoke_mcp_tool(tool_name, args))
            return future.result()
    return asyncio.run(_ainvoke_mcp_tool(tool_name, args))
