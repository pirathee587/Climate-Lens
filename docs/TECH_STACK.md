# Technology stack and development standards

**Principle:** proven, understandable open-source components with low operational overhead. Proposed versions must be pinned and smoke-tested by the team before implementation; these files do not claim tested compatibility.

## 1. Stack selection

| Layer | Chosen technology | Why | Owner | P0 status |
|---|---|---|---|---|
| UI framework | React + TypeScript + Vite | Fast modular SPA, strongly typed API usage | Shinthurie | Required |
| Styling | Tailwind CSS | Responsive layout and consistent component styling | Shinthurie | Required |
| Charts | Recharts | Responsive interactive time-series plots | Shinthurie | Required |
| Maps | Leaflet + React Leaflet | Transparent preset regions, interactive map, low complexity | Kavishanth | Required |
| Server | Python + FastAPI + Pydantic | Typed HTTP API and automatic OpenAPI spec | Pirathee | Required |
| Scientific computation | NumPy, SciPy, pandas | Reference statistics, time aggregation, validation | Gaja | Required |
| NASA preprocessing | Earthaccess, Xarray/NetCDF4 **or** verified Giovanni exports | Access/inspect and process actual NASA collections; use only what data path needs | Harith | Required offline preparation, optional packages |
| Data store | CSV + JSON manifest, hashes | Reproducibility and reliable offline demo | Harith | Required |
| Metadata persistence | SQLite / Python stdlib | Minimal result caching if needed | Pirathee | Optional |
| Tests | Pytest + httpx + React Testing Library/Vitest | Unit/API/component behavior | Each owner | Required |
| Quality | Ruff; ESLint/Prettier; TypeScript strict | Consistent, reviewable code | Each owner | Required |
| Source management | GitHub, PR review, Actions | Collaborative ownership, reproducible checks | Pirathee | Required workflow |
| Deployment | Static UI + single Python service | Easy demonstration and rollback | Pirathee | Required if public demo |
| Container tooling | Docker / Compose | Reproducible environment | Pirathee | P1 |
| Database scale-up | PostgreSQL + PostGIS | Geometry/history at larger scale | Future team | P2 |

**Do not add** Redis, Kafka, Kubernetes, Spring Boot, microservice orchestration, cloud data warehouses, login providers or AI agents to the MVP. Those create overhead without proving the central NASA science workflow.

## 2. Why not Java Spring Boot for v1?

Java remains appropriate for large enterprise API projects, but implementing a second Java process purely as a gateway to Python increases contracts, latency, deployment and handoffs. Use Python FastAPI as the primary backend because it directly hosts the scientific analysis. The team can evaluate Spring Boot after the challenge without rewriting the frontend HTTP contract.

## 3. Proposed source tree

```text
backend/
  app/
    main.py
    api/v1/{variables,regions,analyses,comparisons,exports}.py
    schemas/{common,analysis,source}.py
    services/{analyzer,comparison,export}.py
    data/{catalog,snapshot_loader,validation}.py
    statistics/{annual,regression,mann_kendall}.py
    core/{config,errors,logging}.py
  tests/{unit,integration}/
  requirements.txt        # proposed; pin after validation
  .env.example

frontend/
  src/
    app/
    api/
    components/
    features/{investigate,charts,regions,compare}/
    types/
  package.json
  package-lock.json        # commit after npm install
  vite.config.ts

data/demo/
  snapshots/              # real NASA-derived CSV only
  manifests/              # JSON metadata, checksums
  README.md
```

## 4. Proposed local setup (once files are implemented)

### Backend
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm ci
npm run dev
```

**Environment variable design (placeholders only):**

```env
# Backend
APP_ENV=development
APP_PORT=8000
ALLOWED_ORIGINS=http://localhost:5173
SNAPSHOT_ROOT=../data/demo
LOG_LEVEL=INFO
# NASA_EARTHDATA_USERNAME=...   # P1 only; secrets never committed
# NASA_EARTHDATA_PASSWORD=...   # P1 only; prefer secure credential handling

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

No frontend environment variable should contain a sensitive NASA token. Real `.env` is gitignored. For public hosting set HTTPS origins, secure secret storage and rate limits.

## 5. Developer quality commands (proposed)

```bash
# Backend
ruff check backend/
ruff format --check backend/
pytest -q backend/tests

# Frontend
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

These are contract targets for scripts, **not proof that a runnable project already exists**.

## 6. API contracts and code standards

- OpenAPI is the source of truth; API types in frontend should be generated or kept synchronized.
- Python: typed Pydantic models, explicitly returned status codes; pure scientific functions and minimal hidden mutable state.
- TypeScript: `strict: true`, controlled UI inputs, reusable components, explicit loading/error states.
- Conventions: English source code and docs, descriptive `snake_case` Python / `camelCase` TS, kebab-case branch names.
- Commit only tested behavior; PRs include requirement IDs and tests, particularly for NASA data/algorithm changes.

## 7. Performance strategy

- Use a one-time import to reduce a large global gridded product to small regional time series.
- Analyze only arrays of hundreds of monthly records rather than repeatedly downloading global satellite archives.
- Memoize data loading by `(manifest checksum, region)`; use the actual requested years in statistics.
- Display initial chart skeletons but do not show fabricated placeholder measurements as if computed.

## 8. Deployment checklist

- [ ] Run backend and UI test suites.
- [ ] Verify NASA product/run/version and manifest hashes.
- [ ] Backend CORS allows only frontend origin.
- [ ] Data files included or securely accessible to deployment.
- [ ] `/health` and `/api/v1/variables` return expected status.
- [ ] Live demo works with NASA disconnected.
- [ ] Map tiles/attribution follow provider terms.
- [ ] HTTPS, controlled logs and no exposed secrets.
- [ ] App claims only real supported variables and regions.

## 9. Official technology docs

- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/docs/
- Vite: https://vite.dev/guide/
- Tailwind: https://tailwindcss.com/docs/
- Recharts: https://recharts.org/
- Leaflet: https://leafletjs.com/reference.html
- React Leaflet: https://react-leaflet.js.org/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- pandas: https://pandas.pydata.org/docs/
- NumPy: https://numpy.org/doc/
- SciPy: https://docs.scipy.org/doc/scipy/
- Pytest: https://docs.pytest.org/
- Earthaccess: https://earthaccess.readthedocs.io/
- GitHub Actions: https://docs.github.com/en/actions
- Warp project rules: https://docs.warp.dev/getting-started/quickstart/coding-in-warp/
