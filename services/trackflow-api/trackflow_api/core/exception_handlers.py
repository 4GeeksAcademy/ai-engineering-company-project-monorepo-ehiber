import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger("trackflow_api")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else None
        field = ".".join(str(part) for part in first_error["loc"][1:]) if first_error else "request"
        message = first_error["msg"] if first_error else "The request payload is invalid."
        return JSONResponse(
            status_code=400,
            content={"detail": {"field": field, "message": message}},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, str):
            return JSONResponse(status_code=exc.status_code, content={"detail": detail})
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )
