"""Independent regional analyses over one verified two-region catalog per request."""

from typing import Annotated

from fastapi import Depends

from app.core.errors import APIError
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ComparisonRequest,
    ComparisonResponse,
    DatasetCompatibility,
    YearRange,
)
from app.services.analysis_service import AnalysisService, get_analysis_service

INDEPENDENT_WARNING = (
    "Regional tests are independent. No test of the difference between slopes "
    "has been performed; significance in one region does not establish a "
    "statistically significant difference between regions or a cause."
)


def verified_result_compatibility(
    left: AnalysisResponse, right: AnalysisResponse
) -> DatasetCompatibility:
    """Defense after source validation, never classification of untrusted artifacts."""
    flags = DatasetCompatibility(
        same_product=left.source.collection_id == right.source.collection_id,
        same_version=left.source.version == right.source.version,
        same_run=left.source.run_type == right.source.run_type == "Final",
    )
    if not all(flags.model_dump().values()) or any(
        getattr(left.source, field) != getattr(right.source, field)
        for field in ("original_variable", "original_unit", "aggregation_method")
    ):
        raise APIError(
            409,
            "INCOMPATIBLE_DATA",
            "Reviewed sources are not scientifically compatible.",
        )
    return flags


def complete_years(result: AnalysisResponse) -> set[int]:
    return {
        row.year
        for row in result.annual
        if row.valid_months == 12 and row.precipitation_total_mm is not None
    }


class ComparisonService:
    def __init__(self, analysis: AnalysisService) -> None:
        self.analysis = analysis

    def compare(self, request: ComparisonRequest) -> ComparisonResponse:
        # Keep the strict catalog gate: uncertain/incompatible artifacts remain503.
        snapshots = self.analysis.catalog.validated_snapshots()
        common = request.model_dump(exclude={"left_region_id", "right_region_id"})
        left = self.analysis.analyze_validated(
            AnalysisRequest(**common, region_id=request.left_region_id), snapshots
        )
        right = self.analysis.analyze_validated(
            AnalysisRequest(**common, region_id=request.right_region_id), snapshots
        )
        compatibility = verified_result_compatibility(left, right)
        left_years, right_years = complete_years(left), complete_years(right)
        shared = sorted(left_years & right_years)
        if len(shared) < 10:
            raise APIError(
                422,
                "INSUFFICIENT_DATA",
                "At least 10 shared complete years are required.",
            )
        warnings = [*left.warnings, *right.warnings, INDEPENDENT_WARNING]
        warnings.extend(
            [
                "Left complete analysis years: "
                + ", ".join(map(str, sorted(left_years))),
                "Right complete analysis years: "
                + ", ".join(map(str, sorted(right_years))),
                "Shared complete years: " + ", ".join(map(str, shared)),
            ]
        )
        if left_years != right_years:
            warnings.append(
                "Regional estimates use different eligible year sets and are not "
                "matched-sample comparisons. Each statistic uses all complete years "
                "for its own region within the unchanged requested interval."
            )
        try:
            return ComparisonResponse(
                shared_requested_period=YearRange(
                    start_year=request.start_year, end_year=request.end_year
                ),
                shared_analyzed_years=shared,
                dataset_compatibility=compatibility,
                left=left,
                right=right,
                warnings=warnings,
            )
        except ValueError:
            raise APIError(
                500, "ANALYSIS_ERROR", "Comparison response failed validation."
            ) from None


def get_comparison_service(
    analysis: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> ComparisonService:
    return ComparisonService(analysis)
