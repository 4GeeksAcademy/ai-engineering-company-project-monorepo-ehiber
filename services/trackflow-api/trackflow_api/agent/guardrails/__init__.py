"""Input/output harness guardrails for the TrackFlow CX knowledge agent."""

from .auth_tracking import authorize_tracking, extract_tracking_id, lookup_tracking_owner
from .classify import classify_input
from .country_policy import detect_policy_country_lock, policy_lock_instruction
from .messages import (
    REDIRECT_GENERAL_LOGISTICS,
    REDIRECT_OFF_TOPIC,
    REJECTION_INJECTION,
    REJECTION_PERSONAL_USE,
    REJECTION_UNAUTHORIZED_TRACKING,
)
from .metrics import get_guardrail_stats, record_guardrail_event, reset_guardrail_stats
from .output import validate_output
from .sanitize import sanitize_untrusted_text, wrap_rag_context, wrap_tool_result
from .types import FailureType, InputGuardResult, OutputGuardResult, TrackingAuthResult

__all__ = [
    "FailureType",
    "InputGuardResult",
    "OutputGuardResult",
    "TrackingAuthResult",
    "authorize_tracking",
    "classify_input",
    "detect_policy_country_lock",
    "extract_tracking_id",
    "get_guardrail_stats",
    "lookup_tracking_owner",
    "policy_lock_instruction",
    "record_guardrail_event",
    "reset_guardrail_stats",
    "sanitize_untrusted_text",
    "validate_output",
    "wrap_rag_context",
    "wrap_tool_result",
    "REDIRECT_GENERAL_LOGISTICS",
    "REDIRECT_OFF_TOPIC",
    "REJECTION_INJECTION",
    "REJECTION_PERSONAL_USE",
    "REJECTION_UNAUTHORIZED_TRACKING",
]
