"""API comparisons use artificial bundles and real unchanged source/science code."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.snapshot_repository import get_snapshot_repository
from app.services.statistics_adapter import (
    GajaStatisticsAdapter,
    get_statistics_adapter,
)
from tests.unit.analysis_fixtures import make_case
from tests.unit.repository_fixtures import SyntheticRepository, UnvalidatedDescriptor
from tests.unit.test_comparison_service import comparison_request


def body(case):
    return comparison_request(case).model_dump(mode="json")


def test_success_caches_both_independent_sides(tmp_path):
    case = make_case(tmp_path, region_options={"colombo_area": {"slope": -5}})
    app = create_app(case.settings)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/comparisons",
            json=body(case),
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 200
        assert response.headers["x-request-id"]
        assert (
            response.headers["access-control-allow-origin"] == "http://localhost:5173"
        )
        result = response.json()
        assert result["shared_analyzed_years"] == list(range(2001, 2013))
        for side in ("left", "right"):
            item = result[side]
            cached = client.get("/api/v1/analyses/" + item["analysis_id"])
            assert cached.json() == item
            assert (
                client.get(
                    "/api/v1/analyses/" + item["analysis_id"] + "/export.csv"
                ).status_code
                == 200
            )
    assert len(app.state.result_cache) == 2


@pytest.mark.parametrize(
    "updates",
    [
        {"left_region_id": "colombo_area"},
        {"right_region_id": "unknown"},
        {"variable_id": "temperature"},
        {"start_year": 2013},
        {"start_year": 2000},
        {"alpha": 0},
        {"alpha": 1},
        {"source_mode": "live"},
    ],
)
def test_invalid_comparison_requests_leave_no_results(tmp_path, updates):
    case = make_case(tmp_path)
    app = create_app(case.settings)
    with TestClient(app) as client:
        response = client.post("/api/v1/comparisons", json=body(case) | updates)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ARGUMENT"
    assert len(app.state.result_cache) == 0


def test_failed_shared_year_check_is_atomic(tmp_path):
    case = make_case(
        tmp_path,
        region_options={
            "jaffna_area": {"missing": ("2001-04", "2002-04")},
            "colombo_area": {"missing": ("2003-04",)},
        },
    )
    app = create_app(case.settings)
    with TestClient(app) as client:
        response = client.post("/api/v1/comparisons", json=body(case))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSUFFICIENT_DATA"
    assert len(app.state.result_cache) == 0


def test_second_side_science_failure_does_not_cache_first(tmp_path):
    from app.services.statistics_adapter import ScienceNumericalError

    case = make_case(tmp_path)

    class FailSecond(GajaStatisticsAdapter):
        calls = 0

        def analyze(self, aggregation, alpha):
            self.calls += 1
            if self.calls == 2:
                raise ScienceNumericalError("private secret-test-marker")
            return super().analyze(aggregation, alpha)

    app = create_app(case.settings)
    app.dependency_overrides[get_statistics_adapter] = lambda: FailSecond()
    with TestClient(app) as client:
        response = client.post("/api/v1/comparisons", json=body(case))
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "ANALYSIS_ERROR"
    assert "secret-test-marker" not in response.text
    assert len(app.state.result_cache) == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("version_label", "V08"),
        ("run_type", "Early"),
        ("spatial_aggregation", "different"),
        ("normalization_units", "unknown"),
        ("review", None),
    ],
)
def test_uncertain_repository_metadata_still_fails_closed(tmp_path, field, value):
    # Invalid/inconsistent adapter DTOs cannot be promoted into reviewed409 cases.
    repository = SyntheticRepository(tmp_path)
    raw = repository.descriptors[1].model_dump()
    raw["manifest"][field] = value
    repository.descriptors[1] = UnvalidatedDescriptor(raw)
    app = create_app(Settings(app_env="test", snapshot_root=tmp_path))
    app.dependency_overrides[get_snapshot_repository] = lambda: repository
    request = dict(
        variable_id="precipitation",
        left_region_id="jaffna_area",
        right_region_id="colombo_area",
        start_year=2011,
        end_year=2011,
    )
    with TestClient(app) as client:
        response = client.post("/api/v1/comparisons", json=request)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATASET_UNAVAILABLE"
    assert str(tmp_path) not in response.text
    assert len(app.state.result_cache) == 0


@pytest.mark.parametrize("failure", ["partial", "policy", "snapshot", "manifest"])
def test_missing_reviewed_inputs_do_not_leave_partial_cache(tmp_path, failure):
    case = make_case(tmp_path)
    settings = case.settings
    if failure == "partial":
        settings = settings.model_copy(
            update={"snapshot_approvals": settings.snapshot_approvals[:1]}
        )
    elif failure == "policy":
        settings = settings.model_copy(
            update={"snapshot_quality_policies": settings.snapshot_quality_policies[:1]}
        )
    else:
        descriptor = case.repository.list_verified_datasets()[1]
        path = (
            descriptor.snapshot_path
            if failure == "snapshot"
            else descriptor.manifest_path
        )
        (tmp_path / path).write_bytes(b"CORRUPT SYNTHETIC")
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post("/api/v1/comparisons", json=body(case))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATASET_UNAVAILABLE"
    assert len(app.state.result_cache) == 0


def test_default_production_stays_unavailable(tmp_path):
    case = make_case(tmp_path)
    app = create_app(Settings(app_env="production", snapshot_root=tmp_path))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        for path in ("/api/v1/variables", "/api/v1/regions/presets"):
            assert client.get(path).status_code == 503
        for path, request in (
            ("/api/v1/analyses", case.request),
            ("/api/v1/comparisons", body(case)),
        ):
            response = client.post(path, json=request)
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "DATASET_UNAVAILABLE"
            assert "SYNTHETIC" not in response.text
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
    assert len(app.state.result_cache) == 0
