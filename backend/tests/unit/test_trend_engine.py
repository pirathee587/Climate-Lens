"""Synthetic scientific interface validation, not real NASA observations."""

import json
from dataclasses import asdict

import numpy as np
import pytest
from scipy.stats import chi2

from app.schemas.analysis import Statistics
from app.statistics import (
    AnnualObservation,
    InsufficientDataError,
    InvalidDataError,
    MonthlyObservation,
    aggregate_annual_precipitation,
    analyze_annual_trend,
)
from app.statistics.diagnostics import assess_assumptions
from app.statistics.regression import ordinary_least_squares


def noisy_rows(slope=10):
    noise = np.random.default_rng(42).normal(0, 5, 40)
    return tuple(
        AnnualObservation(2000 + i, 1000 + slope * i + float(v))
        for i, v in enumerate(noise)
    )


@pytest.mark.parametrize("slope,direction", [(10, "increasing"), (-5, "decreasing")])
def test_known_trend_and_unassessable_perfect_residuals(slope, direction):
    result = analyze_annual_trend(
        tuple(
            AnnualObservation(y, 1500 + slope * (y - 2000)) for y in range(2001, 2025)
        )
    )
    assert result.ols_slope_mm_per_year == pytest.approx(slope)
    assert result.sen_slope_mm_per_year == pytest.approx(slope)
    assert result.direction == direction
    assert result.significance_status == "indeterminate"
    assert result.diagnostics.lag_one_correlation is None


def test_successful_noisy_trend_reproducibility_and_schema_mapping():
    source = noisy_rows()
    result = analyze_annual_trend(source)
    assert result == analyze_annual_trend(tuple(reversed(source)))
    assert result.significance_status == "significant"
    assert result.assumptions_status == "not_rejected_by_lag1_screen"
    assert result.analyzed_years == tuple(range(2000, 2040))
    assert result.n_complete_years == 40
    assert (
        Statistics.model_validate(result.statistics_payload()).significance_status
        == "significant"
    )
    json.dumps(asdict(result), allow_nan=False)
    assert result.numpy_version and result.scipy_version and result.algorithm_version
    assert any("causation" in warning for warning in result.warnings)


def test_nonsignificant_noise_and_constant_series():
    result = analyze_annual_trend(noisy_rows(slope=0))
    assert result.significance_status == "not_significant"
    assert result.mann_kendall.p_value >= result.alpha
    constant = analyze_annual_trend(
        tuple(AnnualObservation(y, 1000) for y in range(2000, 2024))
    )
    assert constant.ols_r_squared is None
    assert constant.sen_slope_mm_per_year == 0
    assert constant.direction == "no_clear_direction"
    assert constant.significance_status == "indeterminate"
    assert constant.mann_kendall.p_value == 1
    json.dumps(asdict(constant), allow_nan=False)


def test_gapped_years_preserve_calendar_spacing_and_metadata():
    years = [2000, 2001, 2003, 2004, 2007, 2008, 2010, 2012, 2014, 2018]
    result = analyze_annual_trend(
        tuple(AnnualObservation(y, 500 + 10 * (y - 2000)) for y in years),
        excluded_years=(2002, 2005),
    )
    assert result.sen_slope_mm_per_year == pytest.approx(10)
    assert result.ols_slope_mm_per_year == pytest.approx(10)
    assert result.analyzed_years == tuple(years)
    assert result.excluded_years == (2002, 2005)
    assert result.significance_status == "indeterminate"
    assert result.diagnostics.ljung_box_p_value is None


def test_insufficient_years_raise_traceable_exception():
    with pytest.raises(InsufficientDataError) as error:
        analyze_annual_trend(
            tuple(AnnualObservation(y, 500) for y in range(2000, 2004))
        )
    assert (error.value.minimum, error.value.available) == (10, 4)


def test_incomplete_year_handoff():
    monthly = [
        MonthlyObservation("synthetic", f"{y}-{m:02d}", 10, "valid")
        for y in range(2000, 2012)
        for m in range(1, 13)
        if (y, m) != (2005, 4)
    ]
    aggregation = aggregate_annual_precipitation(monthly)
    result = analyze_annual_trend(
        aggregation.observations, excluded_years=aggregation.excluded_years
    )
    assert result.n_complete_years == 11
    assert result.excluded_years == (2005,)
    assert 2005 not in result.analyzed_years


@pytest.mark.parametrize("pattern", ["positive", "negative"])
def test_serial_dependence_blocks_indicative_mk_rejection(pattern):
    source = tuple(
        AnnualObservation(
            2000 + i,
            1000 + 5 * i + 20 * (np.sin(i / 4) if pattern == "positive" else (-1) ** i),
        )
        for i in range(60)
    )
    result = analyze_annual_trend(source)
    assert result.mann_kendall.reject_null
    assert result.diagnostics.dependence_detected
    assert result.diagnostics.ljung_box_p_value < result.diagnostics.diagnostic_alpha
    assert result.significance_status == "indeterminate"


def test_ljung_box_statistic_independent_formula():
    source = noisy_rows()
    ols = ordinary_least_squares(source)
    diagnostic = assess_assumptions(source, ols)
    x, y = [r.year for r in source], [r.total_mm for r in source]
    mx, my = sum(x) / len(x), sum(y) / len(y)
    residual = [
        b - my - ols.slope_mm_per_year * (a - mx) for a, b in zip(x, y, strict=True)
    ]
    r1 = sum(a * b for a, b in zip(residual[:-1], residual[1:], strict=True)) / sum(
        v * v for v in residual
    )
    q = len(source) * (len(source) + 2) * r1**2 / (len(source) - 1)
    assert diagnostic.lag_one_correlation == pytest.approx(r1)
    assert diagnostic.ljung_box_q == pytest.approx(q)
    assert diagnostic.ljung_box_p_value == pytest.approx(chi2.sf(q, 1))


@pytest.mark.parametrize("alpha", [0, 1, -0.1, float("nan"), float("inf"), True])
def test_public_alpha_validation(alpha):
    with pytest.raises(InvalidDataError):
        analyze_annual_trend(noisy_rows(), alpha)


def test_excluded_year_consistency():
    for excluded in [(2000,), (1999, 1999)]:
        with pytest.raises(InvalidDataError):
            analyze_annual_trend(noisy_rows(), excluded_years=excluded)


def test_alpha_override_keeps_fixed_sen95_and_ten_year_minimum():
    low = analyze_annual_trend(noisy_rows(), alpha=0.01)
    high = analyze_annual_trend(noisy_rows(), alpha=0.1)
    assert (low.sen_ci95_low_mm_per_year, low.sen_ci95_high_mm_per_year) == (
        high.sen_ci95_low_mm_per_year,
        high.sen_ci95_high_mm_per_year,
    )
    assert low.mann_kendall.alpha == 0.01
    assert high.mann_kendall.alpha == 0.1
    assert low.diagnostics.diagnostic_alpha == high.diagnostics.diagnostic_alpha == 0.05
    short = analyze_annual_trend(noisy_rows()[:10])
    assert short.n_complete_years == 10
    assert any("Short record" in warning for warning in short.warnings)
