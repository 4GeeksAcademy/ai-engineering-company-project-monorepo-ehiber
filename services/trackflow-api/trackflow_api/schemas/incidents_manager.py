from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    category: str
    status: str = "open"
    origin: str
    branch: str


class IncidentPublic(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: str
    updated_at: str


class IncidentListItem(BaseModel):
    """Schema ligero para listados de incidentes."""
    id: int
    title: str
    category: str
    status: str
    created_at: str
    branch: str  # Útil para filtrado


class IncidentStatusUpdate(BaseModel):
    status: str


class IncidentSummary(BaseModel):
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_origin: dict[str, int]
    by_branch: dict[str, int]
    total: int


class FieldValidationErrorDetail(BaseModel):
    field: str
    message: str
