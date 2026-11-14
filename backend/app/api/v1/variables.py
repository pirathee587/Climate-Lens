from fastapi import APIRouter

from app.schemas.common import ErrorResponse
from app.schemas.source import VariablesResponse
from app.services.catalog import require_verified_catalog

router = APIRouter()


@router.get(
    "", response_model=VariablesResponse, responses={503: {"model": ErrorResponse}}
)
def get_variables() -> VariablesResponse:
    require_verified_catalog()
    raise AssertionError("Phase 02 must supply a verified catalog implementation")
