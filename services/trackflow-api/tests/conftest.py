import pytest

from trackflow_api.core.config import get_settings
from trackflow_api.core.database import init_db


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("TRACKFLOW_JWT_SECRET_KEY", "test-secret-key-for-pytest")
    monkeypatch.setenv("TRACKFLOW_DATABASE_PATH", str(tmp_path / "app.json"))
    monkeypatch.setenv("TRACKFLOW_DEV_EMAIL_OUTPUT_DIR", str(tmp_path / "dev-emails"))
    get_settings.cache_clear()
    init_db()
    yield
    get_settings.cache_clear()
