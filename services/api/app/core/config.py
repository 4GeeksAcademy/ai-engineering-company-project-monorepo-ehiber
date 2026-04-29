from functools import lru_cache
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("TRACKFLOW_APP_ENV", "development")
        self.api_host = os.getenv("TRACKFLOW_API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("TRACKFLOW_API_PORT", "8000"))
        self.allowed_origins_raw = os.getenv(
            "TRACKFLOW_ALLOWED_ORIGINS",
            "http://localhost:5173",
        )
        self.database_path = os.getenv(
            "TRACKFLOW_DATABASE_PATH",
            str(REPO_ROOT / "data" / "app.db"),
        )
        self.jwt_secret_key = os.getenv("TRACKFLOW_JWT_SECRET_KEY", "")
        self.jwt_algorithm = os.getenv("TRACKFLOW_JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("TRACKFLOW_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.incidents_context_path = os.getenv(
            "TRACKFLOW_INCIDENTS_CONTEXT_PATH",
            str(REPO_ROOT / "data" / "incidents" / "context.json"),
        )
        self.incidents_last_result_path = os.getenv(
            "TRACKFLOW_INCIDENTS_LAST_RESULT_PATH",
            str(REPO_ROOT / "data" / "incidents" / "last_result.json"),
        )
        self.incidents_last_export_path = os.getenv(
            "TRACKFLOW_INCIDENTS_LAST_EXPORT_PATH",
            str(REPO_ROOT / "data" / "incidents" / "results.csv"),
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
