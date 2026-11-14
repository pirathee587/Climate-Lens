"""HTTP smoke for an explicitly unconfigured dataset; never a real-data demo."""

import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID


class SmokeFailure(RuntimeError):
    pass


def check_backend(base_url: str, environment: str, origin: str) -> None:
    def request(path, status, code=None, body=None, method=None, headers=None):
        data = None if body is None else json.dumps(body).encode()
        req = Request(
            base_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={
                "Origin": origin,
                "Content-Type": "application/json",
                **(headers or {}),
            },
        )
        try:
            response = urlopen(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            if response.status != status:
                raise SmokeFailure(
                    f"{path}: expected HTTP {status}, got {response.status}"
                )
            payload = json.load(response)
            request_id = response.headers.get("X-Request-ID", "")
            UUID(request_id)
            if code:
                error = payload["error"]
                if error["code"] != code or error["request_id"] != request_id:
                    raise SmokeFailure(f"{path}: incorrect error contract")
                if not isinstance(error["details"], dict) or not isinstance(
                    error["message"], str
                ):
                    raise SmokeFailure(f"{path}: invalid error fields")
            if response.headers.get("Access-Control-Allow-Origin") != origin:
                raise SmokeFailure(f"{path}: configured CORS origin not accepted")
            if "Content-Disposition" not in response.headers.get(
                "Access-Control-Expose-Headers", ""
            ):
                raise SmokeFailure(f"{path}: download header is not browser-visible")
        print(f"PASS {path} HTTP {status}")
        return payload

    health = request("/health", 200)
    if health != {"status": "ok", "service": "terratrend-api", "api_version": "v1"}:
        raise SmokeFailure("incorrect liveness payload")
    request("/api/v1/variables", 503, "DATASET_UNAVAILABLE")
    request("/api/v1/regions/presets", 503, "DATASET_UNAVAILABLE")
    common = dict(
        variable_id="precipitation",
        start_year=2001,
        end_year=2024,
        alpha=0.05,
        source_mode="verified_snapshot",
    )
    request(
        "/api/v1/analyses",
        503,
        "DATASET_UNAVAILABLE",
        common | {"region_id": "jaffna_area"},
    )
    request(
        "/api/v1/comparisons",
        503,
        "DATASET_UNAVAILABLE",
        common | {"left_region_id": "jaffna_area", "right_region_id": "colombo_area"},
    )
    for suffix in ("", "/export.csv", "/annual.csv", "/metadata.json"):
        request(
            "/api/v1/analyses/00000000-0000-0000-0000-000000000000" + suffix,
            404,
            "NOT_FOUND",
        )
    request("/api/v1/analyses/not-a-uuid", 422, "INVALID_ARGUMENT")
    preflight = Request(
        base_url.rstrip("/") + "/api/v1/analyses",
        method="OPTIONS",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    with urlopen(preflight, timeout=5) as response:
        if (
            response.status != 200
            or response.headers.get("Access-Control-Allow-Origin") != origin
        ):
            raise SmokeFailure("CORS preflight failed")
    for path in ("/docs", "/openapi.json"):
        # /docs serves HTML in development, so do not parse it as JSON.
        req = Request(base_url.rstrip("/") + path)
        try:
            response = urlopen(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            expected = 404 if environment == "production" else 200
            if response.status != expected:
                raise SmokeFailure(f"{path}: expected HTTP {expected}")
        print(f"PASS {path} HTTP {expected}")
    print("PASS CORS and unconfigured-data checks; liveness is not dataset readiness")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--environment", choices=("production", "development"), default="production"
    )
    parser.add_argument("--origin", default="http://localhost:5173")
    args = parser.parse_args()
    try:
        check_backend(args.base_url, args.environment, args.origin)
    except Exception as exc:
        # Never print response bodies, URLs containing credentials or raw exceptions.
        raise SystemExit(
            f"FAIL backend smoke ({type(exc).__name__}); inspect status/configuration"
        ) from None
