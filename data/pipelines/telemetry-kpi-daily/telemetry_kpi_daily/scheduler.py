from __future__ import annotations

import os
import sys
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

# Deprecated: use docker-entrypoint.sh worker. Kept for local dev fallback.
from telemetry_kpi_daily.flows import telemetry_kpi_daily_flow  # noqa: E402


def main() -> None:
  pool = os.getenv("PREFECT_WORK_POOL", "trackflow-docker-pool")
  print(
      "scheduler.py is deprecated. Start the worker with:\n"
      f"  prefect worker start --pool {pool} --type process\n"
      "Then deploy with:\n"
      "  prefect deploy --all --prefect-file data/pipelines/prefect.yaml"
  )
  telemetry_kpi_daily_flow(triggered_by="scheduler", force=False)


if __name__ == "__main__":
    main()
