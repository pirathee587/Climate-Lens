"""TerraTrend API with verified analysis, comparison and application-local results."""

from fastapi import FastAPI

from app.api.v1.router import router
from app.core.config import Settings
from app.core.errors import register_error_handlers
from app.core.logging import (
    ErrorBoundaryMiddleware,
    RequestContextMiddleware,
    RestrictedCORSMiddleware,
    configure_logging,
)
from app.schemas.common import ErrorResponse, HealthResponse
from app.services.result_cache import ResultCache


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    configure_logging(settings.log_level)
    development = settings.app_env != "production"
    app = FastAPI(
        title="TerraTrend API",
        version="0.1.0",
        docs_url="/docs" if development else None,
        redoc_url=None,
        openapi_url="/openapi.json" if development else None,
        responses={
            400: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )
    app.state.settings = settings
    app.state.result_cache = ResultCache(
        ttl_seconds=settings.result_cache_ttl_seconds,
        max_entries=settings.result_cache_max_entries,
    )
    register_error_handlers(app)
    app.include_router(router)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse()

    app.add_middleware(ErrorBoundaryMiddleware)
    app.add_middleware(
        RestrictedCORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Request-ID", "Content-Disposition"],
    )
    app.add_middleware(RequestContextMiddleware)
    return app


app = create_app()
