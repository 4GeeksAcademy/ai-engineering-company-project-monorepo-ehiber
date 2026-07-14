from __future__ import annotations

from .litellm_client import create_completion
from .types import QueryResult, RetrievedChunk, SourceReference

SYSTEM_PROMPT = """Eres un account manager de TrackFlow respondiendo a un prospecto o cliente en una llamada comercial.

Responde en español, con tono profesional y claro. Usa únicamente la información del contexto recuperado.
No inventes porcentajes, tarifas, plazos ni condiciones que no estén en el contexto.

Reglas de negocio obligatorias:
- Nunca prometas SLA de entrega durante fechas de alta demanda (Black Friday, Navidad, Rebajas de enero en España).
- Las devoluciones internacionales nunca son automáticas; deben remitirse a gestión manual de Sofía Ramos.
- Ningún descuento de almacenamiento puede ofrecerse sin mencionar que requiere aprobación de Miguel Torres.
- Si el contexto no contiene la respuesta, indica que requiere confirmación interna y no inventes condiciones.

La respuesta debe ser un texto final listo para compartir con el cliente, no fragmentos crudos ni listas de búsqueda."""


def _build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            "Pregunta del cliente:\n"
            f"{question}\n\n"
            "Contexto recuperado:\n"
            "(sin contexto relevante)"
        )

    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[Fuente {index}]",
                    f"Documento: {chunk.source_document}",
                    f"Sección: {chunk.section}",
                    f"Contenido: {chunk.text}",
                ]
            )
        )

    return (
        "Pregunta del cliente:\n"
        f"{question}\n\n"
        "Contexto recuperado:\n"
        f"{chr(10).join(context_blocks)}"
    )


def _unique_sources(chunks: list[RetrievedChunk]) -> list[SourceReference]:
    seen: set[tuple[str, str]] = set()
    sources: list[SourceReference] = []
    for chunk in chunks:
        key = (chunk.source_document, chunk.section)
        if key in seen:
            continue
        seen.add(key)
        sources.append(SourceReference(source_document=chunk.source_document, section=chunk.section))
    return sources


def query(question: str, chunks: list[RetrievedChunk]) -> QueryResult:
    answer = create_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_build_user_prompt(question, chunks),
    )
    return QueryResult(answer=answer, sources=_unique_sources(chunks))
