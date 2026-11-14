"""Aggregate already-normalized monthly totals; never perform rate conversion."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.statistics.models import (
    MAX_YEARS,
    AggregationResult,
    AnnualObservation,
    AnnualSummary,
    InvalidDataError,
    MonthlyObservation,
    checked_year,
    finite_number,
)


@dataclass(frozen=True)
class QualityPolicy:
    accepted_quality_flags: frozenset[str] = frozenset({"valid"})
    minimum_valid_fraction: float | None = None

    def __post_init__(self) -> None:
        if isinstance(self.accepted_quality_flags, str):
            raise InvalidDataError("Accepted quality flags must be a collection.")
        flags = frozenset(self.accepted_quality_flags)
        if not flags or any(
            not isinstance(flag, str) or not flag.strip() for flag in flags
        ):
            raise InvalidDataError(
                "Quality policy needs explicit nonempty accepted flags."
            )
        object.__setattr__(self, "accepted_quality_flags", flags)
        if self.minimum_valid_fraction is not None:
            fraction = finite_number(self.minimum_valid_fraction)
            if not 0 <= fraction <= 1:
                raise InvalidDataError("Coverage threshold must be in [0,1].")


def aggregate_annual_precipitation(
    observations: Sequence[MonthlyObservation],
    *,
    policy: QualityPolicy | None = None,
    year_range: tuple[int, int] | None = None,
) -> AggregationResult:
    if not observations or len(observations) > MAX_YEARS * 12:
        raise InvalidDataError("Expected 1–2400 normalized monthly observations.")
    policy = policy or QualityPolicy()
    monthly = {}
    regions = set()
    invalid_count = 0
    for row in observations:
        if not isinstance(row, MonthlyObservation):
            raise InvalidDataError("Expected MonthlyObservation inputs.")
        if not isinstance(row.region_id, str) or not row.region_id.strip():
            raise InvalidDataError("Region ID is required.")
        regions.add(row.region_id)
        if (
            not isinstance(row.period, str)
            or len(row.period) != 7
            or not row.period.isascii()
        ):
            raise InvalidDataError("Expected YYYY-MM monthly dates.")
        try:
            period = date.fromisoformat(row.period + "-01")
        except ValueError:
            raise InvalidDataError("Invalid monthly calendar date.") from None
        if row.period in monthly:
            raise InvalidDataError("Duplicate region-month observations.")
        if row.validity not in {"valid", "missing", "invalid"}:
            raise InvalidDataError("Unknown validity status.")
        if not isinstance(row.quality_flag, str) or not row.quality_flag.strip():
            raise InvalidDataError("Explicit source quality flag is required.")
        value = (
            None
            if row.total_mm is None
            else finite_number(row.total_mm, nonnegative=True)
        )
        fraction = (
            None if row.valid_fraction is None else finite_number(row.valid_fraction)
        )
        if fraction is not None and not 0 <= fraction <= 1:
            raise InvalidDataError("Coverage fraction must be in [0,1].")
        if row.validity == "missing" and value is not None:
            raise InvalidDataError("Missing measurement must have a null value.")
        valid = (
            value is not None
            and row.validity == "valid"
            and row.quality_flag in policy.accepted_quality_flags
            and (fraction is None or fraction > 0)
        )
        if policy.minimum_valid_fraction is not None:
            valid = (
                valid
                and fraction is not None
                and fraction >= policy.minimum_valid_fraction
            )
        if not valid:
            invalid_count += 1
        monthly[row.period] = (period.year, value if valid else None)
    if len(regions) != 1:
        raise InvalidDataError("Aggregate one region at a time.")
    years = [item[0] for item in monthly.values()]
    if year_range is not None and len(year_range) != 2:
        raise InvalidDataError("Year range requires exactly two bounds.")
    start, end = (
        (min(years), max(years))
        if year_range is None
        else tuple(checked_year(y) for y in year_range)
    )
    if (
        start > end
        or end - start + 1 > MAX_YEARS
        or min(years) < start
        or max(years) > end
    ):
        raise InvalidDataError("Invalid or out-of-bounds aggregation year range.")
    complete, summaries, excluded, missing, warnings = [], [], [], [], []
    for year in range(start, end + 1):
        values = []
        for month in range(1, 13):
            key = f"{year:04d}-{month:02d}"
            if key not in monthly:
                missing.append(key)
            elif monthly[key][1] is not None:
                values.append(monthly[key][1])
        total = None
        if len(values) == 12:
            try:
                total = math.fsum(values)
            except OverflowError:
                raise InvalidDataError("Annual precipitation total overflow.") from None
            if not math.isfinite(total):
                raise InvalidDataError("Annual precipitation total is not finite.")
            complete.append(AnnualObservation(year, total))
        else:
            excluded.append(year)
            warnings.append(f"Excluded {year}: {len(values)}/12 valid monthly totals.")
        summaries.append(AnnualSummary(year, total, len(values)))
    if invalid_count:
        warnings.append(
            f"{invalid_count} months excluded by validity/quality/missing-data policy."
        )
    return AggregationResult(
        next(iter(regions)),
        tuple(complete),
        tuple(summaries),
        tuple(excluded),
        tuple(missing),
        tuple(warnings),
    )
