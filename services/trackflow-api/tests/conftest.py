import pytest

from trackflow_api.core.config import get_settings
from trackflow_api.core.database import get_inventory_engine, init_db


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("TRACKFLOW_JWT_SECRET_KEY", "test-secret-key-for-pytest")
    monkeypatch.setenv("TRACKFLOW_DATABASE_PATH", str(tmp_path / "app.json"))
    monkeypatch.setenv("SUPABASE_URI", f"sqlite:///{tmp_path / 'inventory.db'}")
    monkeypatch.setenv("TRACKFLOW_DEV_EMAIL_OUTPUT_DIR", str(tmp_path / "dev-emails"))
    get_settings.cache_clear()
    get_inventory_engine.cache_clear()
    init_db()
    yield
    get_inventory_engine.cache_clear()
    get_settings.cache_clear()
