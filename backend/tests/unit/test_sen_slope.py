"""Synthetic pairwise-median and trusted SciPy confidence-bound references."""

import itertools
import statistics

import pytest
from scipy.stats import theilslopes

from app.statistics import AnnualObservation
from app.statistics.sen_slope import estimate_sen_slope


@pytest.mark.parametrize("slope,base", [(10, 500), (-5, 1500), (0, 100)])
def test_exact_slopes_and_calendar_spacing(slope, base):
    result = estimate_sen_slope(
        [
            AnnualObservation(y, base + slope * (y - 2000))
            for y in [2001, 2003, 2008, 2015]
        ]
    )
    assert result.slope_mm_per_year == pytest.approx(slope)
    assert result.ci95_low_mm_per_year == pytest.approx(slope)
    assert result.ci95_high_mm_per_year == pytest.approx(slope)


def test_pairwise_median_and_confidence_reference():
    x, y = [2001, 2002, 2004, 2008, 2010, 2013], [10, 15, 12, 28, 25, 42]
    rows = [AnnualObservation(a, b) for a, b in zip(x, y, strict=True)]
    median = statistics.median(
        (b.total_mm - a.total_mm) / (b.year - a.year)
        for a, b in itertools.combinations(rows, 2)
    )
    expected = theilslopes(y, x, alpha=0.95)
    result = estimate_sen_slope(rows[::-1])
    assert result.slope_mm_per_year == pytest.approx(median)
    assert result.ci95_low_mm_per_year == pytest.approx(expected.low_slope)
    assert result.ci95_high_mm_per_year == pytest.approx(expected.high_slope)
    assert (
        result.ci95_low_mm_per_year
        <= result.slope_mm_per_year
        <= result.ci95_high_mm_per_year
    )
