from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.common import ErrorResponse
from app.schemas.source import RegionsResponse
from app.services.catalog import CatalogService, get_catalog_service

router = APIRouter()


@router.get(
    "/presets",
    response_model=RegionsResponse,
    responses={503: {"model": ErrorResponse}},
)
def get_regions(
    catalog: Annotated[CatalogService, Depends(get_catalog_service)],
) -> RegionsResponse:
    return catalog.regions()
