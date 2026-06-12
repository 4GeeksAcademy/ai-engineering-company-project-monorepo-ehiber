from functools import lru_cache
import os
from pathlib import Path


def find_repo_root() -> Path:
    resolved_path = Path(__file__).resolve()
    for parent in resolved_path.parents:
        if (parent / "package.json").exists() and (parent / "services" / "trackflow-api").exists():
            return parent

    return resolved_path.parents[4] if len(resolved_path.parents) > 4 else resolved_path.parents[3]


REPO_ROOT = find_repo_root()
DOTENV_CANDIDATES = (
    REPO_ROOT / ".env",
    REPO_ROOT / "services" / "trackflow-api" / ".env",
)


def load_dotenv_file() -> None:
    for dotenv_path in DOTENV_CANDIDATES:
        if not dotenv_path.exists():
            continue

        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
        break


load_dotenv_file()


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("TRACKFLOW_APP_ENV", "development")
        self.api_host = os.getenv("TRACKFLOW_API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("TRACKFLOW_API_PORT", "8000"))
        self.allowed_origins_raw = os.getenv(
            "TRACKFLOW_ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://localhost:3001",
        )
        self.database_path = os.getenv(
            "TRACKFLOW_DATABASE_PATH",
            str(REPO_ROOT / "data" / "app.json"),
        )
        self.supabase_uri = os.getenv("SUPABASE_URI", "")
        self.jwt_secret_key = os.getenv("TRACKFLOW_JWT_SECRET_KEY", "")
        self.jwt_algorithm = os.getenv("TRACKFLOW_JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("TRACKFLOW_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.incidents_context_path = os.getenv(
            "TRACKFLOW_INCIDENTS_CONTEXT_PATH",
            str(REPO_ROOT / "data" / "incidents" / "context.json"),
        )
        self.incidents_manager_context_path = os.getenv(
            "TRACKFLOW_INCIDENTS_MANAGER_CONTEXT_PATH",
            str(REPO_ROOT / "data" / "incidents" / "manager-context.json"),
        )
        self.incidents_last_result_path = os.getenv(
            "TRACKFLOW_INCIDENTS_LAST_RESULT_PATH",
            str(REPO_ROOT / "data" / "incidents" / "last_result.json"),
        )
        self.incidents_last_export_path = os.getenv(
            "TRACKFLOW_INCIDENTS_LAST_EXPORT_PATH",
            str(REPO_ROOT / "data" / "incidents" / "results.csv"),
        )
        self.password_reset_expire_minutes = int(
            os.getenv("TRACKFLOW_PASSWORD_RESET_EXPIRE_MINUTES", "30")
        )
        self.password_reset_app_url = os.getenv(
            "TRACKFLOW_PASSWORD_RESET_APP_URL",
            "http://localhost:3000",
        ).rstrip("/")
        self.password_reset_from_email = os.getenv(
            "TRACKFLOW_PASSWORD_RESET_FROM_EMAIL",
            "TrackFlow <onboarding@resend.dev>",
        )
        self.resend_api_key = os.getenv("TRACKFLOW_RESEND_API_KEY", "")
        self.dev_email_output_dir = os.getenv(
            "TRACKFLOW_DEV_EMAIL_OUTPUT_DIR",
            str(REPO_ROOT / "data" / "dev-emails"),
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
