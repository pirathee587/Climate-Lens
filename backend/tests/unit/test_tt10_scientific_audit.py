"""TT-10 scientific data, conversion, OLS fitted values, and reproducibility tests.

All observations in this module are synthetic algorithm verification fixtures,
not NASA measurements.
"""

import math

import numpy as np
import pymannkendall as mk_ref
import pytest
from scipy import stats

from app.statistics import (
    AnnualObservation,
    InvalidDataError,
    MonthlyObservation,
    NumericalAnalysisError,
    QualityPolicy,
    analyze_annual_trend,
    audit_regional_trend,
    verify_annual_sum,
    verify_monthly_conversion,
)
from app.statistics.models import OLSResult


@pytest.mark.parametrize(
    ("period", "rate", "units", "expected_hours", "expected_mm"),
    [
        ("2024-02", 1.0, "mm/hr", 696, 696.0),  # ST-01 / TC-002 leap Feb
        ("2023-02", 1.0, "mm/hr", 672, 672.0),  # ST-02 / TC-001 non-leap Feb
        ("2024-01", 1.0, "mm/hr", 744, 744.0),  # 31-day month
        ("2024-04", 0.5, "mm/hr", 720, 360.0),  # 30-day month
        ("2024-02", 696.0, "mm", 696, 696.0),  # Already accumulated mm
        ("2024-02", 696.0, "mm/month", 696, 696.0),  # Already accumulated mm/month
    ],
)
def test_verify_monthly_conversion_spot_checks(
    period: str,
    rate: float,
    units: str,
    expected_hours: int,
    expected_mm: float,
) -> None:
    check = verify_monthly_conversion(period, rate, units, expected_mm)
    assert check.calendar_hours == expected_hours
    assert check.expected_total_mm == pytest.approx(expected_mm, abs=1e-12)
    assert check.abs_diff_mm <= 1e-12


def test_verify_monthly_conversion_rejects_double_conversion_and_bad_inputs() -> None:
    # Double-converting an already accumulated mm/month value must fail the audit
    with pytest.raises(InvalidDataError, match="Monthly spot-check failed"):
        verify_monthly_conversion("2024-02", 696.0, "mm/month", 696.0 * 696.0)

    # Wrong leap-year hour count (672 instead of 696 in Feb 2024) must fail
    with pytest.raises(InvalidDataError, match="Monthly spot-check failed"):
        verify_monthly_conversion("2024-02", 1.0, "mm/hr", 672.0)

    with pytest.raises(InvalidDataError, match="Unsupported source unit"):
        verify_monthly_conversion("2024-02", 1.0, "inches/day", 1.0)

    with pytest.raises(InvalidDataError, match="Period must be"):
        verify_monthly_conversion("2024-2", 1.0, "mm/hr", 696.0)


def test_verify_annual_sum_requires_twelve_valid_months() -> None:
    months = [100.1 * (m + 1) for m in range(12)]
    expected = math.fsum(months)
    check = verify_annual_sum(2024, months, expected)
    assert check.year == 2024
    assert check.expected_total_mm == pytest.approx(expected, abs=1e-12)
    assert check.abs_diff_mm == 0.0

    # 11-month incomplete year must be rejected (FR-008 / ST-03)
    with pytest.raises(InvalidDataError, match="requires 12 valid months"):
        verify_annual_sum(2024, months[:11], math.fsum(months[:11]))

    # Mismatched annual sum must fail
    with pytest.raises(InvalidDataError, match="Annual sum spot-check failed"):
        verify_annual_sum(2024, months, expected + 0.01)


def test_ols_fitted_values_and_series_on_trend_result() -> None:
    years = list(range(2010, 2022))
    rows = [
        AnnualObservation(
            year=y,
            total_mm=1000.0 + 12.5 * (y - 2010) + 18.0 * math.sin((y - 2010) * 1.3),
        )
        for y in years
    ]
    result = analyze_annual_trend(rows, excluded_years=(2009,))
    fitted_map = result.ols_fitted_series()

    assert list(fitted_map.keys()) == years
    for y in years:
        expected = result.ols_intercept_mm + result.ols_slope_mm_per_year * y
        assert result.ols_fitted_mm(y) == pytest.approx(expected, abs=1e-12)
        assert fitted_map[y] == pytest.approx(expected, abs=1e-12)

    # Excluded or unanalyzed years must be rejected
    with pytest.raises(InvalidDataError, match="analyzed complete years"):
        result.ols_fitted_mm(2009)
    with pytest.raises(InvalidDataError, match="analyzed complete years"):
        result.ols_fitted_mm(2030)

    # Overflowing OLS parameters must raise NumericalAnalysisError
    bad_ols = OLSResult(slope_mm_per_year=1e308, intercept_mm=1e308, r_squared=0.5)
    with pytest.raises(NumericalAnalysisError, match="nonfinite"):
        bad_ols.fitted_mm(2024)


def test_audit_regional_trend_end_to_end_reproducibility() -> None:
    monthly: list[MonthlyObservation] = []
    policy = QualityPolicy(
        accepted_quality_flags=frozenset({"valid"}), minimum_valid_fraction=0.9
    )

    for year in range(2011, 2024):
        for month in range(1, 13):
            period = f"{year:04d}-{month:02d}"
            # Make 2015 incomplete (missing April) to verify FR-008 exclusion
            if year == 2015 and month == 4:
                monthly.append(
                    MonthlyObservation(
                        region_id="jaffna_area",
                        period=period,
                        total_mm=None,
                        quality_flag="missing",
                        validity="missing",
                        valid_fraction=0.0,
                    )
                )
                continue
            val = (
                80.0
                + 1.8 * (year - 2011)
                + 12.0 * math.sin(month * 0.9 + 0.25 * (year - 2011) ** 2)
            )
            monthly.append(
                MonthlyObservation(
                    region_id="jaffna_area",
                    period=period,
                    total_mm=val,
                    quality_flag="valid",
                    validity="valid",
                    valid_fraction=0.98,
                )
            )

    audit = audit_regional_trend(
        monthly,
        policy=policy,
        year_range=(2011, 2023),
        alpha=0.05,
    )
    assert audit.region_id == "jaffna_area"
    assert audit.aggregation.excluded_years == (2015,)
    assert audit.trend.n_complete_years == 12
    assert 2015 not in audit.ols_fitted_by_year
    assert audit.annual_spot_check.year == 2011
    assert audit.annual_spot_check.abs_diff_mm <= 1e-12

    # Independent cross-check against SciPy and PyMannKendall
    x = np.array([obs.year for obs in audit.aggregation.observations], dtype=float)
    y = np.array([obs.total_mm for obs in audit.aggregation.observations], dtype=float)
    ols_ref = stats.linregress(x, y)
    sen_ref = stats.theilslopes(y, x, alpha=0.95)
    mk_out = mk_ref.original_test(y, alpha=0.05)

    assert audit.trend.ols_slope_mm_per_year == pytest.approx(
        float(ols_ref.slope), abs=1e-9
    )
    assert audit.trend.ols_r_squared == pytest.approx(
        float(ols_ref.rvalue**2), abs=1e-9
    )
    assert audit.trend.sen_slope_mm_per_year == pytest.approx(
        float(sen_ref.slope), abs=1e-9
    )
    assert audit.trend.sen_ci95_low_mm_per_year == pytest.approx(
        float(sen_ref.low_slope), abs=1e-9
    )
    assert audit.trend.sen_ci95_high_mm_per_year == pytest.approx(
        float(sen_ref.high_slope), abs=1e-9
    )
    assert audit.trend.mann_kendall_p_value == pytest.approx(float(mk_out.p), abs=1e-9)
