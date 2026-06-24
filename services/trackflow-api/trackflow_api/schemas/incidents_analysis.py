from datetime import datetime
from pydantic import BaseModel, ConfigDict


class InvalidRecordPublic(BaseModel):
    """Schema seguro para registros inválidos, excluyendo raw_record sensible."""
    row_number: int
    reasons: list[str]
    # raw_record OMITIDO intencionalmente por seguridad
    # Contiene datos sensibles de incidentes que no deben exponerse


class SatisfactionSummaryPublic(BaseModel):
    """Resumen de satisfacción de incidentes cerrados."""
    closed_cases_with_score: int
    average_score: float | None
    score_distribution: dict[str, int]


class AnalysisResultPublic(BaseModel):
    """Resultado seguro de análisis de incidentes para consumo público."""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    file_name: str
    processed_at: datetime
    totals: dict[str, int]
    category_breakdown: dict[str, int]
    status_breakdown: dict[str, int]
    country_breakdown: dict[str, int]
    invalid_breakdown: dict[str, int]
    invalid_details: list[InvalidRecordPublic]  # Versión segura sin raw_record
    satisfaction: SatisfactionSummaryPublic