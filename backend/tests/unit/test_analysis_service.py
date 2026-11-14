"""Synthetic service/adapter checks, including actual source and science boundaries."""

from dataclasses import replace
from datetime import UTC
from types import SimpleNamespace

import pytest

from app.core.errors import APIError
from app.schemas.analysis import AnalysisRequest
from app.services.analysis_service import AnalysisService
from app.services.catalog import CatalogService
from app.services.statistics_adapter import GajaStatisticsAdapter, StatisticsUnavailable
from tests.unit.analysis_fixtures import make_case


def service(case, science=None, policies=None):
    return AnalysisService(
        CatalogService(case.repository, case.settings.snapshot_root),
        science or GajaStatisticsAdapter(),
        case.settings.snapshot_quality_policies if policies is None else policies,
    )


@pytest.mark.parametrize("slope", [10, -5, 0])
def test_real_engine_mapping_and_manifest_provenance(tmp_path, slope):
    case = make_case(tmp_path, slope=slope)
    response = service(case).analyze(AnalysisRequest(**case.request))
    descriptor = case.repository.list_verified_datasets()[0]
    assert response.statistics.ols_slope_mm_per_year == pytest.approx(slope)
    assert response.statistics.sen_slope_mm_per_year == pytest.approx(slope)
    assert response.statistics.sen_slope_ci95_mm_per_year == pytest.approx(
        (slope, slope)
    )
    assert (
        response.statistics.mann_kendall_method == "two-sided-original-on-annual-totals"
    )
    assert response.algorithm_version == "terratrend-annual-trend-v1"
    assert response.statistics.significance_status == "indeterminate"
    assert response.source.snapshot_sha256 == descriptor.manifest.output_sha256
    assert response.source.retrieved_at == descriptor.manifest.retrieved_at_utc
    assert response.source.version == "V07T"  # Explicitly synthetic fixture label.
    assert response.region.bbox == descriptor.region.bbox
    assert len(response.monthly) == 144
    assert all(row.valid_months == 12 for row in response.annual)
    assert response.annual[0].precipitation_total_mm == pytest.approx(500)
    assert any(
        "SciPy" in warning and "NumPy" in warning for warning in response.warnings
    )


def test_filtering_and_all_scientific_warnings_preserved(tmp_path):
    case = make_case(tmp_path, missing=("2005-04",), fractions=False)
    request = AnalysisRequest(**(case.request | {"end_year": 2011}))
    api = service(case).analyze(request)
    rows = tuple(
        row
        for row in case.repository.get_verified_monthly_series(
            "precipitation", "jaffna_area"
        )
        if int(row.period[:4]) <= 2011
    )
    science = GajaStatisticsAdapter()
    aggregation = science.aggregate_monthly(
        rows, case.settings.snapshot_quality_policies[0], 2001, 2011
    )
    trend = science.analyze(aggregation, 0.05)
    assert api.statistics.model_dump(mode="json") == type(
        api.statistics
    ).model_validate(trend.statistics_payload()).model_dump(mode="json")
    assert set(aggregation.warnings + trend.warnings).issubset(api.warnings)
    assert any("2005-04" in warning for warning in api.warnings)
    assert any("Coverage fractions" in warning for warning in api.warnings)
    assert api.statistics.sample_years == 10
    assert api.annual[4].precipitation_total_mm is None
    assert api.annual[4].valid_months == 11
    assert all(row.period < "2012-01" for row in api.monthly)


@pytest.mark.parametrize(
    "updates", [{"region_id": "unknown"}, {"start_year": 2000}, {"end_year": 2013}]
)
def test_verified_business_bounds(tmp_path, updates):
    case = make_case(tmp_path)
    with pytest.raises(APIError) as error:
        service(case).analyze(AnalysisRequest(**(case.request | updates)))
    assert (error.value.status_code, error.value.code) == (422, "INVALID_ARGUMENT")


