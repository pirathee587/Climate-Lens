"""All numerical/geographical inputs here are synthetic validation fixtures."""

import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.analysis import (
    AnalysisRequest,
    AnnualItem,
    ComparisonRequest,
    MonthlyItem,
    Statistics,
)
from app.schemas.source import RegionDescriptor, SourceDescriptor

BASE = dict(
    variable_id="precipitation",
    region_id="synthetic_test_region",
    start_year=2001,
    end_year=2002,
)


@pytest.mark.parametrize(
    "field,value",
    [
        ("alpha", 0),
        ("alpha", 1),
        ("alpha", -0.01),
        ("alpha", float("nan")),
        ("alpha", float("inf")),
        ("end_year", 2000),
        ("source_mode", "live"),
        ("variable_id", "temperature"),
        ("start_year", "2001"),
        ("start_year", 2001.5),
        ("start_year", True),
        ("region_id", ""),
    ],
)
def test_invalid_analysis_requests(field, value):
    with pytest.raises(ValidationError):
        AnalysisRequest(**(BASE | {field: value}))


def test_defaults_and_no_dataset_coverage_guesses():
    request = AnalysisRequest(**(BASE | {"start_year": 1900, "end_year": 1901}))
    assert request.alpha == 0.05
    assert request.source_mode == "verified_snapshot"
    # Actual dataset coverage and ten-complete-year minimum belong to later services.
    assert request.start_year == 1900


def test_comparison_uses_same_validation():
    fields = {k: v for k, v in BASE.items() if k != "region_id"}
    fields.update(left_region_id="synthetic_left", right_region_id="synthetic_right")
    assert ComparisonRequest(**fields).alpha == 0.05
    with pytest.raises(ValidationError):
        ComparisonRequest(**(fields | {"alpha": 1}))
    with pytest.raises(ValidationError):
        ComparisonRequest(**(fields | {"right_region_id": "synthetic_left"}))


@pytest.mark.parametrize(
    "bbox",
    [
        [1, 2, 0, 3],
        [0, 3, 1, 2],
        [-181, 0, 1, 1],
        [0, -91, 1, 1],
        [0, 0, float("nan"), 1],
        [0, 0, float("inf"), 1],
        [0, 0, 1],
    ],
)
def test_invalid_geographical_bounds(bbox):
    with pytest.raises(ValidationError):
        RegionDescriptor(
            id="synthetic",
            name="Synthetic test area",
            bbox=bbox,
            geometry_source="synthetic-pytest-only",
        )


def test_valid_synthetic_bbox_and_missing_bbox_rejection():
    region = dict(
        id="synthetic",
        name="Synthetic test area",
        bbox=[0, 0, 1, 1],
        geometry_source="synthetic-pytest-only",
    )
    assert RegionDescriptor(**region).bbox == (0, 0, 1, 1)
    with pytest.raises(ValidationError):
        RegionDescriptor(**(region | {"bbox": None}))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize(
    "field",
    [
        "ols_slope_mm_per_year",
        "sen_slope_mm_per_year",
        "mann_kendall_p_value",
    ],
)
def test_nonfinite_statistics_rejected(field, value):
    with pytest.raises(ValidationError):
        Statistics(mann_kendall_method="synthetic-test", **{field: value})


def test_nulls_preserved_and_confidence_bounds_validated():
    statistics = Statistics(mann_kendall_method="synthetic-test")
    payload = json.loads(statistics.model_dump_json())
    assert payload["mann_kendall_p_value"] is None
    assert payload["sen_slope_ci95_mm_per_year"] == [None, None]
    assert payload["significance_status"] == "indeterminate"
    with pytest.raises(ValidationError):
        Statistics(
            mann_kendall_method="synthetic-test", sen_slope_ci95_mm_per_year=(2, 1)
        )
    with pytest.raises(ValidationError):
        Statistics(
            mann_kendall_method="synthetic-test",
            sen_slope_ci95_mm_per_year=(0, float("inf")),
        )
    with pytest.raises(ValidationError):
        Statistics(mann_kendall_method="synthetic-test", significance_status="unknown")


@pytest.mark.parametrize(
    "fields",
    [
        {"period": "2001-13", "precipitation_total_mm": 1, "valid_fraction": 1},
        {"period": "2001-01", "precipitation_total_mm": -1, "valid_fraction": 1},
        {
            "period": "2001-01",
            "precipitation_total_mm": float("nan"),
            "valid_fraction": 1,
        },
        {"period": "2001-01", "precipitation_total_mm": 1, "valid_fraction": 1.1},
    ],
)
def test_invalid_monthly_values(fields):
    with pytest.raises(ValidationError):
        MonthlyItem(**fields)


def test_missing_rainfall_is_not_zero():
    monthly = MonthlyItem(
        period="2001-01", precipitation_total_mm=None, valid_fraction=None
    )
    assert json.loads(monthly.model_dump_json())["precipitation_total_mm"] is None
    with pytest.raises(ValidationError):
        AnnualItem(year=2001, precipitation_total_mm=None, valid_months=13)


def test_source_requires_actual_checksum_and_timezone():
    fields = dict(
        collection_id="synthetic",
        version="synthetic",
        run_type="Final",
        original_variable="synthetic",
        original_unit="mm",
        snapshot_id=str(uuid4()),
        snapshot_sha256="a" * 64,
        retrieved_at="2026-01-01T00:00:00Z",
        source_uri="https://example.org/synthetic",
        aggregation_method="synthetic-test",
    )
    assert SourceDescriptor(**fields).snapshot_sha256 == "a" * 64
    for override in [
        {"snapshot_sha256": "verify-later"},
        {"retrieved_at": None},
        {"retrieved_at": "2026-01-01T00:00:00"},
    ]:
        with pytest.raises(ValidationError):
            SourceDescriptor(**(fields | override))
