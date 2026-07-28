"""Explicit classification of user decisions against a pending memory proposal."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Decision = Literal["approve", "reject", "edit", "unclear"]


@dataclass(frozen=True)
class MemoryDecisionResult:
    decision: Decision
    edited_content: str | None = None
    confidence: float = 0.0
    reason: str = ""


_APPROVE = (
    r"^\s*(s[ií]|yes|ok|okay|de\s+acuerdo|acepto|guarda(lo)?|recu[eé]rdalo|aprobar?)\s*[.!]?\s*$",
    r"\b(s[ií],?\s*(guarda|recuerda|acepto)|quiero\s+que\s+lo\s+recuerdes)\b",
)
_REJECT = (
    r"^\s*(no|nop|nel|rechaz(o|ar)|descarta(lo)?|no\s+lo\s+guardes|no\s+gracias)\s*[.!]?\s*$",
    r"\b(no\s+quiero\s+que\s+lo\s+recuerdes|no\s+lo\s+recuerdes|no\s+guardar)\b",
)
_EDIT = (
    r"\b(mejor\s+as[ií]|corrige|edita|en\s+realidad|cambia\s+(el\s+texto|la\s+memoria)|guarda\s+esto\s+en\s+su\s+lugar)\b",
)


def classify_memory_decision(
    *,
    message: str,
    explicit_decision: str | None = None,
    edited_content: str | None = None,
) -> MemoryDecisionResult:
    """Classify against the pending proposal.

    Ambiguity/silence → unclear (fail closed: never assume approval).
    """
    if explicit_decision:
        normalized = explicit_decision.strip().lower()
        if normalized in {"approve", "approved", "yes", "si", "sí"}:
            return MemoryDecisionResult(decision="approve", confidence=1.0, reason="explicit_api")
        if normalized in {"reject", "rejected", "no"}:
            return MemoryDecisionResult(decision="reject", confidence=1.0, reason="explicit_api")
        if normalized in {"edit", "edited"}:
            content = (edited_content or "").strip()
            if not content:
                return MemoryDecisionResult(
                    decision="unclear",
                    confidence=0.2,
                    reason="edit_without_content",
                )
            return MemoryDecisionResult(
                decision="edit",
                edited_content=content,
                confidence=1.0,
                reason="explicit_api",
            )
        return MemoryDecisionResult(decision="unclear", confidence=0.1, reason="unknown_explicit")

    text = (message or "").strip()
    if not text:
        return MemoryDecisionResult(decision="unclear", confidence=0.0, reason="empty")

    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in _APPROVE):
        return MemoryDecisionResult(decision="approve", confidence=0.9, reason="phrase_approve")
    if any(re.search(pattern, lowered) for pattern in _REJECT):
        return MemoryDecisionResult(decision="reject", confidence=0.9, reason="phrase_reject")
    if any(re.search(pattern, lowered) for pattern in _EDIT):
        # Treat the whole message as the replacement text when editing in-chat.
        return MemoryDecisionResult(
            decision="edit",
            edited_content=text,
            confidence=0.75,
            reason="phrase_edit",
        )

    return MemoryDecisionResult(decision="unclear", confidence=0.0, reason="ambiguous")
