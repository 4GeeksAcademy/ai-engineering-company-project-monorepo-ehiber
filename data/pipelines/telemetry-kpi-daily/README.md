# Pipeline `telemetry-kpi-daily`

Batch pipeline that extracts telemetry events from `telemetry_events`, computes the three Phase 1 KPIs, and loads aggregated rows into `telemetry_kpi_daily`.

**Design:** [`../PIPELINE_DESIGN.md`](../PIPELINE_DESIGN.md)  
**Transform logic:** [`services/telemetry/analysis.py`](../../../services/telemetry/analysis.py)

---

## Requirements

- `SUPABASE_URI` — same database as `trackflow-api`
- Python 3.11+

---

## Run locally

```bash
cd data/pipelines/telemetry-kpi-daily
pip install -r requirements.txt
pip install -r ../../../services/trackflow-api/requirements.txt

export SUPABASE_URI="postgresql://..."
export PYTHONPATH="$PWD:../../../services/trackflow-api:../../../services"

# Prefect orchestration (default)
python -m telemetry_kpi_daily.run --processing-date 2026-06-30 --pretty

# Direct Python path (no Prefect)
python -m telemetry_kpi_daily.run --processing-date 2026-06-30 --no-prefect --pretty

# Backfill
python -m telemetry_kpi_daily.run --start-date 2026-06-01 --end-date 2026-06-07 --triggered-by backfill --pretty
```

---

## Docker schedule

```bash
docker compose up telemetry-pipeline
```

Default schedule: `0 2 * * *` (02:00 UTC daily). Override with `PIPELINE_CRON`.

---

## Resilience features

| Requirement | Implementation |
| --- | --- |
| Partial failures | Main flow processes each `processing_date` independently; one failed day does not stop others |
| Retries on external DB | Prefect tasks `extract_telemetry_events` and `load_kpi_mart` — 3 retries (justified in `flows.py`), 30s delay |
| Prefect deployment | `data/pipelines/prefect.yaml` — `prefect deploy --prefect-file data/pipelines/prefect.yaml --all` |
| Entrypoint | `data/pipelines/pipeline.py:telemetry_kpi_daily_flow` |
| API ops | `GET /telemetry/pipeline/runs/latest`, `POST /telemetry/pipeline/run` |
| Docker + schedule | `Dockerfile` + `docker-compose.yml` service `telemetry-pipeline` with Prefect `serve(cron=...)` |
| Skip recent success | Skips if `pipeline_runs` has `status=succeeded` for same date within last hour |

---

## Tests

```bash
cd data/pipelines/telemetry-kpi-daily
pytest tests/ -q
```

---

## Prefect mapping

| Flow | Tasks |
| --- | --- |
| `telemetry-kpi-daily-flow` | orchestrates date batch |
| `telemetry-kpi-daily-date-flow` | `extract_telemetry_events` → `validate_telemetry_events` → `transform_kpi_metrics` → `load_kpi_mart` |
| `telemetry-stream-alerts-flow` | placeholder (phase 2) |
