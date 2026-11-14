"""ASGI request IDs and safe structured logs, including unhandled errors."""

import json
import logging
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response

logger = logging.getLogger("terratrend.requests")


def configure_logging(level: str) -> None:
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.propagate = False


class RestrictedCORSMiddleware(CORSMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            request = Request(scope)
            if (
                request.method == "OPTIONS"
                and "access-control-request-method" in request.headers
            ):
                response = self.preflight_response(request.headers)
                if response.status_code == 400:
                    response = error_response(
                        scope["state"]["request_id"],
                        400,
                        "BAD_REQUEST",
                        "CORS preflight rejected.",
                        headers={
                            key: value
                            for key, value in response.headers.items()
                            if key.lower() not in {"content-length", "content-type"}
                        },
                    )
                await response(scope, receive, send)
                return
        await super().__call__(scope, receive, send)


class ErrorBoundaryMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def track_start(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, track_start)
        except Exception as exc:
            logger.error(
                json.dumps(
                    {
                        "event": "request_failed",
                        "request_id": scope["state"]["request_id"],
                        "error_type": type(exc).__name__,
                    }
                )
            )
            if started:
                raise
            response = error_response(
                scope["state"]["request_id"],
                500,
                "ANALYSIS_ERROR",
                "Internal server error.",
            )
            await response(scope, receive, send)


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = perf_counter()
        status = 500

        async def with_request_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, with_request_id)
        finally:
            route = scope.get("route")
            # Matched static routes contain no user-controlled path parameters.
            # Unknown paths and future dynamic routes use safe template labels.
            endpoint = (
                scope["path"]
                if route is not None and not scope.get("path_params")
                else getattr(route, "path", "unmatched")
            )
            logger.info(
                json.dumps(
                    {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "event": "request_completed",
                        "request_id": request_id,
                        "method": scope["method"],
                        "endpoint": endpoint,
                        "status": status,
                        "duration_ms": round((perf_counter() - started) * 1000, 3),
                    }
                )
            )
