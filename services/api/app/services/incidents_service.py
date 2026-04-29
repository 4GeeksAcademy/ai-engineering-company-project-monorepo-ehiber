from pathlib import Path

from ..core.config import get_settings
from ..domain.incidents.analyzer import analyze_csv_bytes, analyze_csv_file
from ..domain.incidents.config import load_incidents_context
from ..domain.incidents.exporters import summary_to_csv
from ..domain.incidents.storage import (
    load_latest_analysis,
    require_export_csv,
    save_export_csv,
    save_latest_analysis,
)


def analyze_uploaded_incidents(file_name: str, payload: bytes) -> dict:
    settings = get_settings()
    config = load_incidents_context(settings.incidents_context_path)
    summary = analyze_csv_bytes(file_name, payload, config).to_dict()
    _persist_summary(summary)
    return summary


def analyze_incidents_file(file_path: str | Path) -> dict:
    settings = get_settings()
    config = load_incidents_context(settings.incidents_context_path)
    summary = analyze_csv_file(file_path, config).to_dict()
    _persist_summary(summary)
    return summary


def get_latest_analysis() -> dict:
    settings = get_settings()
    return load_latest_analysis(settings.incidents_last_result_path)


def export_last_analysis_csv() -> Path:
    settings = get_settings()
    return require_export_csv(settings.incidents_last_export_path)


def export_summary_csv(summary: dict, destination: str | Path) -> Path:
    return save_export_csv(summary_to_csv(summary), destination)


def _persist_summary(summary: dict) -> None:
    settings = get_settings()
    save_latest_analysis(summary, settings.incidents_last_result_path)
    save_export_csv(summary_to_csv(summary), settings.incidents_last_export_path)
