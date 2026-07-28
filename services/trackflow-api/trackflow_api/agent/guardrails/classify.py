from __future__ import annotations

import re

from .types import InputGuardResult

_PERSONAL_USE_PATTERNS = (
    r"\bensayo\b",
    r"\bessay\b",
    r"\btarea(s)?\b",
    r"\bhomework\b",
    r"\bpoema\b",
    r"\bpoem\b",
    r"\bterapeuta\b",
    r"\btherapy\b",
    r"\bconsejo personal\b",
    r"\bpersonal advice\b",
    r"escribe(me)?\s+(un\s+|una\s+)?(c[oó]digo|script|funci[oó]n|app)",
    r"write\s+(me\s+)?(code|an?\s+essay|a\s+poem)",
    r"ayudame\s+a\s+escribir",
    r"ayuda(me)?\s+con\s+(mi\s+)?(c[oó]digo|proyecto|tarea|universidad)",
    r"act[uú]a\s+como\s+(mi\s+)?terapeuta",
)

_INJECTION_PATTERNS = (
    r"ignore\s+(your\s+|all\s+)?(previous\s+|prior\s+)?(instructions|rules)",
    r"ignora\s+(tus\s+|las\s+|todas\s+las\s+)?(instrucciones|reglas)",
    r"act\s+as\s+(an?\s+)?(assistant|ai)\s+with\s+no\s+rules",
    r"act[uú]a\s+como\s+si\s+no\s+tuvieras\s+reglas",
    r"forget\s+(about\s+|that\s+)?(you\s+)?(work|are|trackflow)",
    r"olvida(te)?\s+(de\s+)?(trackflow|tus\s+instrucciones|que\s+trabajas)",
    r"system\s+prompt",
    r"\bjailbreak\b",
    r"sin\s+reglas",
    r"sin\s+restricciones",
    r"developer\s+mode",
    r"dan\s+mode",
    r"override\s+(your\s+)?(instructions|rules|system)",
    r"desactiva\s+(tus\s+)?(reglas|instrucciones|guardrails)",
)

_OFF_TOPIC_PATTERNS = (
    r"^(hola|hello|hey|buenas|buenos\s+d[ií]as|good\s+morning)\b",
    r"c[oó]mo\s+est[aá]s",
    r"how\s+are\s+you",
    r"qu[eé]\s+hora\s+es",
    r"what\s+time\s+is\s+it",
    r"hora\s+en\s+\w+",
    r"\bchiste\b",
    r"\bjoke\b",
    r"cu[eé]ntame\s+algo",
    r"qu[eé]\s+es\s+(la\s+)?log[ií]stica(\s+inversa)?\b",
    r"what\s+is\s+(reverse\s+)?logistics\b",
    r"qu[eé]\s+es\s+(la\s+)?[uú]ltima\s+milla\b",
    r"clima\s+en\b",
    r"weather\s+in\b",
)


def classify_input(question: str) -> InputGuardResult:
    """Classify abuse / scope before the agent runs tools or RAG."""
    text = (question or "").strip()
    lowered = text.lower()

    if _matches(lowered, _PERSONAL_USE_PATTERNS):
        return InputGuardResult(
            decision="reject_personal_use",
            failure_type="content",
            guardrail="detect_personal_use",
            reason="personal_chatbot_use",
        )

    if _matches(lowered, _INJECTION_PATTERNS):
        return InputGuardResult(
            decision="reject_injection",
            failure_type="security",
            guardrail="detect_injection",
            reason="prompt_injection",
        )

    if _matches(lowered, _OFF_TOPIC_PATTERNS):
        return InputGuardResult(
            decision="redirect_off_topic",
            failure_type="content",
            guardrail="detect_off_topic",
            reason="off_domain_redirect",
        )

    return InputGuardResult(
        decision="allow",
        failure_type=None,
        guardrail=None,
        reason=None,
    )


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)
