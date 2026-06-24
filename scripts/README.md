# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._

## Current scripts

- `analyze.py`: analyzes incidents CSV files using the shared TrackFlow backend engine
- `seed_performance_data.py`: bulk seed for local caching/performance benchmarks
- `benchmark_api.py`: measures p50/p95 latency on read-heavy API endpoints

## Example

```bash
python scripts/analyze.py scripts/incidents-trackflow.csv
```

The sample CSV and validation rules come from `ai-engineering-syllabus/content/contexts/incidents-file-analysis/CONTEXT-trackflow.md`.
