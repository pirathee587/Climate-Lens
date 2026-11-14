"""All numeric signals are synthetic unit checks, never NASA observations."""

import pytest

from app.data.imerg_processor import normalize_precipitation
from app.data.snapshot_loader import load_source
from tests.unit.data_fixtures import SYNTHETIC_SOURCE, synthetic_recipe


@pytest.mark.parametrize(
    "period,expected", [("2023-02", 672), ("2024-02", 696), ("2024-01", 744)]
)
def test_actual_calendar_conversion(period, expected):
    assert normalize_precipitation(1, period, "mm/hr") == expected


@pytest.mark.parametrize("unit", ["mm", "mm/month"])
def test_accumulated_values_never_double_converted(unit):
    assert normalize_precipitation(123.5, "2024-02", unit) == 123.5


@pytest.mark.parametrize("value", [None, -9999])
def test_declared_fill_stays_missing(value):
    assert normalize_precipitation(value, "2024-02", "mm/hr", (-9999,)) is None


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), -float("inf"), True])
def test_invalid_precipitation(value):
    with pytest.raises(ValueError):
        normalize_precipitation(value, "2024-02", "mm/hr")


@pytest.mark.parametrize(
    "period", ["2023-13", "2023-00", "0000-01", "2023-2", "bad", "2023-02-01"]
)
def test_invalid_dates(period):
    with pytest.raises(ValueError):
        normalize_precipitation(1, period, "mm")


def test_invalid_units_and_overflow():
    with pytest.raises(ValueError):
        normalize_precipitation(1, "2024-02", "kg")
    with pytest.raises(ValueError):
        normalize_precipitation(1e308, "2024-02", "mm/hr")


def test_sorted_source_preserves_coverage_quality_and_nulls():
    source = (
        b"period,rate,fraction,quality\n"
        b"2024-02,-9999,,synthetic-missing\n2023-02,1,0.25,synthetic-valid\n"
    )
    rows = load_source(source, synthetic_recipe(fill_values=(-9999,)))
    assert [r.period for r in rows] == ["2023-02", "2024-02"]
    assert rows[0].precipitation_total_mm == 672
    assert rows[0].valid_fraction == 0.25
    assert rows[1].precipitation_total_mm is None
    assert rows[1].valid_fraction is None
    assert rows[1].quality_flag == "synthetic-missing"


@pytest.mark.parametrize(
    "source",
    [
        b"period,rate,fraction,quality\n2023-02,1,,test\n2023-02,2,,test\n",
        b"period,rate,fraction,quality\n2023-02,NaN,,test\n",
        b"period,rate,fraction,quality\n2023-02,Infinity,,test\n",
        b"period,rate,fraction,quality\n2023-02,-1,,test\n",
        b"period,rate,fraction,quality\n2023-02,1,1.1,test\n",
        b"period,rate,fraction,quality\n2023-30,1,,test\n",
        b"period,rate,rate\n2023-02,1,1\n",
        b"period,rate,fraction,quality\n2023-02,1\n",
        b"period,rate,fraction,quality\n2023-02,1,,test,extra\n",
        b"other\n1\n",
        b"period,rate,fraction,quality\n",
    ],
)
def test_corrupt_source_rejected(source):
    with pytest.raises(ValueError):
        load_source(source, synthetic_recipe())


def test_bounded_source_and_row_count():
    from app.data.manifest_builder import MAX_MONTHS, MAX_SOURCE_BYTES

    with pytest.raises(ValueError):
        load_source(b"x" * (MAX_SOURCE_BYTES + 1), synthetic_recipe())
    source = (
        b"period,rate,fraction,quality\n"
        + "".join(
            f"{1800 + index // 12:04d}-{index % 12 + 1:02d},1,,synthetic\n"
            for index in range(MAX_MONTHS + 1)
        ).encode()
    )
    with pytest.raises(ValueError):
        load_source(source, synthetic_recipe())


def test_explicit_header_and_date_mapping():
    source = (
        b"SYNTHETIC header metadata\nperiod,rate,fraction,quality\n2024-02-15,1,,test\n"
    )
    rows = load_source(
        source, synthetic_recipe(skip_header_lines=1, period_format="%Y-%m-%d")
    )
    assert rows[0].period == "2024-02"
    assert rows[0].precipitation_total_mm == 696


def test_identity_source_units_preserved():
    rows = load_source(SYNTHETIC_SOURCE, synthetic_recipe(original_units="mm"))
    assert [r.precipitation_total_mm for r in rows] == [1, 1]
