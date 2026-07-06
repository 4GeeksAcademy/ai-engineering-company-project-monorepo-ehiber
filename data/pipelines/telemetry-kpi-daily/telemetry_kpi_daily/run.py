from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from telemetry_kpi_daily.config import load_config, resolve_processing_dates  # noqa: E402
from telemetry_kpi_daily.flows import telemetry_kpi_daily_flow  # noqa: E402
from telemetry_kpi_daily.pipeline_core import run_pipeline  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TrackFlow telemetry KPI daily pipeline.")
    parser.add_argument("--processing-date", type=date.fromisoformat, default=None)
    parser.add_argument("--start-date", type=date.fromisoformat, default=None)
    parser.add_argument("--end-date", type=date.fromisoformat, default=None)
    parser.add_argument(
        "--triggered-by",
        choices=["manual", "backfill", "scheduler"],
        default="manual",
    )
    parser.add_argument("--force", action="store_true", help="Ignore recent-success skip guard.")
    parser.add_argument(
        "--no-prefect",
        action="store_true",
        help="Run without Prefect orchestration (direct Python path).",
    )
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config()
    dates = resolve_processing_dates(
        processing_date=args.processing_date,
        start_date=args.start_date,
        end_date=args.end_date,
        late_data_days=config.late_data_days,
    )

    if args.no_prefect:
        summary = run_pipeline(
            dates,
            config=config,
            triggered_by=args.triggered_by,
            force=args.force,
        )
    else:
        summary = telemetry_kpi_daily_flow(
            processing_date=args.processing_date,
            start_date=args.start_date,
            end_date=args.end_date,
            triggered_by=args.triggered_by,
            force=args.force,
        )

    if args.pretty:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, ensure_ascii=False))

    return 1 if summary.get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
