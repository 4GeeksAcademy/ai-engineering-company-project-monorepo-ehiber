from fastapi import APIRouter

from ..schemas.knowledge import AskRequest, AskResponse
from ..services.rag_service import ask

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/ask", response_model=AskResponse)
def ask_knowledge(payload: AskRequest) -> AskResponse:
    return ask(payload.question)
