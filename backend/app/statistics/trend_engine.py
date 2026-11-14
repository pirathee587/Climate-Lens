"""Pure annual trend orchestration; no FastAPI, source loading or network calls."""

from collections.abc import Sequence

import numpy as np
import scipy

from app.statistics.diagnostics import assess_assumptions
from app.statistics.mann_kendall import mann_kendall
from app.statistics.models import (
    MIN_COMPLETE_YEARS,
    AnnualObservation,
    InvalidDataError,
    TrendResult,
    checked_alpha,
    checked_year,
    prepare_annual,
)
from app.statistics.regression import ordinary_least_squares
from app.statistics.sen_slope import estimate_sen_slope

ALGORITHM_VERSION = "terratrend-annual-trend-v1"


def analyze_annual_trend(
    observations: Sequence[AnnualObservation],
    alpha: float = 0.05,
    *,
    excluded_years: Sequence[int] = (),
    diagnostic_alpha: float = 0.05,
) -> TrendResult:
    alpha = checked_alpha(alpha)
    rows = prepare_annual(observations, MIN_COMPLETE_YEARS)
    excluded = tuple(sorted(checked_year(year) for year in excluded_years))
    years = tuple(row.year for row in rows)
    if len(set(excluded)) != len(excluded) or set(excluded).intersection(years):
        raise InvalidDataError(
            "Excluded years must be unique and outside analyzed years."
        )
    ols = ordinary_least_squares(rows)
    sen = estimate_sen_slope(rows)
    mk = mann_kendall(rows, alpha)
    diagnostics = assess_assumptions(rows, ols, diagnostic_alpha=diagnostic_alpha)
    status = "indeterminate"
    if diagnostics.status == "not_rejected_by_lag1_screen":
        status = "significant" if mk.reject_null else "not_significant"
    direction = (
        "increasing"
        if sen.slope_mm_per_year > 0
        else "decreasing"
        if sen.slope_mm_per_year < 0
        else "no_clear_direction"
    )
    warnings = list(diagnostics.warnings)
    if mk.tied_groups:
        warnings.append(
            "Tied annual totals: MK variance includes exact-value tie correction."
        )
    if excluded:
        warnings.append(
            "Incomplete/invalid years excluded: " + ", ".join(map(str, excluded))
        )
    warnings.append("MK uses a tie/continuity-corrected normal approximation.")
    warnings.append(
        "Sen 95% interval is nominal, without serial-dependence correction."
    )
    warnings.append(
        "Exploratory trends do not establish causation or environmental importance."
    )
    return TrendResult(
        ols.slope_mm_per_year,
        ols.intercept_mm,
        ols.r_squared,
        sen.slope_mm_per_year,
        sen.ci95_low_mm_per_year,
        sen.ci95_high_mm_per_year,
        mk,
        alpha,
        status,
        diagnostics.status,
        len(rows),
        years,
        excluded,
        direction,
        diagnostics,
        tuple(warnings),
        ALGORITHM_VERSION,
        scipy.__version__,
        np.__version__,
    )
