import logging
import time

from fastapi import Request

logger = logging.getLogger("api.timing")


async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "%s %s → %s | %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
