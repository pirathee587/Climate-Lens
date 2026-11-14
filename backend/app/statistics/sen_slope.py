"""Theil–Sen annual slope and a fixed 95% slope confidence interval."""

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import theilslopes

from app.statistics.models import (
    AnnualObservation,
    NumericalAnalysisError,
    SenResult,
    prepare_annual,
)


def estimate_sen_slope(observations: Sequence[AnnualObservation]) -> SenResult:
    rows = prepare_annual(observations)
    if all(row.total_mm == rows[0].total_mm for row in rows):
        return SenResult(0.0, 0.0, 0.0)
    scale = max(row.total_mm for row in rows)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            fit = theilslopes(
                [r.total_mm / scale for r in rows], [r.year for r in rows], alpha=0.95
            )
            slope, low, high = (
                float(v * scale) for v in (fit.slope, fit.low_slope, fit.high_slope)
            )
    except (FloatingPointError, OverflowError, ValueError) as exc:
        raise NumericalAnalysisError("Sen slope computation failed.") from exc
    if (
        not all(math.isfinite(v) for v in (slope, low, high))
        or not low <= slope <= high
    ):
        raise NumericalAnalysisError("Sen slope interval is invalid or nonfinite.")
    return SenResult(slope, low, high)
