from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FailureType = Literal["structural", "content", "security"]
GuardDecision = Literal[
    "allow",
    "reject_injection",
    "reject_personal_use",
    "redirect_off_topic",
]


@dataclass(frozen=True)
class InputGuardResult:
    decision: GuardDecision
    failure_type: FailureType | None
    guardrail: str | None
    reason: str | None = None


@dataclass(frozen=True)
class TrackingAuthResult:
    authorized: bool
    tracking_id: str | None
    failure_type: FailureType | None = None
    guardrail: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class OutputGuardResult:
    ok: bool
    answer: str
    failure_type: FailureType | None = None
    guardrail: str | None = None
    reason: str | None = None
