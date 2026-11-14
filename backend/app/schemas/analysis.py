"""Future analysis/comparison contracts only; no data loading or calculations."""

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
