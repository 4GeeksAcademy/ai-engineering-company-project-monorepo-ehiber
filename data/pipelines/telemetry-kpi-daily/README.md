# Pipeline `telemetry-kpi-daily`

Batch pipeline that extracts telemetry events from `telemetry_events`, computes the three Phase 1 KPIs, and loads aggregated rows into `telemetry_kpi_daily`.

**Design:** [`../PIPELINE_DESIGN.md`](../PIPELINE_DESIGN.md)  
**Entrypoint:** [`../pipeline.py`](../pipeline.py)  
**Transform logic:** [`services/telemetry/analysis.py`](../../../services/telemetry/analysis.py)

---

## Requirements

Copy [`.env.example`](../../../.env.example) and set:

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URI` | Same database as `trackflow-api` |
| `PREFECT_API_URL` | Prefect Cloud workspace API URL |
| `PREFECT_API_KEY` | Prefect Cloud API key |
| `PREFECT_WORK_POOL` | Work pool name (default: `trackflow-docker-pool`) |

---

## Architecture (Part 3 — subflows)

```
telemetry_kpi_daily_flow
  └── process_date_flow (per processing_date)
        ├── extract_subflow   → extract_telemetry_events
        ├── validate_subflow  → validate_telemetry_events (allow_failure)
        ├── transform_subflow → transform_kpi_metrics (cached 1h)
        └── load_subflow      → load_kpi_mart
```

`--no-prefect` uses the same stage functions via `run_*_phase()` in [`subflows.py`](telemetry_kpi_daily/subflows.py).

---

## Run locally (no Prefect Cloud)

```bash
cd data/pipelines/telemetry-kpi-daily
pip install -r requirements.txt
pip install -r ../../../services/trackflow-api/requirements.txt

export SUPABASE_URI="sqlite:///./local.db"
export PYTHONPATH="$PWD:../../../services/trackflow-api:../../../services:.."

python -m telemetry_kpi_daily.run --processing-date 2026-06-30 --no-prefect --pretty
```

---

## Prefect Cloud + Docker

### One-time setup

```bash
# Authenticate CLI with Prefect Cloud
prefect cloud login

# Create work pool (process type — runs inside worker container)
prefect work-pool create --type process trackflow-docker-pool

# Register deployments from prefect.yaml
prefect deploy --all --prefect-file data/pipelines/prefect.yaml
```

### Start worker (Docker)

```bash
docker compose up telemetry-pipeline
```

The container runs `prefect worker start --pool trackflow-docker-pool`.

### Trigger manual run (visible in Prefect Cloud UI)

```bash
prefect deployment run 'telemetry-kpi-daily-flow/telemetry-kpi-daily-manual'
```

Scheduled runs use cron `0 2 * * *` UTC (defined in [`prefect.yaml`](../prefect.yaml)).

---

## Tests (no Prefect Cloud required)

```bash
cd data/pipelines/telemetry-kpi-daily
PYTHONPATH="$PWD:../../../services/trackflow-api:../../../services:.." pytest tests/ -q
```

| Suite | Covers |
| --- | --- |
| `test_transform.py` | KPI 1/2/3 via `transform_metrics` + `analysis.py` |
| `test_subflows.py` | Phase runners + `allow_failure` coalesce |
| `test_pipeline.py` | Idempotency, skip guard, partial failure |

---

## API ops

| Endpoint | Description |
| --- | --- |
| `GET /telemetry/pipeline/runs/latest` | Last run metadata |
| `POST /telemetry/pipeline/run` | Trigger flow from API |

---

## Prefect mapping

| Flow | Role |
| --- | --- |
| `telemetry-kpi-daily-flow` | Main coordinator (date batch) |
| `telemetry-kpi-daily-date-flow` | Per-date orchestrator + ledger |
| `extract-subflow` | Extract phase |
| `validate-subflow` | Validate phase (optional) |
| `transform-subflow` | Transform phase |
| `load-subflow` | Load phase |
| `telemetry-stream-alerts-flow` | Placeholder (phase 2) |
