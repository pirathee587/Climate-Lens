"""Actual API integration over synthetic approved artifacts and real Gaja algorithms."""

import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.statistics_adapter import (
    GajaStatisticsAdapter,
    StatisticsUnavailable,
    get_statistics_adapter,
)
from tests.unit.analysis_fixtures import make_case


@pytest.fixture
def case(tmp_path):
    return make_case(tmp_path)


def test_ten_year_analysis_actual_factory_and_uuid(case):
    with TestClient(create_app(case.settings)) as client:
        body = case.request | {"end_year": 2010}
        response = client.post(
            "/api/v1/analyses", json=body, headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        result = response.json()
        assert UUID(result["analysis_id"])
        assert (
            result["analysis_id"]
            != client.post("/api/v1/analyses", json=body).json()["analysis_id"]
        )
        assert response.headers["x-request-id"]
        assert (
            response.headers["access-control-allow-origin"] == "http://localhost:5173"
        )
        assert result["statistics"]["sample_years"] == 10
        assert result["request"] == body
        assert set(result) == {
            "analysis_id",
            "request",
            "region",
            "source",
            "monthly",
            "annual",
            "statistics",
            "warnings",
            "algorithm_version",
        }
        assert "snapshot_path" not in response.text
        assert client.get("/api/v1/variables").status_code == 200
        assert client.post("/api/v1/comparisons", json={}).status_code == 422
        assert (
            client.get("/api/v1/analyses/" + result["analysis_id"]).status_code == 200
        )
        assert (
            client.get(
                "/api/v1/analyses/" + result["analysis_id"] + "/export.csv"
            ).status_code
            == 200
        )


@pytest.mark.parametrize(
    "updates",
    [
        {"variable_id": "temperature"},
        {"region_id": "unknown"},
        {"start_year": 2013},
        {"alpha": 0},
        {"alpha": 1},
        {"alpha": -0.1},
        {"source_mode": "live"},
    ],
)
def test_invalid_requests(case, updates):
    with TestClient(create_app(case.settings)) as client:
        response = client.post("/api/v1/analyses", json=case.request | updates)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ARGUMENT"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]


def test_production_default_has_no_synthetic_results(case):
    # Synthetic bundles remain unavailable without explicit approvals.
    settings = Settings(app_env="production", snapshot_root=case.settings.snapshot_root)
    with TestClient(create_app(settings)) as client:
        for path in ("/api/v1/variables", "/api/v1/regions/presets"):
            assert client.get(path).status_code == 503
        response = client.post("/api/v1/analyses", json=case.request)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATASET_UNAVAILABLE"
        assert "SYNTHETIC" not in response.text
        assert client.get("/health").json() == {
            "status": "ok",
            "service": "terratrend-api",
            "api_version": "v1",
        }
        assert client.get("/docs").status_code == 404


@pytest.mark.parametrize(
    "mutation", ["snapshot", "manifest", "descriptor", "partial", "quality"]
)
def test_unavailable_artifacts_have_safe_errors(case, mutation):
    settings = case.settings
    descriptor = json.loads(
        (
            settings.snapshot_root / settings.snapshot_approvals[0].descriptor_path
        ).read_bytes()
    )
    if mutation == "partial":
        settings = settings.model_copy(
            update={"snapshot_approvals": settings.snapshot_approvals[:1]}
        )
    elif mutation == "quality":
        settings = settings.model_copy(update={"snapshot_quality_policies": ()})
    else:
        relative = (
            settings.snapshot_approvals[0].descriptor_path
            if mutation == "descriptor"
            else descriptor[
                "snapshot_path" if mutation == "snapshot" else "manifest_path"
            ]
        )
        (settings.snapshot_root / relative).write_bytes(b"CORRUPT SYNTHETIC ARTIFACT")
    with TestClient(create_app(settings)) as client:
        response = client.post("/api/v1/analyses", json=case.request)
        assert client.get("/health").status_code == 200
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATASET_UNAVAILABLE"
    assert str(settings.snapshot_root) not in response.text


@pytest.mark.parametrize(
    "missing,rejected,nulls,expected_valid",
    [
        (("2005-04",), (), (), 11),
        ((), ("2005-04",), (), 11),
        ((), (), ("2005-04",), 11),
        (tuple(f"2005-{m:02d}" for m in range(1, 13)), (), (), 0),
    ],
)
def test_missing_quality_rejected_and_gapped_years(
    tmp_path, missing, rejected, nulls, expected_valid
):
    case = make_case(tmp_path, missing=missing, rejected=rejected, nulls=nulls)
    with TestClient(create_app(case.settings)) as client:
        response = client.post("/api/v1/analyses", json=case.request)
    assert response.status_code == 200
    result = response.json()
    assert result["statistics"]["sample_years"] == 11
    assert result["statistics"]["significance_status"] == "indeterminate"
    assert result["annual"][4]["valid_months"] == expected_valid
    assert result["annual"][4]["precipitation_total_mm"] is None
    assert any("2005" in warning for warning in result["warnings"])
    if nulls:
        assert (
            next(row for row in result["monthly"] if row["period"] == "2005-04")[
                "precipitation_total_mm"
            ]
            is None
        )
    if rejected:
        assert any("quality-rejected" in warning for warning in result["warnings"])


def test_less_than_ten_complete_years(tmp_path):
    case = make_case(tmp_path, end=2009)
    with TestClient(create_app(case.settings)) as client:
        response = client.post("/api/v1/analyses", json=case.request)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSUFFICIENT_DATA"


def test_source_rate_is_not_converted_twice(tmp_path):
    case = make_case(tmp_path, original_units="mm/hr")
    with TestClient(create_app(case.settings)) as client:
        response = client.post("/api/v1/analyses", json=case.request)
    assert response.status_code == 200
    result = response.json()
    assert result["source"]["original_unit"] == "mm/hr"
    assert result["monthly"][0]["precipitation_total_mm"] == 744
    assert result["monthly"][1]["precipitation_total_mm"] == 672
    assert result["annual"][0]["precipitation_total_mm"] == 8760


def test_scientific_unavailability_is_not_a_dataset_error(case):
    class Unavailable(GajaStatisticsAdapter):
        def _engine(self):
            raise StatisticsUnavailable("private secret-test-marker")

    app = create_app(case.settings)
    app.dependency_overrides[get_statistics_adapter] = lambda: Unavailable()
    with TestClient(app) as client:
        response = client.post("/api/v1/analyses", json=case.request)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "STATISTICS_ENGINE_UNAVAILABLE"
    assert "secret-test-marker" not in response.text


def test_numerical_failure_has_safe_response_and_logs(case, monkeypatch, caplog):
    import app.statistics as engine

    def failing(*args, **kwargs):
        raise engine.NumericalAnalysisError("private secret-test-marker")

    monkeypatch.setattr(engine, "analyze_annual_trend", failing)
    with TestClient(create_app(case.settings)) as client:
        response = client.post("/api/v1/analyses", json=case.request)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "ANALYSIS_ERROR"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert "secret-test-marker" not in response.text + caplog.text
    assert str(case.settings.snapshot_root) not in response.text + caplog.text
