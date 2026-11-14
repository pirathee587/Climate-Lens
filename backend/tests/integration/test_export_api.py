"""Cached retrieval/export is offline and exactly matches synthetic API analyses."""

import csv
import io
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.analysis_service import AnalysisService
from app.services.catalog import CatalogService
from app.services.result_cache import ResultCache
from tests.unit.analysis_fixtures import make_case


@pytest.fixture
def completed(tmp_path):
    case = make_case(
        tmp_path, missing=("2005-04",), nulls=("2006-02",), fractions=False
    )
    app = create_app(case.settings)
    with TestClient(app) as client:
        response = client.post("/api/v1/analyses", json=case.request)
        assert response.status_code == 200
        result = response.json()
        yield client, app, result, case


def test_cached_retrieval_and_exports_do_not_access_data_or_compute(
    completed, monkeypatch
):
    client, app, result, case = completed

    def forbidden(*args, **kwargs):
        raise AssertionError("cached routes must not fetch data or recalculate science")

    monkeypatch.setattr(CatalogService, "validated_snapshots", forbidden)
    monkeypatch.setattr(AnalysisService, "analyze", forbidden)
    # Disallow network sockets too: TestClient's local ASGI transport needs none.
    import socket

    monkeypatch.setattr(socket, "create_connection", forbidden)
    base = "/api/v1/analyses/" + result["analysis_id"]
    response = client.get(base)
    assert response.status_code == 200
    assert response.json() == result
    assert response.headers["x-request-id"]
    for suffix in ("/export.csv", "/annual.csv", "/metadata.json"):
        assert client.get(base + suffix).status_code == 200
    # A new application/process-local cache cannot see this application's ID.
    with TestClient(create_app(case.settings)) as other:
        assert other.get(base).status_code == 404
    assert len(app.state.result_cache) == 1


def test_monthly_csv_values_nulls_header_and_download_headers(completed):
    client, _, result, _ = completed
    base = "/api/v1/analyses/" + result["analysis_id"]
    response = client.get(
        base + "/export.csv", headers={"Origin": "http://localhost:5173"}
    )
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="terratrend-{result["analysis_id"]}-monthly.csv"'
    )
    assert "Content-Disposition" in response.headers["access-control-expose-headers"]
    reader = csv.DictReader(io.StringIO(response.text))
    assert reader.fieldnames == [
        "region_id",
        "period",
        "precipitation_total_mm",
        "valid_fraction",
        "snapshot_id",
    ]
    rows = list(reader)
    assert len(rows) == len(result["monthly"])
    assert [row["period"] for row in rows] == sorted(row["period"] for row in rows)
    for row, expected in zip(rows, result["monthly"], strict=True):
        assert row["period"] == expected["period"]
        assert row["region_id"] == result["region"]["id"]
        assert row["snapshot_id"] == result["source"]["snapshot_id"]
        for field in ("precipitation_total_mm", "valid_fraction"):
            if expected[field] is None:
                assert row[field] == ""
            else:
                assert float(row[field]) == expected[field]


def test_annual_csv_and_reproducibility_metadata_match_original(completed):
    client, _, result, _ = completed
    base = "/api/v1/analyses/" + result["analysis_id"]
    response = client.get(base + "/annual.csv")
    reader = csv.DictReader(io.StringIO(response.text))
    assert reader.fieldnames == [
        "region_id",
        "year",
        "precipitation_total_mm",
        "valid_months",
        "snapshot_id",
    ]
    rows = list(reader)
    assert len(rows) == len(result["annual"])
    for row, expected in zip(rows, result["annual"], strict=True):
        assert int(row["year"]) == expected["year"]
        assert int(row["valid_months"]) == expected["valid_months"]
        assert row["snapshot_id"] == result["source"]["snapshot_id"]
        if expected["precipitation_total_mm"] is None:
            assert row["precipitation_total_mm"] == ""
        else:
            assert (
                float(row["precipitation_total_mm"])
                == expected["precipitation_total_mm"]
            )
    response = client.get(base + "/metadata.json")
    meta = response.json()
    for field in (
        "analysis_id",
        "request",
        "region",
        "source",
        "statistics",
        "algorithm_version",
        "warnings",
    ):
        assert meta[field] == result[field]
    assert meta["normalized_units"]["annual"] == "mm"
    assert meta["scientific_limitations"]
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.parametrize("suffix", ["", "/export.csv", "/annual.csv", "/metadata.json"])
def test_unknown_and_malformed_ids_have_safe_structured_errors(client, suffix):
    for identifier, status, code in (
        (str(uuid4()), 404, "NOT_FOUND"),
        ("not-a-uuid", 422, "INVALID_ARGUMENT"),
    ):
        response = client.get("/api/v1/analyses/" + identifier + suffix)
        assert response.status_code == status
        assert response.json()["error"]["code"] == code
        assert (
            response.json()["error"]["request_id"] == response.headers["x-request-id"]
        )


def test_expiration_and_restart_clear_all_downloads(tmp_path):
    case = make_case(tmp_path)
    app = create_app(case.settings)
    now = [0]
    app.state.result_cache = ResultCache(ttl_seconds=10, clock=lambda: now[0])
    with TestClient(app) as client:
        result = client.post("/api/v1/analyses", json=case.request).json()
        now[0] = 10
        for suffix in ("", "/export.csv", "/annual.csv", "/metadata.json"):
            response = client.get("/api/v1/analyses/" + result["analysis_id"] + suffix)
            assert response.status_code == 404
            assert response.json()["error"]["code"] == "NOT_FOUND"
    with TestClient(create_app(Settings(app_env="test"))) as restarted:
        assert (
            restarted.get("/api/v1/analyses/" + result["analysis_id"]).status_code
            == 404
        )


def test_failed_single_analysis_does_not_enter_cache(tmp_path):
    case = make_case(tmp_path, end=2009)
    app = create_app(case.settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/analyses", json=case.request).status_code == 422
    assert len(app.state.result_cache) == 0
