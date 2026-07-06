FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/data/pipelines/telemetry-kpi-daily:/app/services/trackflow-api:/app/services

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY data/pipelines/telemetry-kpi-daily/requirements.txt /tmp/pipeline-requirements.txt
COPY services/trackflow-api/requirements.txt /tmp/api-requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /tmp/pipeline-requirements.txt \
    && pip install -r /tmp/api-requirements.txt

COPY data/pipelines/telemetry-kpi-daily /app/data/pipelines/telemetry-kpi-daily
COPY data/pipelines/pipeline.py /app/data/pipelines/pipeline.py
COPY data/pipelines/prefect.yaml /app/data/pipelines/prefect.yaml
COPY services/trackflow-api/trackflow_api /app/services/trackflow-api/trackflow_api
COPY services/telemetry /app/services/telemetry
COPY docs/telemetry/event-schemas.json /app/docs/telemetry/event-schemas.json

WORKDIR /app/data/pipelines/telemetry-kpi-daily

CMD ["python", "-m", "telemetry_kpi_daily.scheduler"]
