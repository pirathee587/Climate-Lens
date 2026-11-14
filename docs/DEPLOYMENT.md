# TerraTrend runtime and deployment preparation

Phase 05 prepares local containers and CI. No cloud deployment has occurred.
**Frontend/full-system integration is blocked:** `main` does not yet contain
`frontend/package.json`, its lockfile or `index.html`. The real scaffold is on
Shinthurie's `feat/tt-06-frontend-scaffold`; do not generate a replacement or merge
that branch automatically. Real NASA demonstration readiness is separately blocked
by absent independently reviewed source artifacts and quality policies.

## Prerequisites

- Python 3.12 with venv/ensurepip for local development and HTTP smoke scripts.
- Docker Engine with working non-root containers and `no-new-privileges` support.
- Docker Compose 2.24.4 or newer. The development override uses `!override` to replace
  port/mount lists. See [Docker merge rules](https://docs.docker.com/reference/compose-file/merge/).
- When the real frontend is merged: Node 22.12 or newer within the Node 22 series,
  npm, the committed package-lock.json and the owner's actual Vite application.
- Ports 8000 and 5173 are loopback-only defaults. Choose other host ports in `.env`
  if occupied; update browser API URL and CORS origin together.

## Local Python and Node setup

From the repository root:

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --no-access-log
```

The app reads process environment, not `.env` files implicitly. `backend/.env.example`
is a reference; export reviewed settings explicitly when using local Python. Default
empty approvals keep catalogs/analysis/comparison unavailable while health stays 200.
No database is required. See [backend configuration](../backend/README.md).

After the frontend owner supplies the real reviewed scaffold, in another terminal:

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test -- --run
npm run build
npm run dev -- --host 127.0.0.1
```

These frontend commands are presently **blocked**, not verified build instructions
for the current branch. Do not create placeholder manifests to make them pass.

## Compose environment

Optional root `.env` is Compose interpolation input; start from `.env.example`.
Never commit a real `.env`, NASA credentials or reviewed approval records. Avoid
printing expanded Compose configurations containing operator configuration; use
`docker compose config --quiet`. Example defaults contain no approved data.

| Setting | Default / meaning |
|---|---|
| BACKEND_HOST_PORT | 8000, mapped from localhost to container 8000 |
| FRONTEND_HOST_PORT | 5173, mapped to production 8080 or development 5173 |
| VITE_API_BASE_URL | http://localhost:8000/api/v1, browser-facing public URL |
| ALLOWED_ORIGINS | http://localhost:5173, exact browser origin(s), comma-separated |
| SNAPSHOT_HOST_PATH | ./data/demo; existing immutable artifact root |
| SNAPSHOT_APPROVALS | [] JSON array of independently reviewed descriptor fingerprints |
| SNAPSHOT_QUALITY_POLICIES | [] JSON array of reviewed snapshot-bound flag policies |
| RESULT_CACHE_TTL_SECONDS | 1200, bounded 1..86400 |
| RESULT_CACHE_MAX_ENTRIES | 100, bounded 2..1000 |
| LOG_LEVEL | INFO |

APP_ENV, APP_PORT=8000 and SNAPSHOT_ROOT=/data/demo are set by Compose. The development
override changes APP_ENV. An explicitly empty ALLOWED_ORIGINS denies browser origins.
The API's existing validators reject invalid settings. Do not invent flags, coverage
thresholds, timestamps, geometry or hashes to activate data.

Production Vite configuration is a **build argument** baked into public assets;
changing an Nginx environment variable after build does not change those assets.
Development Vite receives VITE_API_BASE_URL as process environment. Never place
secrets in a VITE_ variable. If ports/hosts change, rebuild production frontend and
set the exact frontend origin in backend CORS. Browser requests use localhost/public
API hostname, never the Compose-only service name `backend`. Both containers still
share the isolated Compose default network. A same-origin proxy is a future hosting
choice, not implemented here; the supplied Nginx config rejects `/api/` rather than
returning HTML as a fake API response.

## Production configuration and backend-only run

```bash
docker compose config --quiet
docker compose up --detach --build --wait backend
curl http://127.0.0.1:8000/health
docker compose logs --tail=100 backend
docker compose down --timeout 15
```

Backend production runs as UID 10001, explicit one Uvicorn worker, no database and no
runtime downloader. Root filesystem and snapshot mount are read-only; `/tmp` is
bounded tmpfs. All Linux capabilities are dropped and no-new-privileges is enabled.
`/docs` and `/openapi.json` are disabled. Logging is structured; no query strings,
request bodies, credentials or raw exceptions are emitted. Nginx access logs are
disabled in the supplied configuration.

Once the real frontend is merged, reviewed and its tests/build pass, the complete
production command is `docker compose up --detach --build --wait`. This is currently
**blocked**. Frontend listens internally on 8080 and serves static assets as its
existing unprivileged image user. Nginx config supplies SPA fallback, separate
missing-asset404 and no API proxy. Its syntax is independently checked against the
unprivileged Nginx base image; that check is not a frontend application build.

Frontend depends on backend being healthy. This only waits for liveness, **not NASA
readiness**. [Docker startup ordering](https://docs.docker.com/compose/how-tos/startup-order/)
describes `service_healthy`. Frontend/backend health probes never approve datasets.

## Development configuration

```bash
docker compose -f compose.yaml -f compose.dev.yaml config --quiet
docker compose -f compose.yaml -f compose.dev.yaml up --detach --build --wait backend
docker compose -f compose.yaml -f compose.dev.yaml logs --tail=100 backend
docker compose -f compose.yaml -f compose.dev.yaml down --timeout 15
```

Backend `/app/app` is a read-only source bind mount; Uvicorn reload observes host
changes. Snapshot volume stays read-only. Development docs are enabled. When real
frontend exists, omit `backend` to start both services: source/public mounts are
read-only, Vite listens on 0.0.0.0:5173, and its non-root container filesystem remains
writable for node_modules/.vite. Production has no application source mounts.
Frontend Dockerfile is preserved while its source application is absent. The
owner scaffold already fixes /app/node_modules permissions by running npm ci as
USER node; retain that fix when the owner merges it.

## Snapshot preparation and approval

SNAPSHOT_HOST_PATH must already exist; Compose does not create an accidental empty
mount directory. It maps to `/data/demo:ro`. Maintain the Harith-generated bundle
layout: source artifacts, normalized snapshots, manifests/envelopes and descriptors,
with the relative references recorded by the real importer. Do not rename artifacts
independently of their descriptors. Keep source acquisition credentials outside the
bundle and outside Docker build contexts.

Harith supplies authentic source bytes, actual units, geometry, coverage, conversion
and reproducible processing. Independent review supplies descriptor fingerprints
and provenance evidence. Scientific/data owners approve snapshot-bound quality
flags and any coverage threshold. Configure those approvals in ignored runtime
settings; do not bake them into images. Files must remain immutable while serving.
Missing, corrupt or inconsistent artifacts fail 503 DATASET_UNAVAILABLE. Approved
source configuration is not established merely by finding files or matching a hash.
No synthetic production snapshots are supplied.

## Smoke checks and CI

```bash
python3 scripts/check_compose.py
python3 -m unittest discover -s scripts/tests -v
bash scripts/smoke-stack.sh production backend
bash scripts/smoke-stack.sh development backend
```

Smoke script uses an isolated project, empty approval/policy arrays, temporary host
ports and cleanup traps. It builds the requested target, checks UID 10001, module
imports, read-only snapshot writes, container-local and host-visible HTTP, CORS,
structured 503/404/422 errors and docs mode. It removes only its own containers and
network; images remain cached. It never activates synthetic data or changes source
content. Health is 200, catalogs/valid analysis/comparison503, unknown result/download
UUIDs404. Existing backend tests verify successful cache retrieval and CSV using
isolated artificial fixtures; the unconfigured-container smoke does not claim that
successful scientific-data path.

After the real frontend is available:

```bash
bash scripts/smoke-stack.sh production full
bash scripts/smoke-stack.sh development full
```

Full mode refuses to run when package.json/lockfile/index.html are absent. It uses
localhost 18000/15173 by default, injects matching Vite/CORS configuration, and checks
frontend HTML/assets and production SPA fallback. SMOKE_BACKEND_HOST_PORT and
SMOKE_FRONTEND_HOST_PORT can select other fixed full-mode ports. HTTP checks do not
prove React rendering, graphs or browser interaction: actual browser E2E and frontend
unavailable-state verification remain Phase 06 prerequisites.

Backend CI runs Python checks/audit, smoke checker unit tests, production build and
an exact no-new-privileges offline container smoke. Docker CI validates both Compose
variants and runs production/development backend Compose smoke. When real scaffold
exists it additionally builds/smokes both full-stack variants. Frontend CI requires
npm ci, lint, typecheck, non-watch tests, production build and high-severity audit.
Absent frontend jobs are explicitly **skipped / NOT TESTED**, even if readiness jobs
and the overall workflow conclude success. Security workflow scans history and tree.
Actions use pinned SHAs and read-only repository permissions; images are not published.

## Frontend contract handoff

- `frontend/src/features/compare/comparisonTypes.ts`: add required
  `shared_analyzed_years: readonly number[]`; align side analysis request and
  geometry_source fields with backend AnalysisResponse, and nonnull verified bbox /
  retrieval timestamp types. Existing permissive types are not proof of integration.
- `frontend/src/features/compare/comparisonValidation.ts`: consume returned shared
  years, not a fresh client-side eligibility decision. Preserve backend warnings
  disclosing differing regional sample sets; no slope-difference significance claim.
- On the remote scaffold, `frontend/src/types/api.ts` already mirrors the backend
  shared-year field, nullable values and errors. Its optional annual ols_fitted_mm
  remains pending backend contract work, so the fitted line is unavailable.
- Remote `frontend/src/api/client.ts` already uses the selected browser-visible
  default and GET export route, and unwraps structured errors. Coordinate cached-ID
  expiry, optional annual/metadata download UI and unavailable state with its owner.
- Review/merge the actual frontend branch, including its non-root Docker ownership
  fix. Do not remove backend fields or silently edit teammate-owned React/API code.

## Troubleshooting, shutdown and release limitations

- Dataset 503 with health 200 is expected without real approved bundles; do not treat
  liveness as readiness or substitute fabricated graphs.
- Unknown, expired, evicted or restarted analysis IDs return 404. Cache TTL/capacity
  are bounded; retained JSON limits are 2 MiB per entry /32 MiB total. Exactly one backend
  worker is used: cache IDs are not shared across processes/replicas. Restart loses IDs.
- CORS requires exact scheme/hostname/port. localhost and 127.0.0.1 are distinct origins.
  Vite variables are public; a Docker service DNS name is not browser-resolvable.
- `no-new-privileges` must work on the host runtime. On the current local Snap Docker,
  enabling it causes `exec /usr/local/bin/python: operation not permitted`. A minimal
  Python probe isolated that incompatibility. Keep the committed restriction; fix the
  runtime or use a compatible Engine/VM before relying on local hardened startup.
  Diagnostic local runs that omit the flag are not hardened-profile validation.
- Root filesystem is intentionally read-only. Only `/tmp` is writable in production;
  prepare snapshots outside the API and mount them read-only. Fix host permissions
  for UID 10001 reading artifacts rather than switching to root.
- Use `docker compose down --timeout 15`; add both `-f` flags for development. Do not
  run unrelated project cleanup or delete source artifacts. Containers handle SIGTERM
  through their foreground application processes; no init wrapper is required.

No TLS termination, public hostname, hosting account, paid infrastructure, deployment
credentials, public port exposure, cloud resources or deployment workflow is created.
Future hosting needs a reviewed HTTPS/browser URL and CORS strategy, compatible Docker
runtime, genuine immutable reviewed bundles, frontend integration and real browser
E2E/security/science acceptance. A same-origin reverse proxy or replica-wide cache
requires a separately authorized design. No real-data offline demo or release is claimed.
