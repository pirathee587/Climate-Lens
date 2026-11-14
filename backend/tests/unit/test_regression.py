"""Synthetic known-line and independent SciPy OLS reference tests."""

import math

import pytest
from scipy.stats import linregress

from app.statistics import (
    AnnualObservation,
    InsufficientDataError,
    InvalidDataError,
    NumericalAnalysisError,
)
from app.statistics.regression import ordinary_least_squares


@pytest.mark.parametrize("slope,base", [(10, 500), (-5, 1500)])
def test_known_calendar_slopes(slope, base):
    rows = [
        AnnualObservation(y, base + slope * (y - 2000))
        for y in [2001, 2003, 2008, 2015]
    ]
    result = ordinary_least_squares(rows[::-1])
    assert result.slope_mm_per_year == pytest.approx(slope)
    assert result.intercept_mm == pytest.approx(base - slope * 2000)
    assert result.r_squared == pytest.approx(1)


def test_noisy_reference_and_constant_series():
    x, y = [2001, 2002, 2005, 2006, 2010], [10, 15, 12, 18, 25]
    expected = linregress(x, y)
    result = ordinary_least_squares(
        [AnnualObservation(a, b) for a, b in zip(x, y, strict=True)]
    )
    assert result.slope_mm_per_year == pytest.approx(expected.slope)
    assert result.intercept_mm == pytest.approx(expected.intercept)
    assert result.r_squared == pytest.approx(expected.rvalue**2)
    constant = ordinary_least_squares(
        [AnnualObservation(y, 100) for y in range(2001, 2010)]
    )
    assert constant.slope_mm_per_year == 0
    assert constant.r_squared is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True])
def test_invalid_annual_numbers(value):
    with pytest.raises(InvalidDataError):
        AnnualObservation(2000, value)


def test_duplicates_sizes_and_year_types():
    with pytest.raises(InvalidDataError):
        ordinary_least_squares([AnnualObservation(2000, 1), AnnualObservation(2000, 2)])
    with pytest.raises(InsufficientDataError):
        ordinary_least_squares([AnnualObservation(2000, 1)])
    for year in [True, 2000.0, "2000", 0, 10000]:
        with pytest.raises(InvalidDataError):
            AnnualObservation(year, 1)
    with pytest.raises(InvalidDataError):
        ordinary_least_squares([AnnualObservation(y, 1) for y in range(1800, 2001)])


def test_numerical_instability_raises_instead_of_fallback():
    with pytest.raises(NumericalAnalysisError):
        ordinary_least_squares(
            [AnnualObservation(9998, 0), AnnualObservation(9999, 1e308)]
        )
    result = ordinary_least_squares(
        [AnnualObservation(2000, 1e300), AnnualObservation(2001, 1.01e300)]
    )
    assert math.isfinite(result.slope_mm_per_year)
