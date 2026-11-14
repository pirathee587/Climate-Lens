# Pirathee Phase 01 — TT-01 implementation report

Status: **PHASE 01 COMPLETE — locally validated**. Date: 14 November 2026.
GitHub-hosted CI execution is pending a separately authorized commit/push.
No commit, push, PR, GitHub issue, deployment or Phase 02 work was performed.

## Implemented scope

Runnable FastAPI application factory; exact liveness endpoint; restricted CORS;
generated request UUIDs and structured safe error responses; JSON request logs;
typed future request/response contracts; explicitly unavailable catalog boundary;
Python 3.12 dependency pins/constraints; backend-only CI and non-root Docker image.
No database or database driver, data loading, statistical formulas, cache, analysis,
comparison, CSV export or frontend functionality was added.

Owner: Pirathee. Scope references: TT-01; FR-019; NFR-006/007/008/015.
Original project documentation was inspected and preserved. The supplied Pirathee
implementation roadmap/prompt authorized this phase and overrides optional database
choices from the archived baseline. Full frontend/Compose work remains Phase 05.

## Exact modified files

```text
.github/workflows/backend-ci.yml
backend/.dockerignore
backend/Dockerfile
```

## Exact created files

```text
backend/PHASE01_REPORT.md
backend/README.md
backend/app/__init__.py
backend/app/api/__init__.py
backend/app/api/v1/__init__.py
backend/app/api/v1/regions.py
backend/app/api/v1/router.py
backend/app/api/v1/variables.py
backend/app/core/__init__.py
backend/app/core/config.py
backend/app/core/errors.py
backend/app/core/logging.py
backend/app/main.py
backend/app/schemas/__init__.py
backend/app/schemas/analysis.py
backend/app/schemas/common.py
backend/app/schemas/source.py
backend/app/services/__init__.py
backend/app/services/catalog.py
backend/pyproject.toml
backend/requirements-dev.lock
backend/requirements-dev.txt
backend/requirements-runtime.lock
backend/requirements.txt
backend/tests/__init__.py
backend/tests/conftest.py
backend/tests/integration/__init__.py
backend/tests/integration/test_catalog_unavailable.py
backend/tests/integration/test_errors.py
backend/tests/integration/test_health.py
backend/tests/unit/__init__.py
backend/tests/unit/test_config.py
backend/tests/unit/test_schemas.py
```

The existing .gitkeep placeholders remain. `backend/.venv/` is local and ignored.

## Current endpoints

| Endpoint | Verified behavior |
|---|---|
| GET /health | 200 exact liveness JSON |
| GET /api/v1/variables | 503 DATASET_UNAVAILABLE |
| GET /api/v1/regions/presets | 503 DATASET_UNAVAILABLE |
| GET /docs and /openapi.json | 200 in development/test; 404 in production |
| POST /api/v1/analyses and /comparisons | 404; intentionally not implemented |

Only implemented routes are advertised in generated OpenAPI. Future schema classes
exist for analysis/comparison inputs and outputs, provenance, verified bounds,
monthly/annual series, nullable finite statistics, statuses and UUID result IDs.
No verified region/date metadata is available. File presence never enables catalogs.

## Actual production container responses

These were captured from the final locally built image using urllib inside a
container with external networking disabled. They contain no scientific data.

`/health` → 200

```json
{
  "status": "ok",
  "service": "terratrend-api",
  "api_version": "v1"
}
```

`/api/v1/variables` → 503

```json
{
  "error": {
    "code": "DATASET_UNAVAILABLE",
    "message": "Verified snapshots are not integrated. Dataset catalogs are unavailable.",
    "details": {},
    "request_id": "fb3e61ef-ff1d-4ebd-ad6a-81e82fbe441c"
  }
}
```

`/api/v1/regions/presets` → 503

```json
{
  "error": {
    "code": "DATASET_UNAVAILABLE",
    "message": "Verified snapshots are not integrated. Dataset catalogs are unavailable.",
    "details": {},
    "request_id": "6b41dab4-85e2-40f7-a859-2f367eafe4de"
  }
}
```

`/docs` → 404

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found.",
    "details": {},
    "request_id": "9ed00352-177a-4d29-94b6-7cc639bc41c3"
  }
}
```

## Commands actually executed and results

From repository root (unless noted):

```text
python3.12 -m venv backend/.venv
  INITIAL FAILURE: ensurepip is unavailable on this host.
  RESOLVED locally: downloaded the official PyPI pip wheel via Python urllib,
  verified its published SHA-256, extracted it under /tmp, and installed pip into
  backend/.venv with --ignore-installed. No global package/system changes.

backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
  PASS; Python 3.12.3, all direct/dependency pins resolve.

backend/.venv/bin/python -m ruff check backend
  All checks passed!
backend/.venv/bin/python -m ruff format --check backend
  27 files already formatted
backend/.venv/bin/python -m pytest -q backend/tests
  71 passed, 1 warning in 0.47s
backend/.venv/bin/python -m pip check
  No broken requirements found.
backend/.venv/bin/python -m pip_audit -r backend/requirements-dev.lock --no-deps --disable-pip
  No known vulnerabilities found.
  Auditor advises hashed dependencies; these lock files pin versions, not hashes.

