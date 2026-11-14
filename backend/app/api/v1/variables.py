from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.common import ErrorResponse
from app.schemas.source import VariablesResponse
from app.services.catalog import CatalogService, get_catalog_service

router = APIRouter()


@router.get(
    "", response_model=VariablesResponse, responses={503: {"model": ErrorResponse}}
)
def get_variables(
    catalog: Annotated[CatalogService, Depends(get_catalog_service)],
) -> VariablesResponse:
    return catalog.variables()
