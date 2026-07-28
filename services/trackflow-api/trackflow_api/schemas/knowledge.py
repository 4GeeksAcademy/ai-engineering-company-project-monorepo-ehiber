from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    memory_decision: Literal["approve", "reject", "edit"] | None = None
    proposal_id: str | None = None
    edited_content: str | None = Field(default=None, max_length=2000)


class SourceReferenceResponse(BaseModel):
    source_document: str
    section: str


class TraceStepResponse(BaseModel):
    node: str
    status: str = "ok"
    ms: int = 0
    detail: dict = Field(default_factory=dict)


class MemoryProposalResponse(BaseModel):
    proposal_id: str
    content: str
    consolidation_key: str
    carrier: str | None = None
    country: str | None = None
    topic: str | None = None
    status: str = "pending"


class MemoryDecisionResponse(BaseModel):
    handled: bool = False
    decision: str | None = None
    proposal_id: str | None = None
    message: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceReferenceResponse]
    run_id: str
    trace: list[TraceStepResponse] = Field(default_factory=list)
    checkpointed: bool = False
    memory_proposal: MemoryProposalResponse | None = None
    memory_decision: MemoryDecisionResponse | None = None


class GuardrailStatsResponse(BaseModel):
    by_failure_type: dict[str, int] = Field(default_factory=dict)
    by_guardrail: dict[str, int] = Field(default_factory=dict)
    total: int = 0


class MemoryAuditItem(BaseModel):
    id: int | None = None
    proposal_id: str
    event_type: str
    proposed_content: str
    decision_content: str | None = None
    consolidation_key: str | None = None
    created_at: str


class MemoryAuditListResponse(BaseModel):
    items: list[MemoryAuditItem] = Field(default_factory=list)
