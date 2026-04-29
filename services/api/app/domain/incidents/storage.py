import json
from pathlib import Path

from ...core.errors import ExportUnavailableError


def save_latest_analysis(summary: dict, result_path: str | Path) -> None:
    path = Path(result_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def load_latest_analysis(result_path: str | Path) -> dict:
    path = Path(result_path)
    if not path.exists():
        raise ExportUnavailableError("No analysis has been stored yet.")
    return json.loads(path.read_text(encoding="utf-8"))


def save_export_csv(csv_content: str, export_path: str | Path) -> Path:
    path = Path(export_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(csv_content, encoding="utf-8", newline="")
    return path


def require_export_csv(export_path: str | Path) -> Path:
    path = Path(export_path)
    if not path.exists():
        raise ExportUnavailableError("No CSV export is available yet.")
    return path
