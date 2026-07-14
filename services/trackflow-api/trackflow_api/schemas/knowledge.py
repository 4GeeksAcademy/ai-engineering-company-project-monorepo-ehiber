from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class SourceReferenceResponse(BaseModel):
    source_document: str
    section: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceReferenceResponse]
