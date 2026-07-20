"""Run a callable with an explicit wall-clock timeout (cross-platform)."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TypeVar

T = TypeVar("T")


class ToolTimeoutError(TimeoutError):
    """Raised when a live tool exceeds AGENT_TOOL_TIMEOUT_SECONDS."""


def call_with_timeout(fn: Callable[..., T], timeout_seconds: float, *args, **kwargs) -> T:
    if timeout_seconds <= 0:
        return fn(*args, **kwargs)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise ToolTimeoutError(
                f"Tool call exceeded timeout of {timeout_seconds:g}s"
            ) from exc
