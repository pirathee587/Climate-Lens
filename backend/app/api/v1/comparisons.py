"""Independent comparisons publish both analysis IDs only on complete success."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.analysis import ComparisonRequest, ComparisonResponse
from app.schemas.common import ErrorResponse
from app.services.comparison_service import ComparisonService, get_comparison_service
from app.services.result_cache import ResultCache, get_result_cache

router = APIRouter()


@router.post(
    "",
    response_model=ComparisonResponse,
    responses={409: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def compare(
    body: ComparisonRequest,
    service: Annotated[ComparisonService, Depends(get_comparison_service)],
    cache: Annotated[ResultCache, Depends(get_result_cache)],
) -> ComparisonResponse:
    result = service.compare(body)
    cache.put_many((result.left, result.right))
    return result
