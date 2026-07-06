# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._

## Current scripts

- `analyze.py`: analyzes incidents CSV files using the shared TrackFlow backend engine
- `nightly_telemetry.py`: nightly export of telemetry to `data/raw/` + KPI pipeline trigger (DEV-53)
- `seed_performance_data.py`: bulk seed for local caching/performance benchmarks
- `benchmark_api.py`: measures p50/p95 latency on read-heavy API endpoints

### Nightly telemetry (DEV-53)

Runs as an **independent process** (not inside FastAPI). Orchestrates CSV export and the KPI pipeline with a `job_runs` ledger and distributed lock.

```bash
# Default: yesterday UTC
python scripts/nightly_telemetry.py

# Backfill / rubric override
TARGET_DATE=2026-06-30 python scripts/nightly_telemetry.py
```

CSV output: `data/raw/telemetry_YYYY-MM-DD.csv`

Scheduled via `scripts/crontab` (`0 2 * * *` UTC) in the `nightly-telemetry` Docker Compose service.

## Example

```bash
python scripts/analyze.py scripts/incidents-trackflow.csv
```

The sample CSV and validation rules come from `ai-engineering-syllabus/content/contexts/incidents-file-analysis/CONTEXT-trackflow.md`.
