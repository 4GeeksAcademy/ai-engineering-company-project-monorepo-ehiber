# TrackFlow MCP (Variant B) — Streamable HTTP + MCP Auth
FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    MCP_PORT=8002 \
    MCP_HOST=0.0.0.0 \
    PYTHONPATH=/workspace:/workspace/services/trackflow-api:/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY mcps/trackflow-mcp/pyproject.toml /app/pyproject.toml
COPY mcps/trackflow-mcp/trackflow_mcp /app/trackflow_mcp

# Install MCP package deps (no lockfile yet — resolve at build)
RUN uv pip install --system -e /app

EXPOSE 8002
CMD ["uvicorn", "trackflow_mcp.server:app", "--host", "0.0.0.0", "--port", "8002"]
