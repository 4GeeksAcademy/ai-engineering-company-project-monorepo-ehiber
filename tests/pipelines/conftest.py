"""Shared pytest fixtures for tests/pipelines (rubric entrypoint)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlmodel import SQLModel, create_engine

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_ROOT = REPO_ROOT / "data" / "pipelines" / "telemetry-kpi-daily"
SERVICES_API = REPO_ROOT / "services" / "trackflow-api"
SERVICES = REPO_ROOT / "services"
PIPELINES_DIR = REPO_ROOT / "data" / "pipelines"

for path in (
    str(PIPELINE_ROOT),
    str(PIPELINES_DIR),
    str(SERVICES_API),
    str(SERVICES),
):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture()
def pipeline_env(tmp_path, monkeypatch):
    db_path = tmp_path / "pipeline.db"
    uri = f"sqlite:///{db_path}"
    monkeypatch.setenv("SUPABASE_URI", uri)

    from trackflow_api.core import config as config_module
    from trackflow_api.core import database as database_module
    from trackflow_api import models  # noqa: F401

    config_module.get_settings.cache_clear()
    database_module.get_inventory_engine.cache_clear()

    engine = create_engine(uri, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine
