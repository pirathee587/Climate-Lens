"""Analysis, comparison and reproducibility contracts; no calculations."""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import Alpha, APIModel, NonEmpty, Period, Year
from app.schemas.source import RegionDescriptor, SourceDescriptor

Fraction = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Rainfall = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class SourceMode(StrEnum):
    VERIFIED_SNAPSHOT = "verified_snapshot"


class SignificanceStatus(StrEnum):
    SIGNIFICANT = "significant"
    NOT_SIGNIFICANT = "not_significant"
    INDETERMINATE = "indeterminate"


class Direction(StrEnum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    NO_CLEAR_DIRECTION = "no_clear_direction"


class YearRange(APIModel):
    start_year: Year
    end_year: Year

    @model_validator(mode="after")
    def ordered_years(self) -> "YearRange":
        if self.start_year > self.end_year:
            raise ValueError("start_year must not exceed end_year")
        return self


class AnalysisParameters(YearRange):
    variable_id: Literal["precipitation"]
    alpha: Alpha = 0.05
    source_mode: SourceMode = SourceMode.VERIFIED_SNAPSHOT


class AnalysisRequest(AnalysisParameters):
    region_id: NonEmpty


class ComparisonRequest(AnalysisParameters):
    left_region_id: NonEmpty
    right_region_id: NonEmpty

    @model_validator(mode="after")
    def distinct_regions(self) -> "ComparisonRequest":
        if self.left_region_id == self.right_region_id:
            raise ValueError("comparison requires distinct regions")
        return self


class MonthlyItem(APIModel):
    period: Period
    precipitation_total_mm: Rainfall | None
    valid_fraction: Fraction | None


class AnnualItem(APIModel):
    year: Year
    precipitation_total_mm: Rainfall | None
    valid_months: Annotated[int, Field(strict=True, ge=0, le=12)]


class Statistics(APIModel):
    sample_years: Annotated[int, Field(strict=True, ge=0)] | None = None
    ols_slope_mm_per_year: float | None = None
    ols_r_squared: Fraction | None = None
    sen_slope_mm_per_year: float | None = None
    sen_slope_ci95_mm_per_year: tuple[float | None, float | None] = (None, None)
    mann_kendall_p_value: Fraction | None = None
    mann_kendall_method: NonEmpty
    alpha: Alpha = 0.05
    direction: Direction | None = None
    significance_status: SignificanceStatus = SignificanceStatus.INDETERMINATE
    assumptions_status: NonEmpty = "not_evaluated"

    @model_validator(mode="after")
    def ordered_interval(self) -> "Statistics":
        low, high = self.sen_slope_ci95_mm_per_year
        if low is not None and high is not None and low > high:
            raise ValueError("Sen confidence interval must be ordered")
        return self


class AnalysisResponse(APIModel):
    analysis_id: UUID
    request: AnalysisRequest
    region: RegionDescriptor
    source: SourceDescriptor
    monthly: list[MonthlyItem]
    annual: list[AnnualItem]
    statistics: Statistics
    warnings: list[str]
    algorithm_version: NonEmpty

    @model_validator(mode="after")
    def chronological_series(self) -> "AnalysisResponse":
        for periods in (
            [item.period for item in self.monthly],
            [item.year for item in self.annual],
        ):
            if periods != sorted(set(periods)):
                raise ValueError("time series must be ordered without duplicates")
        return self


class DatasetCompatibility(APIModel):
    same_product: bool
    same_version: bool
    same_run: bool


class ComparisonResponse(APIModel):
    shared_requested_period: YearRange
    shared_analyzed_years: list[Year]
    dataset_compatibility: DatasetCompatibility
    left: AnalysisResponse
    right: AnalysisResponse
    warnings: list[str]

    @model_validator(mode="after")
    def valid_shared_years(self) -> "ComparisonResponse":
        left_years = {
            row.year
            for row in self.left.annual
            if row.valid_months == 12 and row.precipitation_total_mm is not None
        }
        right_years = {
            row.year
            for row in self.right.annual
            if row.valid_months == 12 and row.precipitation_total_mm is not None
        }
        if self.shared_analyzed_years != sorted(left_years & right_years):
            raise ValueError("shared years must match complete regional years")
        if len(self.shared_analyzed_years) < 10:
            raise ValueError("at least ten shared complete years are required")
        if self.left.region.id == self.right.region.id:
            raise ValueError("comparison regions must differ")
        if self.left.analysis_id == self.right.analysis_id:
            raise ValueError("comparison analyses require distinct IDs")
        for side in (self.left, self.right):
            if (
                side.request.start_year != self.shared_requested_period.start_year
                or side.request.end_year != self.shared_requested_period.end_year
                or side.request.region_id != side.region.id
                or any(
                    not self.shared_requested_period.start_year
                    <= row.year
                    <= self.shared_requested_period.end_year
                    for row in side.annual
                )
            ):
                raise ValueError("comparison period/region is inconsistent")
        return self


class ReproducibilityMetadata(APIModel):
    analysis_id: UUID
    request: AnalysisRequest
    region: RegionDescriptor
    source: SourceDescriptor
    normalized_units: dict[str, str]
    statistics: Statistics
    algorithm_version: NonEmpty
    warnings: list[str]
    scientific_limitations: list[str]
