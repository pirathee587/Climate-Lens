"""Central safe v1 errors; never echo exception messages or request bodies."""

from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    request_id: str,
    status: int,
    code: str,
    message: str,
    details: dict | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or {},
            request_id=UUID(request_id),
        )
    )
    return JSONResponse(
        payload.model_dump(mode="json"), status_code=status, headers=headers
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def api_error(request: Request, exc: APIError) -> JSONResponse:
        return error_response(
            request.state.request_id, exc.status_code, exc.code, exc.message
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        malformed = any(error["type"] == "json_invalid" for error in exc.errors())
        return error_response(
            request.state.request_id,
            400 if malformed else 422,
            "BAD_REQUEST" if malformed else "INVALID_ARGUMENT",
            "Malformed JSON request." if malformed else "Request validation failed.",
            # No input, exception context or user-supplied labels are reflected.
            details={"error_count": len(exc.errors())},
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        code, message = {
            400: ("BAD_REQUEST", "Bad request."),
            404: ("NOT_FOUND", "Resource not found."),
            405: ("METHOD_NOT_ALLOWED", "Method not allowed."),
            422: ("INVALID_ARGUMENT", "Request validation failed."),
        }.get(exc.status_code, ("HTTP_ERROR", "Request could not be completed."))
        if exc.status_code >= 500:
            code, message = "ANALYSIS_ERROR", "Internal server error."
        return error_response(
            request.state.request_id,
            exc.status_code,
            code,
            message,
            headers=exc.headers,
        )
