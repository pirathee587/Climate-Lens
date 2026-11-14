"""Validated source → Gaja aggregation/analysis → existing v1 response contract."""

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Request

from app.core.errors import APIError
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnnualItem,
    MonthlyItem,
    Statistics,
)
from app.schemas.quality import ReviewedQualityPolicy
from app.schemas.repository import ValidatedMonthlySeries
from app.schemas.source import SourceDescriptor
from app.services.catalog import CatalogService, get_catalog_service
from app.services.statistics_adapter import (
    ScienceInputError,
    ScienceInsufficientData,
    ScienceNumericalError,
    StatisticsAdapter,
    StatisticsUnavailable,
    get_statistics_adapter,
)


class AnalysisService:
    def __init__(
        self,
        catalog: CatalogService,
        science: StatisticsAdapter,
        quality_policies: tuple[ReviewedQualityPolicy, ...],
    ) -> None:
        self.catalog = catalog
        self.science = science
        self.quality_policies = quality_policies

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        return self.analyze_validated(request, self.catalog.validated_snapshots())

    def analyze_validated(
        self,
        request: AnalysisRequest,
        snapshots: tuple[ValidatedMonthlySeries, ...],
    ) -> AnalysisResponse:
        """Internal orchestration over this request's already verified catalog."""
        selected = next(
            (
                item
                for item in snapshots
                if item.descriptor.region.id == request.region_id
            ),
            None,
        )
        if selected is None:
            raise APIError(422, "INVALID_ARGUMENT", "Select a verified region preset.")
        descriptor = selected.descriptor
        manifest = descriptor.manifest
        if descriptor.variable.id != request.variable_id:
            raise APIError(
                422, "INVALID_ARGUMENT", "Variable does not match verified data."
            )
        if request.start_year < int(manifest.time_start[:4]) or request.end_year > int(
            manifest.time_end[:4]
        ):
            raise APIError(
                422, "INVALID_ARGUMENT", "Requested years exceed verified coverage."
            )
        policies = [
            p
            for p in self.quality_policies
            if p.snapshot_sha256.lower() == manifest.output_sha256.lower()
        ]
        if len(policies) != 1:
            raise APIError(
                503,
                "DATASET_UNAVAILABLE",
                "Reviewed source quality policy is unavailable.",
            )
        try:
            policy = ReviewedQualityPolicy.model_validate(
                policies[0].model_dump(warnings="error")
            )
            if policy.review.reviewed_at < manifest.retrieved_at_utc:
                raise ValueError("quality review predates source retrieval")
        except ValueError:
            raise APIError(
                503,
                "DATASET_UNAVAILABLE",
                "Reviewed source quality policy is unavailable.",
            ) from None
        monthly = tuple(
            row
            for row in selected.observations
            if request.start_year <= int(row.period[:4]) <= request.end_year
        )
        try:
            aggregation = self.science.aggregate_monthly(
                monthly, policy, request.start_year, request.end_year
            )
            if len(aggregation.observations) < 10:
                raise ScienceInsufficientData(
                    "At least 10 complete years are required."
                )
            trend = self.science.analyze(aggregation, request.alpha)
            statistics = Statistics.model_validate(trend.statistics_payload())
            actual_years = tuple(row.year for row in aggregation.observations)
            if (
                trend.analyzed_years != actual_years
                or trend.n_complete_years != len(actual_years)
                or statistics.alpha != request.alpha
            ):
                raise ScienceNumericalError(
                    "Scientific response metadata is inconsistent."
                )
            warnings = [*aggregation.warnings, *trend.warnings]
            warnings.append(
                "Analyzed complete calendar years: " + ", ".join(map(str, actual_years))
            )
            if aggregation.missing_periods:
                warnings.append(
                    "Absent monthly periods: " + ", ".join(aggregation.missing_periods)
                )
            if any(row.valid_fraction is None for row in monthly):
                warnings.append(
                    "Coverage fractions are unavailable for some source observations; "
                    "the reviewed quality policy governs eligibility."
                )
            rejected = sum(
                row.precipitation_total_mm is not None
                and row.quality_flag not in policy.accepted_quality_flags
                for row in monthly
            )
            if rejected:
                warnings.append(
                    f"{rejected} quality-rejected values remain in monthly output "
                    "and are excluded from annual analysis."
                )
            warnings.append(
                f"Scientific implementation: {trend.mann_kendall.method_version}; "
                f"SciPy {trend.scipy_version}; NumPy {trend.numpy_version}."
            )
            return AnalysisResponse(
                analysis_id=uuid4(),
                request=request,
                region=descriptor.region,
                source=SourceDescriptor(
                    collection_id=manifest.collection_id,
                    version=manifest.version_label,
                    run_type=manifest.run_type,
                    original_variable=manifest.original_variable_name,
                    original_unit=manifest.original_units,
                    snapshot_id=manifest.snapshot_id,
                    snapshot_sha256=manifest.output_sha256,
                    retrieved_at=manifest.retrieved_at_utc,
                    source_uri=manifest.source_url,
                    aggregation_method=f"{manifest.spatial_aggregation}; "
                    f"{manifest.rate_to_total_conversion}; "
                    f"{manifest.missing_data_policy}",
                ),
                monthly=[
                    MonthlyItem(
                        period=row.period,
                        precipitation_total_mm=row.precipitation_total_mm,
                        valid_fraction=row.valid_fraction,
                    )
                    for row in monthly
                ],
                annual=[
                    AnnualItem(
                        year=row.year,
                        precipitation_total_mm=row.total_mm,
                        valid_months=row.valid_months,
                    )
                    for row in aggregation.year_summaries
                ],
                statistics=statistics,
                warnings=warnings,
                algorithm_version=trend.algorithm_version,
            )
        except StatisticsUnavailable:
            raise APIError(
                503,
                "STATISTICS_ENGINE_UNAVAILABLE",
                "Statistical analysis is temporarily unavailable.",
            ) from None
        except ScienceInsufficientData:
            raise APIError(
                422,
                "INSUFFICIENT_DATA",
                "At least 10 complete calendar years are required.",
            ) from None
        except ScienceInputError:
            raise APIError(
                422, "INVALID_ARGUMENT", "Scientific inputs failed validation."
            ) from None
        except Exception:
            # Includes numerical failures and invalid/nonfinite response mappings.
            raise APIError(
                500, "ANALYSIS_ERROR", "Statistical analysis could not be completed."
            ) from None


def get_analysis_service(
    request: Request,
    catalog: Annotated[CatalogService, Depends(get_catalog_service)],
    science: Annotated[StatisticsAdapter, Depends(get_statistics_adapter)],
) -> AnalysisService:
    return AnalysisService(
        catalog, science, request.app.state.settings.snapshot_quality_policies
    )