def test_missing_and_wrong_hash_quality_policies_fail_closed(tmp_path):
    case = make_case(tmp_path)
    for policies in [
        (),
        (
            case.settings.snapshot_quality_policies[0].model_copy(
                update={"snapshot_sha256": "a" * 64}
            ),
        ),
    ]:
        with pytest.raises(APIError) as error:
            service(case, policies=policies).analyze(AnalysisRequest(**case.request))
        assert (error.value.status_code, error.value.code) == (
            503,
            "DATASET_UNAVAILABLE",
        )


def test_adapter_handles_import_failure_without_mislabeling_data(monkeypatch):
    from app.services import statistics_adapter

    def missing_module(name):
        raise ImportError("private secret-test-marker")

    monkeypatch.setattr(
        statistics_adapter, "importlib", SimpleNamespace(import_module=missing_module)
    )
    with pytest.raises(StatisticsUnavailable):
        GajaStatisticsAdapter()._engine()


@pytest.mark.parametrize(
    "exception_name,status,code",
    [
        ("InvalidDataError", 422, "INVALID_ARGUMENT"),
        ("InsufficientDataError", 422, "INSUFFICIENT_DATA"),
        ("NumericalAnalysisError", 500, "ANALYSIS_ERROR"),
        ("RuntimeError", 500, "ANALYSIS_ERROR"),
    ],
)
def test_actual_engine_exceptions_map_safely(
    tmp_path, monkeypatch, exception_name, status, code
):
    import app.statistics as engine

    case = make_case(tmp_path)
    exception = (
        RuntimeError
        if exception_name == "RuntimeError"
        else getattr(engine, exception_name)
    )

    def failing(*args, **kwargs):
        raise (
            exception(4)
            if exception_name == "InsufficientDataError"
            else exception("secret-test-marker")
        )

    monkeypatch.setattr(engine, "analyze_annual_trend", failing)
    with pytest.raises(APIError) as error:
        service(case).analyze(AnalysisRequest(**case.request))
    assert (error.value.status_code, error.value.code) == (status, code)
    assert "secret-test-marker" not in error.value.message


def test_nonfinite_scientific_response_is_not_json_success(tmp_path):
    case = make_case(tmp_path)

    class BadResult(GajaStatisticsAdapter):
        def analyze(self, aggregation, alpha):
            return replace(
                super().analyze(aggregation, alpha), ols_slope_mm_per_year=float("nan")
            )

    with pytest.raises(APIError) as error:
        service(case, BadResult()).analyze(AnalysisRequest(**case.request))
    assert (error.value.status_code, error.value.code) == (500, "ANALYSIS_ERROR")


def test_explicit_review_configuration_roundtrips_environment(tmp_path, monkeypatch):
    import json

    from app.core.config import Settings

    case = make_case(tmp_path)
    for name in ("snapshot_approvals", "snapshot_quality_policies"):
        records = getattr(case.settings, name)
        monkeypatch.setenv(
            name.upper(), json.dumps([r.model_dump(mode="json") for r in records])
        )
    settings = Settings.from_env()
    assert settings.snapshot_approvals == case.settings.snapshot_approvals
    assert settings.snapshot_quality_policies == case.settings.snapshot_quality_policies
    with pytest.raises(ValueError):
        Settings(snapshot_approvals=(settings.snapshot_approvals[0],) * 2)
    with pytest.raises(ValueError):
        Settings(snapshot_quality_policies=(settings.snapshot_quality_policies[0],) * 2)


def test_quality_review_cannot_predate_source(tmp_path):
    from datetime import datetime

    case = make_case(tmp_path)
    policy = case.settings.snapshot_quality_policies[0]
    stale = policy.model_copy(
        update={
            "review": policy.review.model_copy(
                update={"reviewed_at": datetime(2000, 1, 1, tzinfo=UTC)}
            )
        }
    )
    with pytest.raises(APIError) as error:
        service(case, policies=(stale,)).analyze(AnalysisRequest(**case.request))
    assert (error.value.status_code, error.value.code) == (503, "DATASET_UNAVAILABLE")
