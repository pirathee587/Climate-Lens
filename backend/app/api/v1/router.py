from fastapi import APIRouter

from app.api.v1 import analyses, regions, variables

router = APIRouter(prefix="/api/v1")
router.include_router(variables.router, prefix="/variables", tags=["catalog"])
router.include_router(regions.router, prefix="/regions", tags=["catalog"])

router.include_router(analyses.router, prefix="/analyses", tags=["analysis"])
