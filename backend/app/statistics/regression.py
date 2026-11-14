"""OLS annual precipitation trend, using actual calendar years."""

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import linregress

from app.statistics.models import (
    AnnualObservation,
    NumericalAnalysisError,
    OLSResult,
    prepare_annual,
)


def ordinary_least_squares(observations: Sequence[AnnualObservation]) -> OLSResult:
    rows = prepare_annual(observations)
    if all(row.total_mm == rows[0].total_mm for row in rows):
        # R² is undefined when total variance is zero, not a perfect explanatory fit.
        return OLSResult(0.0, rows[0].total_mm, None)
    x = np.array([r.year for r in rows], dtype=float)
    scale = max(r.total_mm for r in rows)
    y = np.array([r.total_mm / scale for r in rows], dtype=float)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            fit = linregress(x, y)
            slope, intercept, r_squared = (
                float(fit.slope * scale),
                float(fit.intercept * scale),
                float(fit.rvalue**2),
            )
    except (FloatingPointError, OverflowError, ValueError) as exc:
        raise NumericalAnalysisError("OLS computation failed.") from exc
    if (
        not all(math.isfinite(v) for v in (slope, intercept, r_squared))
        or not 0 <= r_squared <= 1
    ):
        raise NumericalAnalysisError("OLS returned invalid/nonfinite estimates.")
    return OLSResult(slope, intercept, r_squared)
