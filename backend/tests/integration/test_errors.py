import io
import json
import logging
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.logging import logger
from app.schemas.analysis import AnalysisRequest, Statistics


@pytest.mark.parametrize(
    "path,method,status,code",
    [
        ("/unknown", "get", 404, "NOT_FOUND"),
        ("/health", "post", 405, "METHOD_NOT_ALLOWED"),
    ],
)
def test_http_errors_are_structured(client, path, method, status, code):
    response = getattr(client, method)(path)
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == code
    assert error["details"] == {}
    assert UUID(error["request_id"])
    if status == 405:
        assert "GET" in response.headers["allow"]


def test_validation_and_malformed_json_are_safe(app):
    @app.post("/_test/validate")
    def validate(body: AnalysisRequest):
        return body

    with TestClient(app) as client:
        response = client.post("/_test/validate", json={"alpha": "secret-test-marker"})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_ARGUMENT"
        assert "secret-test-marker" not in response.text
        response = client.post(
            "/_test/validate",
            content="{not-json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_unhandled_500_is_safe_with_cors_and_traceable_logs(app):
    @app.get("/_test/crash")
    def crash():
        raise RuntimeError("secret-test-marker")

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    try:
        with TestClient(app) as client:
            response = client.get(
                "/_test/crash?token=secret-test-marker",
                headers={
                    "Origin": "http://localhost:5173",
                    "Authorization": "secret-test-marker",
                },
            )
    finally:
        logger.removeHandler(handler)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "ANALYSIS_ERROR"
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert "secret-test-marker" not in response.text + stream.getvalue()
    assert "Traceback" not in response.text
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert all(
        record["request_id"] == response.headers["x-request-id"] for record in records
    )
    completed = next(r for r in records if r["event"] == "request_completed")
    assert completed["status"] == 500
    assert completed["duration_ms"] >= 0
    assert completed["endpoint"] == "/_test/crash"
    assert "timestamp" in completed


def test_nonfinite_response_becomes_safe_500(app):
    @app.get("/_test/nonfinite", response_model=Statistics)
    def nonfinite():
        return {
            "mann_kendall_method": "synthetic-pytest-only",
            "ols_slope_mm_per_year": float("nan"),
        }

    with TestClient(app) as client:
        response = client.get("/_test/nonfinite")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "ANALYSIS_ERROR"
    assert "NaN" not in response.text and "Infinity" not in response.text


def test_http_500_does_not_echo_private_detail(app):
    @app.get("/_test/http-error")
    def fail():
        raise HTTPException(500, detail="secret-test-marker")

    with TestClient(app) as client:
        response = client.get("/_test/http-error")
    assert response.status_code == 500
    assert "secret-test-marker" not in response.text


def test_catalog_logs_include_full_endpoint(client):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    try:
        client.get("/api/v1/variables")
    finally:
        logger.removeHandler(handler)
    record = json.loads(stream.getvalue().strip())
    assert record["endpoint"] == "/api/v1/variables"
    assert record["status"] == 503
