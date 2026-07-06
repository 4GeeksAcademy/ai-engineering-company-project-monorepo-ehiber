from __future__ import annotations

import os
import sys
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from telemetry_kpi_daily.config import load_config  # noqa: E402
from telemetry_kpi_daily.flows import telemetry_kpi_daily_flow  # noqa: E402


def main() -> None:
    config = load_config()
    cron = os.getenv("PIPELINE_CRON", config.schedule_cron)
    telemetry_kpi_daily_flow.serve(
        name="telemetry-kpi-daily-scheduled",
        cron=cron,
        parameters={"triggered_by": "scheduler", "force": False},
    )


if __name__ == "__main__":
    main()
