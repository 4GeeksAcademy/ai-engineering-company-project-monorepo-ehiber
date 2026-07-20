from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class SourceReferenceResponse(BaseModel):
    source_document: str
    section: str


class TraceStepResponse(BaseModel):
    node: str
    status: str = "ok"
    ms: int = 0
    detail: dict = Field(default_factory=dict)


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceReferenceResponse]
    run_id: str
    trace: list[TraceStepResponse] = Field(default_factory=list)
    checkpointed: bool = False
