import pytest


@pytest.mark.parametrize("path", ["/api/v1/variables", "/api/v1/regions/presets"])
def test_catalog_is_honestly_unavailable(client, path):
    response = client.get(path, headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "DATASET_UNAVAILABLE"
    assert error["details"] == {}
    assert error["request_id"] == response.headers["x-request-id"]
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "bbox" not in response.text
    assert "2001" not in response.text


def test_missing_data_does_not_break_liveness(client):
    assert client.get("/api/v1/variables").status_code == 503
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("path", ["/api/v1/comparisons"])
def test_future_features_are_not_exposed(client, path):
    assert client.post(path, json={}).status_code == 404
