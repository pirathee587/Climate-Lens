# TerraTrend backend — Pirathee Phases 01–02 / TT-01, TT-05 Part 1

A runnable FastAPI foundation with typed v1 contracts and a repository integration boundary. Requirements addressed:
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

The default repository remains unavailable even if files are copied into the
snapshot directory. The Phase 02 integration contract is implemented, but Harith's
actual adapter and verified artifacts are absent; file presence alone never
constitutes verification. No bounding boxes, coverage dates,
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


## Phase 02 — repository integration and catalog readiness

**Status: CONTRACT-READY BUT BLOCKED.** Harith's data directory and snapshot/manifest
directories still contain only placeholders. No real NASA data adapter is integrated.
The production defaults therefore remain 503 for both catalogs, while health is 200.
No Phase 03 work, database, NASA fetching, CSV parsing or ingestion was introduced.

`app/services/snapshot_repository.py` defines the trusted read-only adapter port:

- `list_verified_datasets()` returns normalized `SnapshotDescriptor` objects.
- `list_verified_regions(variable_id)` returns checked `RegionDescriptor` objects.
- `get_verified_monthly_series(variable_id, region_id)` returns already-normalized
  `NormalizedMonthlyRecord` objects, including quality flags and coverage fractions.

Harith's future adapter is responsible for reading its own manifest/CSV format,
normalizing values, independently reviewing source authenticity, and binding parsed
records/metadata to the exact hashed artifacts. `app/schemas/repository.py` describes
an integration DTO, not a new raw manifest file format. There is no competing loader.
Snapshot/manifest paths are repository-relative adapter references, never API inputs.
The adapter must supply a reviewed manifest fingerprint and human provenance review
attestation with reviewer, review time and evidence reference. A checksum match is
artifact integrity relative to that supplied fingerprint, not proof of NASA origin.
The boundary cannot independently establish scientific authenticity or verify that
an adapter correctly parsed its CSV; the trusted reviewed adapter must do that.

Dependency wiring is explicit: the API depends on `get_catalog_service`, which
receives `get_snapshot_repository` and the application's existing `SNAPSHOT_ROOT`.
`get_snapshot_repository` returns `UnavailableSnapshotRepository` until a reviewed
Harith adapter is explicitly wired. Tests override this dependency with a clearly
labeled synthetic adapter rooted in pytest `tmp_path`; it is never enabled in
production. No automatic import, file discovery or request-time network fetch exists.

Catalog service validates both required regions together, including all artifacts,
metadata consistency, matching collection/version/Final run, units, processing and
coverage. The current baseline accepts IMERG collection GPM_3IMERGM_07 with a V07
version label supplied by the adapter; no example version, date or geometry is filled
in. Additional product versions require an explicit science/contract review.
Original units supported by this DTO are mm/hr, mm or mm/month; normalized totals
remain mm/month, and public catalog aggregation units remain mm. No rate conversion
or temporal aggregation happens here. Region display labels and actual bounds come
entirely from the adapter, and null/invalid bounds cannot become selectable presets.
Partial one-region catalogs and silently mixed variants are rejected.

`app/services/snapshot_validation.py` checks read-only artifact existence, hashes,
root confinement, traversal/absolute/Windows paths and symlink references. All
artifact symlinks are rejected, including links inside the root. The trusted local
repository must remain immutable while requests are served; this is not a sandbox
for concurrently hostile filesystem writers. No private paths or provider exception
messages are returned or logged. Missing files, validation failures and provider
exceptions become the existing structured 503 DATASET_UNAVAILABLE with request ID.

`validate_series` returns `ValidatedMonthlySeries`: ordered unique observations,
quality/coverage metadata, descriptor and explicit `missing_periods`. Interior gaps
are recorded without inventing rows. Null rainfall/coverage stays null; NaN/Infinity
and out-of-coverage/duplicate/unordered records are rejected. Catalogs report the
validated first/last span, not a guarantee of complete data within that span. The
later analysis layer must inspect missing months and enforce ten complete years.

Both catalog endpoints return the existing API schemas if the complete injected
repository passes validation. The production response remains unavailable until the
real adapter exists. No external catalog payload or OpenAPI contract was changed.
The backend CI workflow is unchanged: main pushes and relevant PRs run it; feature
pushes do not. It also permits manual backend-only workflow dispatch.

[Phase 02 verification and GitHub delivery report](PHASE02_REPORT.md).
