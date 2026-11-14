"""Create, retrieve and export validated analysis results."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import Response

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ReproducibilityMetadata,
)
from app.schemas.common import ErrorResponse
from app.services.analysis_service import AnalysisService, get_analysis_service
from app.services.export_service import csv_download, metadata
from app.services.result_cache import (
    ResultCache,
    get_cached_analysis,
    get_result_cache,
)

router = APIRouter()
CachedAnalysis = Annotated[AnalysisResponse, Depends(get_cached_analysis)]


@router.post(
    "", response_model=AnalysisResponse, responses={503: {"model": ErrorResponse}}
)
def analyze(
    body: AnalysisRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
    cache: Annotated[ResultCache, Depends(get_result_cache)],
) -> AnalysisResponse:
    result = service.analyze(body)
    cache.put_many((result,))
    return result


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve(result: CachedAnalysis) -> AnalysisResponse:
    return result


@router.get(
    "/{analysis_id}/export.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}, 404: {"model": ErrorResponse}},
)
def export_monthly(result: CachedAnalysis) -> Response:
    return csv_download(result, "monthly")


@router.get(
    "/{analysis_id}/annual.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}, 404: {"model": ErrorResponse}},
)
def export_annual(result: CachedAnalysis) -> Response:
    return csv_download(result, "annual")


@router.get(
    "/{analysis_id}/metadata.json",
    response_model=ReproducibilityMetadata,
    responses={404: {"model": ErrorResponse}},
)
def export_metadata(
    result: CachedAnalysis, response: Response
) -> ReproducibilityMetadata:
    response.headers["Content-Disposition"] = (
        f'attachment; filename="terratrend-{result.analysis_id}-metadata.json"'
    )
    return metadata(result)
