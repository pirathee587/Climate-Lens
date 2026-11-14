from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_exact_response_and_unique_request_ids(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "terratrend-api",
        "api_version": "v1",
    }
    first_id = UUID(response.headers["x-request-id"])
    second = client.get("/health", headers={"X-Request-ID": "untrusted-secret"})
    assert first_id != UUID(second.headers["x-request-id"])


def test_development_docs_and_openapi(client):
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {
        "/health",
        "/api/v1/variables",
        "/api/v1/regions/presets",
    }
    assert "ErrorResponse" in schema["components"]["schemas"]


def test_production_disables_docs():
    with TestClient(create_app(Settings(app_env="production"))) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/health").status_code == 200


def test_allowed_cors_preflight_and_actual_response(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]


def test_disallowed_cors_is_rejected(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    assert response.json()["error"]["code"] == "BAD_REQUEST"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    response = client.get("/health", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in response.headers
