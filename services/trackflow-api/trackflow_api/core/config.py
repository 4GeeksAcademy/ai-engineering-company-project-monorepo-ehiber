from functools import lru_cache
import os
from pathlib import Path


def find_repo_root() -> Path:
    resolved_path = Path(__file__).resolve()
    for parent in resolved_path.parents:
        if (parent / "package.json").exists() and (parent / "services" / "trackflow-api").exists():
            return parent

    workspace = Path("/workspace")
    if (workspace / "package.json").exists() and (workspace / "services" / "trackflow-api").exists():
        return workspace

    if len(resolved_path.parents) > 4:
        return resolved_path.parents[4]
    if len(resolved_path.parents) > 3:
        return resolved_path.parents[3]
    return resolved_path.parents[-1]


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
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.celery_broker_url = os.getenv("CELERY_BROKER_URL", self.redis_url)
        self.celery_result_backend = os.getenv("CELERY_RESULT_BACKEND", self.redis_url)
        self.celery_task_default_queue = os.getenv("CELERY_TASK_DEFAULT_QUEUE", "default")
        self.celery_task_max_retries = int(os.getenv("CELERY_TASK_MAX_RETRIES", "2"))
        self.celery_task_soft_time_limit_seconds = int(
            os.getenv("CELERY_TASK_SOFT_TIME_LIMIT_SECONDS", "300")
        )
        self.celery_task_time_limit_seconds = int(
            os.getenv("CELERY_TASK_TIME_LIMIT_SECONDS", "360")
        )
        self.celery_task_always_eager = os.getenv("CELERY_TASK_ALWAYS_EAGER", "").strip() in {
            "1",
            "true",
            "True",
        }
        self.flower_port = int(os.getenv("FLOWER_PORT", "5555"))
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "trackflow_knowledge")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        self.litellm_api_key = os.getenv("LITELLM_API_KEY", "")
        self.litellm_api_base = os.getenv("LITELLM_API_BASE", "")
        self.rag_embedding_model = os.getenv(
            "RAG_EMBEDDING_MODEL", "openrouter/perplexity/pplx-embed-v1-0.6b"
        )
        self.rag_llm_model = os.getenv(
            "RAG_LLM_MODEL", "openrouter/deepseek/deepseek-v4-flash"
        )
        self.rag_embedding_dimension = int(os.getenv("RAG_EMBEDDING_DIMENSION", "1024"))
        if not self.litellm_api_base:
            # Default gateway when using OpenRouter model strings
            if self.rag_embedding_model.startswith("openrouter/") or self.rag_llm_model.startswith(
                "openrouter/"
            ):
                self.litellm_api_base = "https://openrouter.ai/api/v1"
        self.rag_top_k = int(os.getenv("RAG_TOP_K", "3"))
        self.rag_knowledge_source_dir = os.getenv("RAG_KNOWLEDGE_SOURCE_DIR", "docs/rag")
        # Wall-clock timeout for live agent MCP tool calls
        self.agent_tool_timeout_seconds = float(
            os.getenv("AGENT_TOOL_TIMEOUT_SECONDS", "5")
        )
        # TrackFlow MCP (Variant B) — agent connects via langchain-mcp-adapters
        self.mcp_server_url = os.getenv(
            "TRACKFLOW_MCP_URL", "http://localhost:8002/mcp"
        )
        self.mcp_auth_token = os.getenv("TRACKFLOW_MCP_TOKEN", "")
        self.mcp_auth_jwt_secret = os.getenv(
            "MCP_AUTH_JWT_SECRET", "trackflow-mcp-dev-secret-change-me"
        )
        self.mcp_auth_issuer = os.getenv("MCP_AUTH_ISSUER", "http://localhost:8002/oidc")
        self.mcp_auth_resource = os.getenv(
            "MCP_AUTH_RESOURCE", "http://localhost:8002/mcp"
        )
        self.rfp_storage_dir = os.getenv("TRACKFLOW_RFP_STORAGE_DIR", "data/rfp/uploads")
        self.rfp_fixtures_dir = os.getenv(
            "TRACKFLOW_RFP_FIXTURES_DIR", "docs/agentic-workflow/fixtures/rfp"
        )

    @property
    def rag_knowledge_source_path(self) -> Path:
        source = Path(self.rag_knowledge_source_dir)
        if source.is_absolute():
            return source
        return REPO_ROOT / source

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
