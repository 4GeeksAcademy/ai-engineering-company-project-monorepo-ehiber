import json
from pathlib import Path

from ...core.config import get_settings
from ...core.errors import AnalysisInputError


def load_manager_context(config_path: str | Path | None = None) -> dict:
    path = Path(config_path or get_settings().incidents_manager_context_path)
    if not path.exists():
        raise AnalysisInputError(f"Incident manager context file not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AnalysisInputError(f"Invalid incident manager context JSON: {path}") from exc
