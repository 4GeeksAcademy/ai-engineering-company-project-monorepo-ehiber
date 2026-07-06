#!/usr/bin/env python3
"""Nightly telemetry job — independent CLI entrypoint (DEV-53)."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKFLOW_API_ROOT = REPO_ROOT / "services" / "trackflow-api"
SERVICES_ROOT = REPO_ROOT / "services"
PIPELINE_PKG = REPO_ROOT / "data" / "pipelines" / "telemetry-kpi-daily"
PIPELINES_DIR = REPO_ROOT / "data" / "pipelines"

for path in (TRACKFLOW_API_ROOT, SERVICES_ROOT, PIPELINE_PKG, PIPELINES_DIR, REPO_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from trackflow_api.services.nightly_telemetry_service import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
