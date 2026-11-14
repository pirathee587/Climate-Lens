"""TT-10 scientific data and reproducibility audit functions (pure Python, no I/O)."""

import calendar
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.statistics.annual_aggregation import (
    QualityPolicy,
    aggregate_annual_precipitation,
)
from app.statistics.models import (
    AggregationResult,
    InvalidDataError,
    MonthlyObservation,
    TrendResult,
    checked_year,
    finite_number,
)
from app.statistics.trend_engine import analyze_annual_trend

SUPPORTED_SOURCE_UNITS = frozenset({"mm/hr", "mm", "mm/month"})
DEFAULT_POLICY = QualityPolicy()


@dataclass(frozen=True)
class MonthlySpotCheck:
    period: str
    original_units: str
    calendar_hours: int
    expected_total_mm: float
    reported_total_mm: float
    abs_diff_mm: float


@dataclass(frozen=True)
class AnnualSumSpotCheck:
    year: int
    expected_total_mm: float
    reported_total_mm: float
    abs_diff_mm: float


@dataclass(frozen=True)
class RegionScientificAudit:
    region_id: str
    annual_spot_check: AnnualSumSpotCheck
    aggregation: AggregationResult
    trend: TrendResult
    ols_fitted_by_year: dict[int, float]


def _parse_period(period: str) -> tuple[int, int]:
    if not isinstance(period, str) or len(period) != 7 or not period.isascii():
        raise InvalidDataError("Period must be an ASCII YYYY-MM string.")
    try:
        parsed = date.fromisoformat(f"{period}-01")
    except ValueError as exc:
        raise InvalidDataError("Invalid calendar period.") from exc
    return parsed.year, parsed.month


def verify_monthly_conversion(
    period: str,
    raw_value: float,
    original_units: str,
    reported_total_mm: float,
    *,
    tolerance: float = 1e-9,
) -> MonthlySpotCheck:
    """Verify FR-007 monthly conversion without double-converting accumulated mm."""
    year, month = _parse_period(period)
    if original_units not in SUPPORTED_SOURCE_UNITS:
        raise InvalidDataError(f"Unsupported source unit: {original_units!r}.")
    raw_num = finite_number(raw_value, nonnegative=True)
    rep_num = finite_number(reported_total_mm, nonnegative=True)
    tol = finite_number(tolerance, nonnegative=True)

    days_in_month = calendar.monthrange(year, month)[1]
    hours = 24 * days_in_month
    expected = raw_num * hours if original_units == "mm/hr" else raw_num
    if not math.isfinite(expected):
        raise InvalidDataError("Converted monthly total overflowed.")
    diff = abs(expected - rep_num)
    if diff > tol:
        raise InvalidDataError(
            f"Monthly spot-check failed for {period}: "
            f"expected {expected}, got {rep_num}."
        )
    return MonthlySpotCheck(
        period=period,
        original_units=original_units,
        calendar_hours=hours,
        expected_total_mm=float(expected),
        reported_total_mm=rep_num,
        abs_diff_mm=float(diff),
    )


def verify_annual_sum(
    year: int,
    monthly_totals_mm: Sequence[float],
    reported_total_mm: float,
    *,
    tolerance: float = 1e-9,
) -> AnnualSumSpotCheck:
    """Verify FR-008 complete 12-month summation using math.fsum."""
    checked = checked_year(year)
    if len(monthly_totals_mm) != 12:
        raise InvalidDataError(
            f"Complete-year verification requires 12 valid months; "
            f"got {len(monthly_totals_mm)}."
        )
    cleaned = [finite_number(v, nonnegative=True) for v in monthly_totals_mm]
    rep_num = finite_number(reported_total_mm, nonnegative=True)
    tol = finite_number(tolerance, nonnegative=True)

    expected = math.fsum(cleaned)
    if not math.isfinite(expected):
        raise InvalidDataError("Annual sum overflowed.")
    diff = abs(expected - rep_num)
    if diff > tol:
        raise InvalidDataError(
            f"Annual sum spot-check failed for {checked}: "
            f"expected {expected}, got {rep_num}."
        )
    return AnnualSumSpotCheck(
        year=checked,
        expected_total_mm=float(expected),
        reported_total_mm=rep_num,
        abs_diff_mm=float(diff),
    )


def audit_regional_trend(
    monthly: Sequence[MonthlyObservation],
    *,
    policy: QualityPolicy = DEFAULT_POLICY,
    year_range: tuple[int, int] | None = None,
    alpha: float = 0.05,
    diagnostic_alpha: float = 0.05,
) -> RegionScientificAudit:
    """Run TT-10 aggregation, trend analysis, and guardrail invariant checks."""
    aggregation = aggregate_annual_precipitation(
        monthly, policy=policy, year_range=year_range
    )
    trend = analyze_annual_trend(
        aggregation.observations,
        alpha=alpha,
        excluded_years=aggregation.excluded_years,
        diagnostic_alpha=diagnostic_alpha,
    )

    # Spot-check the first complete year's 12-month sum against the raw monthly input
    first_complete = aggregation.observations[0]
    eligible_flags = policy.accepted_quality_flags
    min_cov = policy.minimum_valid_fraction
    first_year_prefix = f"{first_complete.year:04d}-"
    first_year_months = [
        row.total_mm
        for row in monthly
        if row.period.startswith(first_year_prefix)
        and row.validity == "valid"
        and row.total_mm is not None
        and row.quality_flag in eligible_flags
        and (min_cov is None or (row.valid_fraction or 0.0) >= min_cov)
    ]
    spot_check = verify_annual_sum(
        first_complete.year, first_year_months, first_complete.total_mm
    )

    # Verify scientific guardrail invariants (FR-013, FR-014, FR-022)
    if (
        trend.assumptions_status != "not_rejected_by_lag1_screen"
        and trend.significance_status != "indeterminate"
    ):
        raise InvalidDataError(
            "Invalid assumption status must classify significance as indeterminate."
        )
    if not any("causation" in w.lower() for w in trend.warnings):
        raise InvalidDataError("Missing mandatory non-causation warning.")

    return RegionScientificAudit(
        region_id=aggregation.region_id,
        annual_spot_check=spot_check,
        aggregation=aggregation,
        trend=trend,
        ols_fitted_by_year=trend.ols_fitted_series(),
    )
