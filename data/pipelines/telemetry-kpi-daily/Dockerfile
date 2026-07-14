FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/data/pipelines/telemetry-kpi-daily:/app/data/pipelines:/app/services/trackflow-api:/app/services

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# API deps via uv lockfile (no pip)
COPY services/trackflow-api/pyproject.toml /tmp/api/pyproject.toml
COPY services/trackflow-api/uv.lock /tmp/api/uv.lock
COPY services/trackflow-api/trackflow_api /tmp/api/trackflow_api
COPY services/trackflow-api/main.py /tmp/api/main.py
COPY services/trackflow-api/seed.py /tmp/api/seed.py
WORKDIR /tmp/api
RUN uv sync --frozen --no-dev

# Pipeline-only deps into the same venv
COPY data/pipelines/telemetry-kpi-daily/requirements.txt /tmp/pipeline-requirements.txt
RUN uv pip install --python /opt/venv/bin/python -r /tmp/pipeline-requirements.txt

WORKDIR /app
COPY data/pipelines/telemetry-kpi-daily /app/data/pipelines/telemetry-kpi-daily
COPY data/pipelines/pipeline.py /app/data/pipelines/pipeline.py
COPY data/pipelines/prefect.yaml /app/data/pipelines/prefect.yaml
COPY services/trackflow-api/trackflow_api /app/services/trackflow-api/trackflow_api
COPY services/telemetry /app/services/telemetry
COPY docs/telemetry/event-schemas.json /app/docs/telemetry/event-schemas.json

RUN chmod +x /app/data/pipelines/telemetry-kpi-daily/docker-entrypoint.sh

ENTRYPOINT ["/app/data/pipelines/telemetry-kpi-daily/docker-entrypoint.sh"]
