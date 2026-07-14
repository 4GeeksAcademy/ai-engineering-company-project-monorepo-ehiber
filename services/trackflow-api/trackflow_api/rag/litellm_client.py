from __future__ import annotations

from typing import Any

from litellm import completion, embedding

from ..core.config import get_settings


def _litellm_kwargs() -> dict[str, Any]:
    settings = get_settings()
    kwargs: dict[str, Any] = {}
    if settings.litellm_api_key:
        kwargs["api_key"] = settings.litellm_api_key
    if settings.litellm_api_base:
        kwargs["api_base"] = settings.litellm_api_base
    return kwargs


def create_embeddings(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    response = embedding(
        model=settings.rag_embedding_model,
        input=texts,
        **_litellm_kwargs(),
    )
    vectors: list[list[float]] = []
    for item in response.data:
        raw = item["embedding"] if isinstance(item, dict) else item.embedding
        vectors.append([float(value) for value in raw])
    return vectors


def create_completion(*, system_prompt: str, user_prompt: str) -> str:
    settings = get_settings()
    response = completion(
        model=settings.rag_llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **_litellm_kwargs(),
    )
    content = response.choices[0].message.content
    if content is None:
        return ""
    return str(content).strip()
