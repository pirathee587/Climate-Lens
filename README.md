# TerraTrend — Climate Lens

TerraTrend investigates regional precipitation trends using a FastAPI backend and
NASA-derived, independently reviewed snapshots. The backend owns annual aggregation,
OLS/Sen/Mann–Kendall analysis, comparison and CSV/provenance exports. React/Vite UI,
charts and maps belong to their frontend owners. Trend evidence does not prove a cause
or a significant difference between regional slopes.

**Phase 05: infrastructure ready for validation; full frontend integration is blocked.**
This branch has the working Phase 01–04 backend and Phase 05 container/CI preparation.
The real frontend scaffold is still on `feat/tt-06-frontend-scaffold`; main contains
map/comparison components but no package.json, lockfile or Vite entry point. It has
not been automatically merged or replaced. Independently reviewed real NASA artifacts
and quality policies are also missing: production health is 200, catalogs and valid
analysis/comparison requests return 503 DATASET_UNAVAILABLE. No fake NASA fallback.

## Start the available backend

```bash
docker compose config --quiet
docker compose up --detach --build --wait backend
curl http://127.0.0.1:8000/health
docker compose down --timeout 15
```

Requires a Docker runtime supporting no-new-privileges and Compose 2.24.4+. Current
local Snap Docker has a documented flag incompatibility; exact hosted validation
and any local diagnostic limits are recorded in the Phase 05 report. Starting the
whole stack remains blocked until the real frontend is merged and verified.

For local Python setup, development Compose, environment variables, browser API URL,
CORS, read-only snapshots, cache constraints and troubleshooting, read
[deployment preparation](docs/DEPLOYMENT.md) and [backend instructions](backend/README.md).
No deployment has occurred and no database is required.

## APIs and verification

The backend implements health, verified variable/region catalogs, analysis,
independent regional comparison, application-local result retrieval, monthly/annual
CSV and metadata downloads. See [API contracts](docs/API_SPEC.md). Result IDs expire
and are lost on restart; use one backend worker. Each scientific result retains
actual source metadata, complete-year counts and inference warnings.

```bash
python3 scripts/check_compose.py
python3 -m unittest discover -s scripts/tests -v
bash scripts/smoke-stack.sh production backend
bash scripts/smoke-stack.sh development backend
```

Backend lint/tests/audit instructions: [backend README](backend/README.md).
Frontend checks and full-stack smoke are NOT TESTED while its scaffold is absent.
Workflow readiness success does not establish frontend test/build success.

## Team and requirements

- Pirathee: FastAPI integration, Docker/Compose, CI and deployment preparation.
- Harith: genuine NASA acquisition, transformations, provenance and snapshots.
- Gaja: statistical engine and scientific validation.
- Shinthurie: frontend scaffold, dashboard, API client and charts.
- Kavishanth: map, region selection and comparison interface.
- Aiya: supplementary manual QA, documentation and demo support.

[Scope](docs/SCOPE.md), [SRS](docs/SRS.md), [architecture](docs/ARCHITECTURE.md),
[scientific methods](docs/SCIENTIFIC_METHOD.md), [sources](docs/DATA_SOURCES.md),
[test strategy](docs/TEST_STRATEGY.md), [team plan](docs/TEAM_PLAN.md) and
[delivery plan](docs/DELIVERY_PLAN.md) describe requirements and ownership. Older
baseline documents contain proposed architecture; current phase reports distinguish
implemented behavior from missing source data and integration prerequisites.

[Phase 03 report](backend/PHASE03_REPORT.md) ·
[Phase 04 report](backend/PHASE04_REPORT.md) ·
[Phase 05 report](backend/PHASE05_REPORT.md)

No frontend, data or statistics ownership is transferred by infrastructure changes.
Full browser E2E, verified-source offline demonstration and release acceptance remain
later work; no cloud deployment, PR or main merge is performed by Phase 05 delivery.
