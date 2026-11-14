"""Synthetic normalized monthly totals; not NASA observations."""

import pytest

from app.statistics import (
    InvalidDataError,
    MonthlyObservation,
    QualityPolicy,
    aggregate_annual_precipitation,
)


def months(year=2024, value=1):
    return [
        MonthlyObservation("synthetic", f"{year}-{m:02d}", value, "valid")
        for m in range(1, 13)
    ]


def test_complete_year_and_no_double_conversion():
    result = aggregate_annual_precipitation(months(value=10)[::-1])
    assert result.observations[0].total_mm == 120
    assert result.year_summaries[0].valid_months == 12
    values = months(value=0)
    values[1] = MonthlyObservation("synthetic", "2024-02", 696, "valid")
    assert aggregate_annual_precipitation(values).observations[0].total_mm == 696


def test_missing_april_and_wholly_missing_years():
    values = [r for r in months() if r.period != "2024-04"]
    result = aggregate_annual_precipitation(values)
    assert result.observations == ()
    assert result.excluded_years == (2024,)
    assert result.missing_periods == ("2024-04",)
    assert result.year_summaries[0].total_mm is None
    assert result.year_summaries[0].valid_months == 11
    assert "11/12" in result.warnings[0]
    result = aggregate_annual_precipitation(
        months(2022) + months(2024), year_range=(2021, 2024)
    )
    assert result.excluded_years == (2021, 2023)
    assert [r.valid_months for r in result.year_summaries] == [0, 12, 0, 12]


@pytest.mark.parametrize(
    "replacement",
    [
        MonthlyObservation("synthetic", "2024-04", None, "missing", "missing"),
        MonthlyObservation("synthetic", "2024-04", 12, "invalid", "invalid"),
        MonthlyObservation("synthetic", "2024-04", 12, "unknown_source_flag"),
    ],
)
def test_missing_invalid_and_unknown_quality_exclude_month(replacement):
    values = months()
    values[3] = replacement
    result = aggregate_annual_precipitation(values)
    assert result.year_summaries[0].valid_months == 11
    assert result.year_summaries[0].total_mm is None


def test_explicit_quality_and_coverage_policy():
    policy = QualityPolicy(frozenset({"source_checked"}), minimum_valid_fraction=0.8)
    values = [
        MonthlyObservation(
            "synthetic", r.period, 1, "source_checked", valid_fraction=0.9
        )
        for r in months()
    ]
    assert (
        aggregate_annual_precipitation(values, policy=policy).observations[0].total_mm
        == 12
    )
    values[0] = MonthlyObservation("synthetic", "2024-01", 1, "source_checked")
    assert aggregate_annual_precipitation(values, policy=policy).excluded_years == (
        2024,
    )


@pytest.mark.parametrize(
    "period", ["2024-13", "2024-2", "0000-01", "bad", "2024-01-01"]
)
def test_invalid_dates(period):
    with pytest.raises(InvalidDataError):
        aggregate_annual_precipitation(
            [MonthlyObservation("synthetic", period, 1, "valid")]
        )


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), -float("inf"), -1, True, "1"]
)
def test_invalid_numbers(value):
    with pytest.raises(InvalidDataError):
        aggregate_annual_precipitation(
            [MonthlyObservation("synthetic", "2024-01", value, "valid")]
        )


def test_duplicate_mixed_empty_and_invalid_metadata():
    for values in [
        [],
        months() + [months()[0]],
        months() + [MonthlyObservation("other", "2025-01", 1, "valid")],
        [MonthlyObservation("synthetic", "2024-01", 1, "valid", "missing")],
        [MonthlyObservation("synthetic", "2024-01", 1, "valid", valid_fraction=1.1)],
    ]:
        with pytest.raises(InvalidDataError):
            aggregate_annual_precipitation(values)
    with pytest.raises(InvalidDataError):
        QualityPolicy(minimum_valid_fraction=-0.1)
    with pytest.raises(InvalidDataError):
        aggregate_annual_precipitation(months(), year_range=(2025, 2024))
    with pytest.raises(InvalidDataError):
        aggregate_annual_precipitation(months(value=1e308))


def test_zero_coverage_and_invalid_range_shape():
    values = months()
    values[0] = MonthlyObservation("synthetic", "2024-01", 1, "valid", valid_fraction=0)
    assert aggregate_annual_precipitation(values).year_summaries[0].valid_months == 11
    with pytest.raises(InvalidDataError):
        aggregate_annual_precipitation(months(), year_range=(2024,))
    with pytest.raises(InvalidDataError):
        QualityPolicy("valid")
