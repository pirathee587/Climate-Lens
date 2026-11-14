from fastapi import APIRouter

from app.schemas.common import ErrorResponse
from app.schemas.source import RegionsResponse
from app.services.catalog import require_verified_catalog

router = APIRouter()


@router.get(
    "/presets",
    response_model=RegionsResponse,
    responses={503: {"model": ErrorResponse}},
)
def get_regions() -> RegionsResponse:
    require_verified_catalog()
    raise AssertionError("Phase 02 must supply a verified catalog implementation")
