import pytest

from trackflow_api.core.cache import cache_clear
from trackflow_api.core.celery_app import configure_celery
from trackflow_api.core.config import get_settings
from trackflow_api.core.database import get_inventory_engine, init_db


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path):
    cache_clear()
    monkeypatch.setenv("TRACKFLOW_JWT_SECRET_KEY", "test-secret-key-for-pytest")
    monkeypatch.setenv("TRACKFLOW_DATABASE_PATH", str(tmp_path / "app.json"))
    monkeypatch.setenv("SUPABASE_URI", f"sqlite:///{tmp_path / 'inventory.db'}")
    monkeypatch.setenv("TRACKFLOW_DEV_EMAIL_OUTPUT_DIR", str(tmp_path / "dev-emails"))
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "1")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("REDIS_URL", "memory://")
    get_settings.cache_clear()
    configure_celery()
    get_inventory_engine.cache_clear()
    init_db()
    yield
    cache_clear()
    get_inventory_engine.cache_clear()
    get_settings.cache_clear()
    configure_celery()
