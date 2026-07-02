# Pipeline `telemetry-kpi-daily`

Batch pipeline that extracts telemetry events from `telemetry_events`, computes the three Phase 1 KPIs, and loads aggregated rows into `telemetry_kpi_daily`.

**Design:** see [`../PIPELINE_DESIGN.md`](../PIPELINE_DESIGN.md)  
**Transform logic:** [`services/telemetry/analysis.py`](../../../services/telemetry/analysis.py)  
**Event contract:** [`docs/telemetry/event-schemas.json`](../../../docs/telemetry/event-schemas.json)

---

## Purpose

| KPI | Metric name |
| --- | --- |
| Order fulfillment rate | `order_fulfillment_rate` |
| Stock discrepancy frequency | `stock_discrepancy_frequency` |
| Receiving–dispatch cycle time | `receiving_dispatch_cycle_time` |

All aggregates are segmented by `warehouse` (`los_angeles`, `zaragoza`).

---

## Stages (planned)

| Stage | Module | Responsibility |
| --- | --- | --- |
| Extract | `stages/extract.py` | Read raw events for `processing_date` using watermark |
| Validate | `stages/validate.py` | Enforce `event-schemas.json` whitelist |
| Transform | `services/telemetry/analysis.py` | `build_metrics()` — shared, not duplicated |
| Load | `stages/load.py` | Upsert into `telemetry_kpi_daily`; update `pipeline_runs` |

---

## Configuration (`config.yaml` — planned)

- `late_data_days`: 3 (reprocess rolling window)
- `pipeline_name`: `telemetry-kpi-daily`
- `schema_version`: `1.0`
- `kpi_event_types`: see design doc §8

---

## How to run (after implementation)

```bash
# Single business day
python -m data.pipelines.telemetry_kpi_daily.run --processing-date 2026-06-28

# Backfill range
python -m data.pipelines.telemetry_kpi_daily.run \
  --start-date 2026-06-01 \
  --end-date 2026-06-07 \
  --triggered-by backfill
```

Until stages are implemented, use the interim CLI:

```bash
python scripts/telemetry_report.py --start-date 2026-06-01 --end-date 2026-06-07 --pretty
```

---

## Scheduling

Not defined in this phase. Orchestration (cron, Prefect, etc.) will be chosen after pipeline architecture and execution are complete. See [`../PIPELINE_DESIGN.md`](../PIPELINE_DESIGN.md) §11.

---

## Verification

1. Run pipeline twice for the same `processing_date` — mart rows must be identical.
2. Compare mart output to `scripts/telemetry_report.py` for the same window.
3. Inspect `pipeline_runs` for counts, watermark, and status.
