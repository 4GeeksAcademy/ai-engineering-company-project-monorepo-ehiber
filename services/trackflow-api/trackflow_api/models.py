from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Text, UniqueConstraint
from sqlmodel import JSON, Column, Field, SQLModel


class SKUCategory(str, Enum):
    FASHION = "fashion"
    ELECTRONICS = "electronics"
    COSMETICS = "cosmetics"


class WarehouseCode(str, Enum):
    LA = "LA"
    ZGZ = "ZGZ"


class ExitType(str, Enum):
    DISPATCH = "dispatch"
    LOSS = "loss"


class SKU(SQLModel, table=True):
    __tablename__ = "skus"
    __table_args__ = (UniqueConstraint("sku", "warehouse", name="uq_sku_warehouse"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(index=True)
    client_name: str
    category: SKUCategory
    warehouse: WarehouseCode = Field(index=True)


class StockEntry(SQLModel, table=True):
    __tablename__ = "stock_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku_id: int = Field(foreign_key="skus.id", index=True)
    quantity: int = Field(gt=0)
    reference: str
    warehouse: WarehouseCode = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    user_uuid: str = Field(index=True)


class StockExit(SQLModel, table=True):
    __tablename__ = "stock_exits"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku_id: int = Field(foreign_key="skus.id", index=True)
    quantity: int = Field(gt=0)
    exit_type: ExitType
    tracking_number: Optional[str] = None
    warehouse: WarehouseCode = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    user_uuid: str = Field(index=True)


class TelemetryEvent(SQLModel, table=True):
    __tablename__ = "telemetry_events"

    event_id: str = Field(primary_key=True, description="Client-provided UUID v4")
    event_type: str = Field(index=True, description="Canonical entity_action name")
    timestamp: datetime = Field(index=True, description="Business fact timestamp (UTC)")
    source: str = Field(description="trackflow-api | backoffice-web")
    tags: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    processing_mode: str = Field(index=True, description="stream | batch")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server-side ingestion timestamp",
    )


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipeline_runs"

    run_id: str = Field(primary_key=True, description="UUID for this pipeline execution")
    pipeline_name: str = Field(index=True)
    processing_date: date = Field(index=True)
    status: str = Field(index=True, description="pending|running|succeeded|failed|partial|skipped")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = Field(default=None)
    events_extracted: int = Field(default=0)
    events_rejected: int = Field(default=0)
    metrics_written: int = Field(default=0)
    watermark_before: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    watermark_after: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    error_summary: str | None = Field(default=None)
    triggered_by: str = Field(default="manual")


class PipelineWatermark(SQLModel, table=True):
    __tablename__ = "pipeline_watermarks"

    pipeline_name: str = Field(primary_key=True)
    last_occurred_at: datetime | None = Field(default=None)
    last_event_id: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by_run_id: str | None = Field(default=None)


class JobRun(SQLModel, table=True):
    __tablename__ = "job_runs"

    run_id: str = Field(primary_key=True, description="UUID for this job execution")
    job_name: str = Field(index=True)
    target_date: date = Field(index=True)
    status: str = Field(
        index=True,
        description="pending|processing|completed|failed",
    )
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    csv_path: str | None = Field(default=None)


class JobLock(SQLModel, table=True):
    __tablename__ = "job_locks"

    job_name: str = Field(primary_key=True)
    is_locked: bool = Field(default=False, index=True)
    locked_at: datetime | None = Field(default=None)
    holder_run_id: str | None = Field(default=None)


class DeadLetterTask(SQLModel, table=True):
    __tablename__ = "dead_letter_tasks"

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, description="Celery task UUID")
    task_name: str = Field(index=True)
    attempt_number: int = Field(ge=1)
    error_message: str
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class TelemetryKpiDaily(SQLModel, table=True):
    __tablename__ = "telemetry_kpi_daily"
    __table_args__ = (
        UniqueConstraint(
            "metric_name",
            "business_date",
            "warehouse",
            "dimensions_key",
            name="uq_telemetry_kpi_daily",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    metric_name: str = Field(index=True)
    business_date: date = Field(index=True)
    warehouse: str = Field(index=True)
    dimensions_key: str = Field(index=True, description="Stable key derived from dimensions JSON")
    dimensions: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    value: float | None = Field(default=None)
    sample_size: int | None = Field(default=None)
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pipeline_run_id: str = Field(index=True)
    schema_version: str = Field(default="1.0")


class AgentMemoryProposal(SQLModel, table=True):
    """Pending memory proposal awaiting explicit user approve/reject/edit."""

    __tablename__ = "agent_memory_proposals"

    proposal_id: str = Field(primary_key=True)
    user_uuid: str = Field(index=True)
    run_id: str = Field(index=True)
    proposed_content: str
    consolidation_key: str = Field(index=True, description="carrier|country|topic")
    carrier: str | None = Field(default=None, index=True)
    country: str | None = Field(default=None, index=True)
    topic: str = Field(index=True)
    status: str = Field(default="pending", index=True, description="pending|approved|rejected|discarded|edited")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    resolved_at: datetime | None = Field(default=None)


class AgentMemoryAudit(SQLModel, table=True):
    """Append-only audit trail for memory proposals and decisions."""

    __tablename__ = "agent_memory_audits"

    id: int | None = Field(default=None, primary_key=True)
    proposal_id: str = Field(index=True)
    user_uuid: str = Field(index=True)
    event_type: str = Field(
        index=True,
        description="proposed|approved|rejected|edited|discarded_unclear|blocked_sensitive",
    )
    proposed_content: str
    decision_content: str | None = Field(default=None)
    consolidation_key: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class AgentMemoryEntry(SQLModel, table=True):
    """Approved durable memories consolidated by carrier + country + topic."""

    __tablename__ = "agent_memory_entries"
    __table_args__ = (
        UniqueConstraint("consolidation_key", "user_uuid", name="uq_memory_key_user"),
    )

    id: int | None = Field(default=None, primary_key=True)
    entry_id: str = Field(index=True)
    user_uuid: str = Field(index=True)
    consolidation_key: str = Field(index=True)
    carrier: str | None = Field(default=None, index=True)
    country: str | None = Field(default=None, index=True)
    topic: str = Field(index=True)
    content: str
    authorized_by: str = Field(index=True, description="user_uuid who approved")
    proposal_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    expires_at: datetime = Field(index=True)


class RfpTicket(SQLModel, table=True):
    """RFP intake ticket with lifecycle status for Sales routing."""

    __tablename__ = "rfp_tickets"

    ticket_id: str = Field(primary_key=True)
    rfp_id: str = Field(index=True)
    status: str = Field(
        default="analizando",
        index=True,
        description=(
            "analizando|esperando_aprobación|generando_borrador|"
            "en_evaluación|terminado|descartado"
        ),
    )
    approval_phase: str | None = Field(
        default=None,
        description="intake|section_signoff|None",
    )
    original_filename: str
    pdf_path: str
    markdown_path: str | None = Field(default=None)
    markdown_content: str | None = Field(default=None, sa_column=Column(Text))
    is_rfp: bool | None = Field(default=None)
    classifier_reason: str | None = Field(default=None, sa_column=Column(Text))
    client_name: str | None = Field(default=None, index=True)
    client_country: str | None = Field(default=None, index=True)
    services_requested: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    monthly_volume: int | None = Field(default=None)
    deadline: str | None = Field(default=None)
    budget_range: str | None = Field(default=None)
    departments_needed: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    readability_metrics: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    processing_cost_estimate: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    synthesis_brief: str | None = Field(default=None, sa_column=Column(Text))
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    celery_task_id: str | None = Field(default=None, index=True)
    created_by_user_uuid: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class RfpDepartmentSection(SQLModel, table=True):
    """Per-department analysis / draft / approval state for an RFP ticket."""

    __tablename__ = "rfp_department_sections"
    __table_args__ = (
        UniqueConstraint("ticket_id", "department_id", name="uq_rfp_ticket_department"),
    )

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(index=True)
    department_id: str = Field(index=True)
    key_aspects: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    draft_content: str | None = Field(default=None, sa_column=Column(Text))
    evaluation_results: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    approval_status: str = Field(
        default="pending",
        index=True,
        description="pending|approved|rejected|needs_human_review",
    )
    approver: str
    approved_at: datetime | None = Field(default=None)
    iteration_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
