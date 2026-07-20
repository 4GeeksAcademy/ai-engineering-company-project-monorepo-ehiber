from fastapi import APIRouter, HTTPException

from ..schemas.knowledge import AskRequest, AskResponse
from ..services.rag_service import ask, get_run_trace

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/ask", response_model=AskResponse)
def ask_knowledge(payload: AskRequest) -> AskResponse:
    try:
        return ask(payload.question)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail="No se pudo completar la consulta de conocimiento. Inténtalo de nuevo más tarde.",
        ) from exc


@router.get("/runs/{run_id}")
def knowledge_run_trace(run_id: str) -> dict:
    return get_run_trace(run_id)
