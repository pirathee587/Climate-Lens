"""Exploratory lag-one screen on OLS-detrended residuals; not an independence proof."""

from collections.abc import Sequence

import numpy as np
from scipy.stats import chi2

from app.statistics.models import (
    AnnualObservation,
    AssumptionDiagnostics,
    OLSResult,
    checked_alpha,
    prepare_annual,
)


def assess_assumptions(
    observations: Sequence[AnnualObservation],
    ols: OLSResult,
    *,
    diagnostic_alpha: float = 0.05,
) -> AssumptionDiagnostics:
    rows = prepare_annual(observations)
    threshold = checked_alpha(diagnostic_alpha)
    n = len(rows)
    pairs = sum(b.year == a.year + 1 for a, b in zip(rows, rows[1:], strict=False))
    warnings = [
        "Lag-one screening cannot establish independence or assess higher lags.",
        "Source quality, processing breaks and causes need separate review.",
    ]
    if n < 20:
        warnings.append(
            "Short record (<20 years): inference and diagnostics have limited power."
        )
    if pairs != n - 1:
        warnings.append(
            "Gapped calendar years: lag-one screening is unavailable; p is indicative."
        )
        return AssumptionDiagnostics(
            "not_evaluated_gapped_years",
            None,
            None,
            None,
            threshold,
            pairs,
            None,
            tuple(warnings),
        )
    # Scale before subtraction/squaring; trend removal uses actual calendar years.
    scale = max(row.total_mm for row in rows) or 1.0
    x = np.array([row.year for row in rows], dtype=float)
    y = np.array([row.total_mm / scale for row in rows], dtype=float)
    residual = y - (ols.slope_mm_per_year / scale) * (x - x.mean()) - y.mean()
    residual -= residual.mean()
    if np.max(np.abs(residual)) <= 16 * np.finfo(float).eps:
        warnings.append(
            "Constant/exact linear series: residual dependence is unassessable."
        )
        return AssumptionDiagnostics(
            "not_evaluated_zero_residual_variance",
            None,
            None,
            None,
            threshold,
            pairs,
            None,
            tuple(warnings),
        )
    correlation = float(
        np.dot(residual[1:], residual[:-1]) / np.dot(residual, residual)
    )
    q = n * (n + 2) * correlation**2 / (n - 1)
    p_value = float(chi2.sf(q, df=1))
    detected = p_value < threshold
    warnings.append(
        "Ljung-Box residual screening is approximate after linear detrending."
    )
    if detected:
        warnings.append(
            "Residual dependence flagged; MK significance is indeterminate."
        )
    return AssumptionDiagnostics(
        "serial_dependence_flagged" if detected else "not_rejected_by_lag1_screen",
        correlation,
        q,
        p_value,
        threshold,
        pairs,
        detected,
        tuple(warnings),
    )