docker build -f backend/Dockerfile -t terratrend-api:phase01 backend
  PASS, including runtime dependency installation and pip check.
  Final image: sha256:a4e46f0aec14089a3fb8585d47bb6afc29e07663c51d886100f38073b2c8fb7d

python3 /tmp/terratrend_smoke.py
  PASS: temporary container, --network none, UID 10001, Docker HEALTHCHECK healthy.
  GET /health=200; both catalogs=503; production docs=404.
  Request IDs matched response headers; temporary container removed in finally.

/tmp/terratrend-actionlint -shellcheck= .github/workflows/backend-ci.yml
  PASS, actionlint v1.7.12; release archive SHA-256 verified before use.
  ShellCheck was disabled (not installed); every run block separately passed bash -n.

PyYAML safe_load backend workflow + bash -n for each run block
  PASS: triggers/jobs/least-privilege permissions and shell syntax parsed.

docker run --rm -v "$PWD:/repo:ro" zricethezav/gitleaks:v8.24.2 dir /repo --redact --no-banner
  PASS: scanned ~441125 bytes; no leaks found.
docker run --rm -v "$PWD:/repo:ro" zricethezav/gitleaks:v8.24.2 git /repo --redact --no-banner
  PASS: 2 commits scanned; no leaks found.

git diff --check
  PASS, no whitespace errors.

Original-doc byte comparison against HEAD and changed-file ownership audit
  PASS: all 15 baseline Markdown documents unchanged; only backend/ and
  .github/workflows/backend-ci.yml changed; Harith/Gaja/UI/data files unchanged.
```

Initial lint/format findings were corrected before the final passing checks.
Tests cover health/docs/CORS, honest catalog errors, request IDs and logs, 400/404/
405/422/500 contracts, private error redaction, response NaN rejection, nullable
values, bounds/checksum validation, request alpha/year/source validation and env
configuration. All numerical/geographical unit-test values are explicitly synthetic
and are never returned by the production catalog.

The one warning is upstream Starlette's deprecation of the httpx TestClient adapter
in favor of httpx2. Current pinned httpx/TestClient behavior passes all tests. Do not
silence it; review the supported adapter during a future dependency update.

## Docker and CI status

Backend production build and running health smoke check PASS. Runtime UID is 10001;
HEALTHCHECK uses Python stdlib HTTP/JSON; no NASA or database access is required.
Existing development target compatibility is retained. No image was pushed.

Backend CI now runs without the old starter readiness bypass. It installs pinned
Python 3.12 development dependencies, lints, checks formatting, tests, validates and
audits dependencies, builds the image and smoke checks its non-root health.
Relevant main pushes/PRs plus manual invocation trigger it. Contents permission is
read-only; checkout/setup-python are SHA-pinned; checkout does not persist credentials.
The existing frontend, Docker-matrix and security workflows were preserved.

CI syntax and local constituent commands are verified. No GitHub-hosted workflow
run has occurred for these uncommitted changes. Deployment/branch protection/PR and
release administration were not changed. No external action is needed for local use.

## Contract decisions and teammate handoff

No API_SPEC/SRS text or implemented wire-contract deviation. Runtime region models
require actual ordered finite bounds and geometry provenance, unlike the schematic
null-bbox examples, following the specification's explicit production requirement.
The comparison response model includes shared_analyzed_years as required by the
specification's explanatory text; there is no comparison endpoint yet.
Pure request schemas check structure, not real dataset coverage or ten complete
years. Those checks depend on Harith's verified import and later integration.

Harith must supply validated immutable snapshots/manifests through the Phase 02
repository boundary. Gaja's statistical module remains independent. UI owners can
consume the error shape now and expect the catalog unavailable state until data
integration. Aiya retains small manual-QA/documentation responsibilities.
Future results will use a short-lived process-local cache: restart loses IDs (404),
and multi-replica operation is outside P0. No cache is implemented in Phase 01.

## Readiness checklist

- [x] Backend boots as a real FastAPI service.
- [x] Exact /health works independently of datasets.
- [x] Both catalogs honestly return structured 503 DATASET_UNAVAILABLE.
- [x] Typed request/response contracts and finite/null validation defined.
- [x] Structured errors, request tracing, safe logs and restricted CORS verified.
- [x] No database, fake runtime data or unsupported scientific endpoint.
- [x] Ruff, formatting, Pytest, pip check and dependency audit pass.
- [x] Docker production build and non-root/network-disabled health smoke pass.
- [x] Backend CI is ready to commit; syntax checked; remote execution pending.
- [x] Other five members' modules and all 15 original Markdown docs untouched.
- [x] Backend README provides truthful setup, endpoint and Docker instructions.
- [x] No commit/push/deploy and no Phase 02 work.

No remaining Phase 01 execution blocker. Local ensurepip setup was resolved; future
fresh hosts need a working Python venv installation. Remote CI and real-data/science
integration remain explicitly unverified. Stop here for phase review.

## Implementation references

- [FastAPI error handlers](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Starlette middleware ordering](https://www.starlette.io/middleware/)
- [Pydantic numeric configuration](https://pydantic.dev/docs/validation/latest/api/pydantic/config/)
