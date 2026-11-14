"""Real engine synthetic comparison checks; no real NASA findings."""

import pytest

from app.core.errors import APIError
from app.schemas.analysis import AnalysisRequest, ComparisonRequest, ComparisonResponse
from app.services.comparison_service import (
    ComparisonService,
    verified_result_compatibility,
)
from tests.unit.analysis_fixtures import make_case
from tests.unit.test_analysis_service import service


def comparison_request(case):
    return ComparisonRequest(
        **{key: value for key, value in case.request.items() if key != "region_id"},
        left_region_id="jaffna_area",
        right_region_id="colombo_area",
    )


def test_independent_trends_one_catalog_validation(tmp_path, monkeypatch):
    case = make_case(tmp_path, region_options={"colombo_area": {"slope": -5}})
    analysis = service(case)
    original = analysis.catalog.validated_snapshots
    calls = []

    def validate():
        calls.append(1)
        return original()

    monkeypatch.setattr(analysis.catalog, "validated_snapshots", validate)
    response = ComparisonService(analysis).compare(comparison_request(case))
    assert len(calls) == 1
    assert response.left.region.id == "jaffna_area"
    assert response.right.region.id == "colombo_area"
    assert response.left.analysis_id != response.right.analysis_id
    assert response.left.statistics.ols_slope_mm_per_year == pytest.approx(10)
    assert response.right.statistics.ols_slope_mm_per_year == pytest.approx(-5)
    assert response.shared_analyzed_years == list(range(2001, 2013))
    assert all(response.dataset_compatibility.model_dump().values())
    assert set(response.left.warnings + response.right.warnings).issubset(
        response.warnings
    )
    assert any("No test of the difference" in w for w in response.warnings)
    assert response.shared_requested_period.start_year == 2001
    assert response.shared_requested_period.end_year == 2012


def test_exactly_ten_shared_years_with_different_samples_are_disclosed(tmp_path):
    case = make_case(
        tmp_path,
        region_options={
            "jaffna_area": {"missing": ("2002-04",)},
            "colombo_area": {"missing": ("2003-04",), "slope": -5},
        },
    )
    result = ComparisonService(service(case)).compare(comparison_request(case))
    assert result.shared_analyzed_years == [2001, *range(2004, 2013)]
    assert result.left.statistics.sample_years == 11
    assert result.right.statistics.sample_years == 11
    assert result.left.annual[1].precipitation_total_mm is None
    assert result.right.annual[2].precipitation_total_mm is None
    assert any("not matched-sample" in w for w in result.warnings)
    for years in ([2001] * 10, list(reversed(result.shared_analyzed_years)), []):
        raw = result.model_dump()
        raw["shared_analyzed_years"] = years
        with pytest.raises(ValueError):
            ComparisonResponse.model_validate(raw)


def test_insufficient_shared_years_even_when_each_has_ten(tmp_path):
    case = make_case(
        tmp_path,
        region_options={
            "jaffna_area": {"missing": ("2001-04", "2002-04")},
            "colombo_area": {"missing": ("2003-04",)},
        },
    )
    with pytest.raises(APIError) as exc:
        ComparisonService(service(case)).compare(comparison_request(case))
    assert (exc.value.status_code, exc.value.code) == (422, "INSUFFICIENT_DATA")


@pytest.mark.parametrize(
    "field,value",
    [
        ("collection_id", "OTHER"),
        ("version", "V08"),
        ("original_variable", "other"),
        ("original_unit", "mm/hr"),
        ("aggregation_method", "different spatial method"),
    ],
)
def test_post_validation_compatibility_defense(tmp_path, field, value):
    case = make_case(tmp_path)
    analysis = service(case)
    left = analysis.analyze(AnalysisRequest(**case.request))
    right = analysis.analyze(
        AnalysisRequest(**(case.request | {"region_id": "colombo_area"}))
    )
    # Unit test only: simulate trusted results reaching the final defense. Real
    # repository mismatches are rejected earlier with 503, never relabeled409.
    right = right.model_copy(
        update={"source": right.source.model_copy(update={field: value})}
    )
    with pytest.raises(APIError) as exc:
        verified_result_compatibility(left, right)
    assert (exc.value.status_code, exc.value.code) == (409, "INCOMPATIBLE_DATA")
