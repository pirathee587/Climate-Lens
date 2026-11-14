# TerraTrend backend — Pirathee Phase 01 / TT-01

A runnable FastAPI foundation with typed v1 contracts. Requirements addressed:
FR-019 (health/errors), NFR-006 (schema validation), NFR-007 (CORS/secrets),
NFR-008 (request tracing) and NFR-015 (local setup). Catalog readiness portions
of FR-001/002 remain pending Harith's verified inputs and Phase 02 integration.
No database, scientific calculations, data import, result cache or frontend code.

## Local setup (Python 3.12)

From the repository root:

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port "${APP_PORT:-8000}" --no-access-log
```

Your Python installation must provide venv/ensurepip. Local validation on the
initial machine required bootstrapping pip inside the venv because ensurepip was
missing; no system packages were installed. See the phase report for details.
Uvicorn access logging is disabled to avoid logging arbitrary URL query strings.
The app emits JSON request logs with timestamp, matched endpoint, status, duration
and generated request ID; bodies, headers, query strings and exception messages
are excluded. Incoming request IDs are replaced with new UUIDs.

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m pip check
python -m pip_audit -r requirements-dev.lock --no-deps --disable-pip
```

Direct dependency versions are in `requirements*.txt`; constraints in
`requirements-runtime.lock` and `requirements-dev.lock` pin the complete verified
Python 3.12/Linux resolution. Install development dependencies from
`requirements-dev.txt`, which includes runtime dependencies. Update direct pins
and both lock files together in a fresh venv, then rerun tests and the audit.
The lock files are version pins, not wheel hash locks or container digest locks.

## Environment configuration

`.env.example` is a reference template. The app reads process environment only;
it does not implicitly load `.env`. Set variables before starting Uvicorn.

| Variable | Default | Meaning |
|---|---|---|
| `APP_ENV` | `development` | `development`, `test` or `production`; production disables docs/OpenAPI |
| `APP_PORT` | `8000` | Validated port; local Uvicorn command above passes it explicitly |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated exact HTTP(S) origins; empty denies all browser origins |
| `SNAPSHOT_ROOT` | repository `data/demo` | Future verified repository root; no data is read in Phase 01 |
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR or CRITICAL |

The example `SNAPSHOT_ROOT=../data/demo` is relative to a local backend working
directory; the container uses `/data/demo` by default. Docker listens on port 8000;
use host port mapping for a different external port. No credentials are required.
CORS accepts GET/POST and Content-Type from exact allowed origins, exposes
X-Request-ID, and does not enable credentials. CORS controls browser access;
non-browser clients can still call public endpoints.

## Current HTTP behavior

| Method/path | Status/behavior |
|---|---|
| `GET /health` | 200, exact liveness response below, independent of dataset readiness |
| `GET /api/v1/variables` | 503 `DATASET_UNAVAILABLE` |
| `GET /api/v1/regions/presets` | 503 `DATASET_UNAVAILABLE` |
| `GET /docs`, `GET /openapi.json` | 200 in development/test; 404 in production |

```json
{"status":"ok","service":"terratrend-api","api_version":"v1"}
```

Errors use `{"error":{"code":"...","message":"...","details":{},"request_id":"..."}}`.
Malformed JSON is 400; schema validation 422; unknown routes 404; wrong methods
405; unexpected errors 500 with no traceback. Every HTTP response has X-Request-ID.
CORS-denied preflight also returns the structured error contract.

The catalog service deliberately remains unavailable even if files are copied into
the snapshot directory. Phase 02 must connect Harith's verified repository; file
presence alone never constitutes verification. No bounding boxes, coverage dates,
NASA metadata, observations or statistics are invented.

Future `AnalysisRequest`, `ComparisonRequest`, source, series, statistics and UUID
result models are defined in `app/schemas/`. Only implemented routes appear in
OpenAPI. Models validate finite numbers, strict integer years, ordered ranges,
alpha, source mode, WGS84 bounds, checksum shape and chronological series. Pure
schemas do not verify provenance or impose dataset coverage/ten-complete-year
business rules; later integration must enforce those against verified data.

## Docker and CI

From the repository root:

```bash
docker build -f backend/Dockerfile -t terratrend-api:phase01 backend
docker run --rm -p 127.0.0.1:8000:8000 \
  -e ALLOWED_ORIGINS=http://localhost:5173 terratrend-api:phase01
curl http://localhost:8000/health
```

The production image runs as UID 10001, uses Python 3.12 slim, installs only runtime
dependencies, has an HTTP/JSON health check, and defaults to `APP_ENV=production`.
It requires neither NASA access nor a database. A `development` target remains
compatible with the existing starter Compose configuration. Existing frontend and
Compose templates are preserved; full system packaging belongs to Phase 05.

`.github/workflows/backend-ci.yml` runs on relevant main pushes, PRs and manual
invocation. It uses read-only repository permissions and SHA-pinned actions; runs
lint, format, tests, pip check and vulnerability audit; builds an image without
publishing; and checks non-root container health. There is no readiness bypass now
that the backend exists. The existing separate secret-scanning workflow remains.
Remote GitHub Actions runs require a later explicitly authorized commit/push.

## Phase boundaries

Harith owns `app/data/` and real snapshots/manifests. Gaja owns `app/statistics/`.
Their directories are unchanged. There are no analysis, comparison, export or
retrieval routes yet. Future result IDs use a process-local short-lived cache:
restart loses IDs (404), and multi-replica caching is outside P0. That cache is not
implemented in this phase. The current team decision is no database in P0,
overriding optional storage alternatives in the original baseline documentation.

[Phase 01 verification report](PHASE01_REPORT.md) records actual results and limits.
