# TerraTrend backend — Pirathee Phase 04

FastAPI integrates Harith's read-only verified repository and Gaja's statistical
engine. **CONTRACT-READY BUT BLOCKED:** independently reviewed real NASA snapshots
and quality policies are still missing. Default catalogs and analysis return 503.
Health remains 200. Comparison, bounded result caching and exports are implemented;
no database is used.

## Verified source configuration and analysis

`POST /api/v1/analyses` implements the existing AnalysisRequest/AnalysisResponse
contract. Valid requests require both verified regions, matching source metadata,
coverage within the manifest, a reviewed quality policy and ten complete years.
The service delegates aggregation and trends to Gaja; it never converts units again.
Incomplete annual totals stay null; actual analyzed years and scientific warnings
are preserved. Successful responses are stored under their original server UUIDs.

Two process environment settings are JSON arrays, empty by default:

- `SNAPSHOT_APPROVALS`: ArtifactApproval objects with `descriptor_path` and
  independently reviewed `descriptor_sha256`; maximum two, no directory discovery.
- `SNAPSHOT_QUALITY_POLICIES`: ReviewedQualityPolicy objects with `snapshot_sha256`,
  nonempty unique `accepted_quality_flags`, nullable `minimum_valid_fraction`, and
  `review` (status reviewed, reviewed_by, reviewed_at, evidence_reference).

Quality policies bind the exact normalized snapshot hash. Review must not predate
source retrieval; evidence must be a public HTTPS reference without credentials,
query or fragment. Scientific/data owners must approve the actual flag semantics
and any fraction threshold; the backend invents neither. Attestations are operator
configuration, not cryptographic proof of NASA authenticity. Files must remain
immutable while serving. Never use test approvals or synthetic fixtures in production.
`SNAPSHOT_ROOT` contains the explicitly approved artifacts; a nonempty approval
list activates HarithSnapshotRepository. Invalid/incomplete artifacts fail closed.

Missing or corrupt data/policy returns 503 DATASET_UNAVAILABLE; unavailable engine
returns 503 STATISTICS_ENGINE_UNAVAILABLE. Invalid scientific input is 422
INVALID_ARGUMENT, insufficient complete years is 422 INSUFFICIENT_DATA, and numerical
or invalid response failures are sanitized 500 ANALYSIS_ERROR.

[Phase 03 report](PHASE03_REPORT.md) and [Phase 04 report](PHASE04_REPORT.md).

## Comparison, retrieval and exports (Phase 04)

POST /api/v1/comparisons reuses one validated catalog pass and runs each region
independently through the existing AnalysisService and Gaja adapter. At least ten
complete years must be shared. Returned shared_analyzed_years is the exact sorted
intersection; the requested period stays unchanged. Each region's estimates use its
own complete-year sample. Different samples are explicitly disclosed, never labeled
matched-sample comparisons; regional slope differences are not significance-tested.
Existing catalog incompatibilities remain fail-closed503. The final trusted-result
compatibility defense uses409 only when evidence establishes incompatibility.

Successful analyses and both sides of a fully successful comparison are retrievable:

- GET /api/v1/analyses/{id}: original complete AnalysisResponse (canonical JSON).
- GET /api/v1/analyses/{id}/export.csv: monthly CSV.
- GET /api/v1/analyses/{id}/annual.csv: annual CSV.
- GET /api/v1/analyses/{id}/metadata.json: provenance/units/method/limitations JSON.

Unknown/expired/evicted IDs return404 NOT_FOUND; malformed UUIDs return422
INVALID_ARGUMENT. Retrieval/downloads perform no source or scientific calls.
CSV null numbers are blank, headers deterministic and dates ordered. Text cells
that could become spreadsheet formulas are prefixed with an apostrophe; JSON keeps
original identifiers. CSV quoting preserves commas, quotes, line breaks and Unicode.
Filenames contain only server UUIDs and fixed suffixes; CORS exposes Content-Disposition.
Monthly columns: region_id,period,precipitation_total_mm,valid_fraction,snapshot_id.
Annual columns: region_id,year,precipitation_total_mm,valid_months,snapshot_id.

Cache settings (process environment, bounded integers):

| Variable | Default | Range |
|---|---|---|
| RESULT_CACHE_TTL_SECONDS | 1200 | 1..86400 seconds |
| RESULT_CACHE_MAX_ENTRIES | 100 | 2..1000 entries |

Minimum capacity two permits atomic comparison insertion. Fixed retained-JSON limits
are 2 MiB per entry and 32 MiB total. The cache uses monotonic deadlines, synchronized
access and deterministic FIFO eviction; reads do not extend TTL or reorder entries.
Validated serialized copies prevent callers mutating cached content. Failed analyses
and failed comparisons publish no results. Oversized results fail before insertion.
Each application owns its cache; restart clears it. Run a single worker for P0:
multiple workers/replicas do not share IDs. No Redis, SQLite or external cache.

Requirements covered: FR-017 independent comparisons; FR-018 CSV/provenance; FR-019
safe errors; NFR-011 missing-data integrity and NFR-014 source/year consistency.
The comparison frontend owner must add shared_analyzed_years to its existing mirror
and consume that backend field. Frontend source is unchanged in this phase.

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
| `SNAPSHOT_ROOT` | repository `data/demo` | Explicitly approved immutable repository root |
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
| `GET /api/v1/variables` | 503 by default; 200 with verified two-region repository |
| `GET /api/v1/regions/presets` | 503 by default; 200 with verified two-region repository |
| `POST /api/v1/analyses` | 503 by default; 200 with approved sources/policies and sufficient years |
| `POST /api/v1/comparisons` | 503 by default; 200 with compatible sources and ten shared complete years |
| `GET /api/v1/analyses/{id}` | 200 for retained result; 404 otherwise |
| `GET /api/v1/analyses/{id}/export.csv`, `/annual.csv`, `/metadata.json` | 200 for retained result; 404 otherwise |
| `GET /docs`, `GET /openapi.json` | 200 in development/test; 404 in production |

```json
{"status":"ok","service":"terratrend-api","api_version":"v1"}
```

Errors use `{"error":{"code":"...","message":"...","details":{},"request_id":"..."}}`.
Malformed JSON is 400; schema validation 422; unknown routes 404; wrong methods
405; unexpected errors 500 with no traceback. Every HTTP response has X-Request-ID.
CORS-denied preflight also returns the structured error contract.

See the Phase 03 configuration above for explicit repository activation. Schemas
validate finite numbers, strict years and ordered series; the orchestration layer
also validates provenance, coverage and complete-year eligibility.

## Docker and CI

From the repository root:

```bash
docker build -f backend/Dockerfile -t terratrend-api:phase04 backend
docker run --rm -p 127.0.0.1:8000:8000 \
  -e ALLOWED_ORIGINS=http://localhost:5173 terratrend-api:phase04
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
Phase 04 delivery includes an explicitly authorized backend-only CI dispatch.

## Ownership and historical reports

Harith owns `app/data/`; Gaja owns `app/statistics/`. Both modules are integrated
without modifying their implementations. Phase 04 implements comparison, a
short-lived result cache and the agreed GET CSV export contract. Frontend fitted
OLS points remain a separate additive contract change; existing schemas are reused.

Earlier reports describe their original phase state:

- [Phase 01](PHASE01_REPORT.md)
- [Phase 02](PHASE02_REPORT.md)
- [Harith data module](DATA_MODULE_REPORT.md)
- [Gaja statistical engine](STATISTICS_MODULE_REPORT.md)
