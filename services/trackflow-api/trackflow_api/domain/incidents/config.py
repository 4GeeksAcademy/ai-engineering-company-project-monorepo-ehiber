import json
from pathlib import Path

from ...core.errors import AnalysisInputError


def load_incidents_context(config_path: str | Path) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise AnalysisInputError(f"Incidents context file not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AnalysisInputError(f"Invalid incidents context JSON: {path}") from exc

    required_keys = {
        "required_fields",
        "category_field",
        "status_field",
        "satisfaction_field",
        "allowed_categories",
        "allowed_statuses",
        "closed_statuses",
    }
    missing = sorted(required_keys - set(payload))
    if missing:
        raise AnalysisInputError(
            f"Incidents context is missing required keys: {', '.join(missing)}"
        )

    return payload
