from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.schemas.common import ErrorResponse
from app.services.analysis_service import AnalysisService, get_analysis_service

router = APIRouter()


@router.post(
    "", response_model=AnalysisResponse, responses={503: {"model": ErrorResponse}}
)
def analyze(
    body: AnalysisRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalysisResponse:
    return service.analyze(body)
