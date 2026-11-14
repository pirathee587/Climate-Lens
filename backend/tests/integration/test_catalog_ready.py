"""Catalog success is tested only with a clearly labeled synthetic injected adapter."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.snapshot_repository import get_snapshot_repository
from tests.unit.repository_fixtures import SyntheticRepository, UnvalidatedDescriptor


@pytest.fixture
def synthetic_client(tmp_path):
    repository = SyntheticRepository(tmp_path)
    app = create_app(Settings(app_env="test", snapshot_root=tmp_path))
    app.dependency_overrides[get_snapshot_repository] = lambda: repository
    with TestClient(app) as client:
        yield client, repository


def test_catalogs_match_verified_adapter_contract(synthetic_client):
    client, repo = synthetic_client
    variables = client.get(
        "/api/v1/variables", headers={"Origin": "http://localhost:5173"}
    )
    assert variables.status_code == 200
    assert variables.json() == {
        "variables": [repo.descriptors[0].variable.model_dump(mode="json")]
    }
    assert variables.headers["x-request-id"]
    assert variables.headers["access-control-allow-origin"] == "http://localhost:5173"
    regions = client.get("/api/v1/regions/presets")
    assert regions.status_code == 200
    assert regions.json() == {
        "regions": [d.region.model_dump(mode="json") for d in repo.descriptors]
    }
    assert all(region["bbox"] is not None for region in regions.json()["regions"])
    assert "snapshot_path" not in regions.text + variables.text
    assert "2011-01" in variables.text
    assert client.get("/health").status_code == 200
    assert client.post("/api/v1/analyses", json={}).status_code == 422
    assert client.post("/api/v1/comparisons", json={}).status_code == 422


@pytest.mark.parametrize(
    "failure",
    ["missing_region", "corrupt_artifact", "adapter_exception", "invalid_manifest"],
)
def test_unavailable_response_has_safe_tracing(synthetic_client, tmp_path, failure):
    client, repo = synthetic_client
    if failure == "missing_region":
        repo.descriptors.pop()
    elif failure == "corrupt_artifact":
        (tmp_path / repo.descriptors[0].snapshot_path).write_bytes(
            b"corrupted-synthetic"
        )
    elif failure == "invalid_manifest":
        raw = repo.descriptors[0].model_dump()
        raw["manifest"].pop("review")
        repo.descriptors[0] = UnvalidatedDescriptor(raw)
    else:

        def failing_adapter():
            raise RuntimeError("private secret-test-marker " + str(tmp_path))

        repo.list_verified_datasets = failing_adapter
    for path in ["/api/v1/variables", "/api/v1/regions/presets"]:
        response = client.get(path, headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATASET_UNAVAILABLE"
        assert (
            response.json()["error"]["request_id"] == response.headers["x-request-id"]
        )
        assert response.json()["error"]["details"] == {}
        assert str(tmp_path) not in response.text
        assert "secret-test-marker" not in response.text
        assert (
            response.headers["access-control-allow-origin"] == "http://localhost:5173"
        )
    assert client.get("/health").status_code == 200
