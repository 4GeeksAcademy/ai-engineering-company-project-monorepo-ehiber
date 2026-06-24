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
from ..schemas.incidents_analysis import AnalysisResultPublic


def analyze_uploaded_incidents(file_name: str, payload: bytes) -> AnalysisResultPublic:
    settings = get_settings()
    config = load_incidents_context(settings.incidents_context_path)
    summary_dict = analyze_csv_bytes(file_name, payload, config).to_dict()
    
    # Filtrar raw_record sensible antes de serializar
    for invalid_detail in summary_dict.get("invalid_details", []):
        invalid_detail.pop("raw_record", None)
    
    _persist_summary(summary_dict)
    return AnalysisResultPublic.model_validate(summary_dict)


def analyze_incidents_file(file_path: str | Path) -> AnalysisResultPublic:
    settings = get_settings()
    config = load_incidents_context(settings.incidents_context_path)
    summary_dict = analyze_csv_file(file_path, config).to_dict()
    
    # Filtrar raw_record sensible antes de serializar
    for invalid_detail in summary_dict.get("invalid_details", []):
        invalid_detail.pop("raw_record", None)
    
    _persist_summary(summary_dict)
    return AnalysisResultPublic.model_validate(summary_dict)


def get_latest_analysis() -> AnalysisResultPublic:
    settings = get_settings()
    summary_dict = load_latest_analysis(settings.incidents_last_result_path)
    
    # Aplicar mismo filtro de seguridad
    for invalid_detail in summary_dict.get("invalid_details", []):
        invalid_detail.pop("raw_record", None)
    
    return AnalysisResultPublic.model_validate(summary_dict)


def export_last_analysis_csv() -> Path:
    settings = get_settings()
    return require_export_csv(settings.incidents_last_export_path)


def export_summary_csv(summary: dict, destination: str | Path) -> Path:
    return save_export_csv(summary_to_csv(summary), destination)


def _persist_summary(summary_dict: dict) -> None:
    """Persiste el resumen de análisis, filtrando datos sensibles."""
    settings = get_settings()
    
    # Crear copia para persistencia que también excluya raw_record
    persist_dict = summary_dict.copy()
    for invalid_detail in persist_dict.get("invalid_details", []):
        invalid_detail.pop("raw_record", None)
    
    save_latest_analysis(persist_dict, settings.incidents_last_result_path)
    save_export_csv(summary_to_csv(persist_dict), settings.incidents_last_export_path)
