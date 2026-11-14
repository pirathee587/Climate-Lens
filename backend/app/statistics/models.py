"""Immutable science-only types and explicit validation errors; no web/database IO."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Literal

MAX_YEARS = 200  # Bounds the quadratic Sen estimator; not a scientific threshold.
MIN_COMPLETE_YEARS = 10


class InvalidDataError(ValueError):
    """Malformed, mixed, duplicate or nonfinite scientific inputs."""


class InsufficientDataError(ValueError):
    def __init__(self, available: int, minimum: int = MIN_COMPLETE_YEARS):
        self.available = available
        self.minimum = minimum
        super().__init__(
            f"At least {minimum} observations required; received {available}."
        )


class NumericalAnalysisError(ValueError):
    """Computation is undefined or outside finite floating-point range."""


def checked_year(year: int) -> int:
    if (
        isinstance(year, bool)
        or not isinstance(year, Integral)
        or not 1 <= year <= 9999
    ):
        raise InvalidDataError("Year must be an integer in the Gregorian calendar.")
    return int(year)


def finite_number(value: float, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidDataError("Observation must be a finite real number.")
    try:
        numeric = float(value)
    except (OverflowError, ValueError):
        raise InvalidDataError("Observation exceeds floating-point range.") from None
    if not math.isfinite(numeric) or (nonnegative and numeric < 0):
        raise InvalidDataError(
            "Observation must be finite and nonnegative where required."
        )
    return numeric


def checked_alpha(alpha: float) -> float:
    alpha = finite_number(alpha)
    if not 0 < alpha < 1:
        raise InvalidDataError("Alpha must be strictly between zero and one.")
    return alpha


@dataclass(frozen=True)
class AnnualObservation:
    year: int
    total_mm: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "year", checked_year(self.year))
        object.__setattr__(
            self, "total_mm", finite_number(self.total_mm, nonnegative=True)
        )


@dataclass(frozen=True)
class MonthlyObservation:
    region_id: str
    period: str
    total_mm: float | None
    quality_flag: str
    validity: Literal["valid", "missing", "invalid"] = "valid"
    valid_fraction: float | None = None


@dataclass(frozen=True)
class AnnualSummary:
    year: int
    total_mm: float | None
    valid_months: int


@dataclass(frozen=True)
class AggregationResult:
    region_id: str
    observations: tuple[AnnualObservation, ...]
    year_summaries: tuple[AnnualSummary, ...]
    excluded_years: tuple[int, ...]
    missing_periods: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class OLSResult:
    slope_mm_per_year: float
    intercept_mm: float
    r_squared: float | None


@dataclass(frozen=True)
class SenResult:
    slope_mm_per_year: float
    ci95_low_mm_per_year: float
    ci95_high_mm_per_year: float


@dataclass(frozen=True)
class MannKendallResult:
    score: int
    variance: float
    z: float
    p_value: float
    alpha: float
    reject_null: bool  # Indicative only: the engine applies assumption gates.
    method: str
    method_version: str
    tied_groups: int


@dataclass(frozen=True)
class AssumptionDiagnostics:
    status: str
    lag_one_correlation: float | None
    ljung_box_q: float | None
    ljung_box_p_value: float | None
    diagnostic_alpha: float
    consecutive_pairs: int
    dependence_detected: bool | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class TrendResult:
    ols_slope_mm_per_year: float
    ols_intercept_mm: float
    ols_r_squared: float | None
    sen_slope_mm_per_year: float
    sen_ci95_low_mm_per_year: float
    sen_ci95_high_mm_per_year: float
    mann_kendall: MannKendallResult
    alpha: float
    significance_status: Literal["significant", "not_significant", "indeterminate"]
    assumptions_status: str
    n_complete_years: int
    analyzed_years: tuple[int, ...]
    excluded_years: tuple[int, ...]
    direction: Literal["increasing", "decreasing", "no_clear_direction"]
    diagnostics: AssumptionDiagnostics
    warnings: tuple[str, ...]
    algorithm_version: str
    scipy_version: str
    numpy_version: str

    @property
    def mann_kendall_p_value(self) -> float:
        return self.mann_kendall.p_value

    def statistics_payload(self) -> dict:
        """JSON-compatible mapping to the unchanged v1 Statistics schema."""
        return {
            "sample_years": self.n_complete_years,
            "ols_slope_mm_per_year": self.ols_slope_mm_per_year,
            "ols_r_squared": self.ols_r_squared,
            "sen_slope_mm_per_year": self.sen_slope_mm_per_year,
            "sen_slope_ci95_mm_per_year": [
                self.sen_ci95_low_mm_per_year,
                self.sen_ci95_high_mm_per_year,
            ],
            "mann_kendall_p_value": self.mann_kendall.p_value,
            "mann_kendall_method": self.mann_kendall.method,
            "alpha": self.alpha,
            "direction": self.direction,
            "significance_status": self.significance_status,
            "assumptions_status": self.assumptions_status,
        }


def prepare_annual(
    observations: Sequence[AnnualObservation],
    minimum: int = 2,
) -> tuple[AnnualObservation, ...]:
    if len(observations) < minimum:
        raise InsufficientDataError(len(observations), minimum)
    if len(observations) > MAX_YEARS:
        raise InvalidDataError("Annual series exceeds the 200-year resource limit.")
    if any(not isinstance(row, AnnualObservation) for row in observations):
        raise InvalidDataError("Expected AnnualObservation inputs.")
    rows = tuple(
        sorted(
            (AnnualObservation(r.year, r.total_mm) for r in observations),
            key=lambda r: r.year,
        )
    )
    if len({row.year for row in rows}) != len(rows):
        raise InvalidDataError("Duplicate calendar years are not permitted.")
    return rows
