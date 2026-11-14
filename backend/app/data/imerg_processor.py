"""Monthly normalization only; no statistical trend calculations."""

import calendar
import math
from datetime import date


def parse_period(period: str) -> tuple[int, int]:
    if len(period) != 7 or not period.isascii():
        raise ValueError("expected YYYY-MM period")
    parsed = date.fromisoformat(period + "-01")
    return parsed.year, parsed.month


def normalize_precipitation(
    value: float | None,
    period: str,
    units: str,
    fill_values: tuple[float, ...] = (),
) -> float | None:
    year, month = parse_period(period)
    if units not in {"mm/hr", "mm", "mm/month"}:
        raise ValueError("unsupported source units")
    value = checked_value(value, fill_values)
    if value is None:
        return None
    total = (
        value * 24 * calendar.monthrange(year, month)[1] if units == "mm/hr" else value
    )
    if not math.isfinite(total):
        raise ValueError("normalization overflow")
    return total


def checked_value(
    value: float | None,
    fill_values: tuple[float, ...] = (),
) -> float | None:
    """Validate decoded native values before spatial or temporal processing."""
    if any(not math.isfinite(fill) for fill in fill_values):
        raise ValueError("fill values must be finite explicit metadata")
    if value is None or value in fill_values:
        return None
    if isinstance(value, bool) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid precipitation observation")
    return value
