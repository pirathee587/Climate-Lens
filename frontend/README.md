# TerraTrend frontend

React 18 + TypeScript (strict) + Vite 7 + Tailwind 3 + Recharts + React Leaflet.
Owners: Shinthurie (shell, investigate, charts — TT-06/TT-09), Kavishanth
(regions map, comparison — TT-07/TT-08).

## Commands

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173 (expects the API on :8000)
npm run lint
npm run typecheck
npm run test -- --run
npm run build
```

Configure the API with `VITE_API_BASE_URL` (see `.env.example`). It must never
contain credentials.

> **Windows note:** if Vitest reports "Cannot read properties of undefined
> (reading 'config')", the folder was opened with a lowercase drive letter
> (`c:\`). Run the tests from `C:\...` instead. CI on Linux is unaffected.

## Layout

| Path                                             | Purpose                                                                                      |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| `src/types/api.ts`                               | TypeScript mirror of `backend/app/schemas/*` (source of truth: backend + `docs/API_SPEC.md`) |
| `src/api/client.ts`                              | Typed fetch client; every failure becomes `ApiError` carrying the backend error envelope     |
| `src/app/`                                       | App root, Investigate/Compare tabs, adapters into feature-owned types                        |
| `src/features/investigate/`                      | Variable card, region/year/alpha form, provenance panel                                      |
| `src/features/charts/`                           | Monthly/annual charts, trend cards, warnings, data table, CSV export                         |
| `src/features/regions/`, `src/features/compare/` | Kavishanth's map, selector and comparison panel                                              |
| `tests/`                                         | Unit + integration tests; `tests/fixtures/synthetic.ts` is **synthetic, not NASA data**      |

## Data integrity rules

- The UI only displays values returned by the backend; it computes no statistics.
- `null` values render as `—`, never `0`. Missing months are chart gaps.
- While the backend has no verified snapshot it returns `503 DATASET_UNAVAILABLE`,
  and the UI shows that state rather than placeholder numbers.
- Synthetic fixtures live only under `tests/` and are never imported by `src/`.
