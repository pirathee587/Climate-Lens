# WARP.md — TerraTrend coding-agent and developer playbook

**Purpose:** Help developers using Warp or other coding assistants work safely and consistently on TerraTrend. **Important:** Warp uses root `AGENTS.md` (all caps) for automatically recognized project rules; this `WARP.md` is the detailed companion, not a substitute. See [Warp official docs](https://docs.warp.dev/getting-started/quickstart/coding-in-warp/).

## 1. Project identity and order of authority

- Product: TerraTrend, a NASA Earth observation trend investigator (student hackathon project, not affiliated with NASA).
- Timebox: 48-hour MVP. Default data: monthly IMERG Final precipitation, two *verified* region presets and complete years.
- Documentation priority: `docs/SRS.md` (requirements), `docs/SCOPE.md` (priority/gates), `docs/API_SPEC.md` (interface), `docs/SCIENTIFIC_METHOD.md` (method), `docs/DATA_SOURCES.md` (provenance), then code/tests. If docs conflict, raise an issue rather than silently guessing.
- Owner assignments are in `docs/TEAM_PLAN.md` and `docs/DELIVERY_PLAN.md`.

## 2. Agent-safe implementation workflow

1. **Read** relevant files and summarize requested changes, responsible owner, dependencies and acceptance criteria.
2. **Plan minimal changes** and identify tests required. Do not refactor unrelated modules.
3. **Implement only the requested task**. P0 is the limit unless explicitly authorized.
4. **Run targeted unit tests, lint and type checks**; report actual outputs and unsatisfied dependencies.
5. **Review the diff** for science errors, secrets, accidental dataset fabrication and missing docs.
6. **Present** changed files, key decisions, verification and limitations. Do not claim tests were run when they were not.

## 3. Coding standards

| Area | Rules |
|---|---|
| Python | Python 3.12 target; type hints, Pydantic schemas, short pure functions; `ruff` formatting/lint, `pytest` tests; document library versions in a lock or constraints file |
| FastAPI | Prefix `/api/v1`; standard error JSON; validate date bounds, source mode, region ID and alpha; write OpenAPI docs; async only where justified |
| TypeScript | Strict types; React function components; ESLint and Prettier; API types map to server schema; no statistical business logic in browser |
| Maps | Leaflet; WGS84 bbox `[west,south,east,north]`; clear preset-area label; attribution for base-map providers |
| Statistics | `mm/hr → mm/month → mm/year totals`; use actual calendar lengths; report `mm/year` trend slope; never substitute significance for causation |
| Data | Commit only permitted/suitably small verified snapshots; include checksums, metadata and source references; no pseudo-data in final demo |
| Security | No secrets in Git/client; `.env.example` contains placeholders only; server-held Earthdata credentials for any optional live data |

## 4. Proposed folders / ownership boundaries

```text
frontend/src/features/investigate/     # Shinthurie
frontend/src/features/charts/          # Shinthurie
frontend/src/features/regions/         # Kavishanth
frontend/src/features/compare/         # Kavishanth
backend/app/api/                       # Pirathee
backend/app/services/                  # Pirathee
backend/app/data/                      # Harith
backend/app/statistics/                # Gaja
backend/tests/                         # Each technical owner

data/demo/                              # Harith, genuine verified sources only

docs/                                   # Owner edits; Aiya helps review and QA
```

No folders above necessarily exist until development starts. Agent must not assume files exist solely from this guide.

## 5. Task-specific prompts for Warp

### Pirathee — API/backend
> Implement TT-05 using `docs/API_SPEC.md` and `docs/SRS.md`. Create typed FastAPI endpoints that validate region IDs and dates, load Harith's verified monthly snapshots, invoke Gaja's statistical function and respond with source metadata. Write API tests and deterministic error payloads. Do not invent observations or modify other members' modules without coordination.

### Harith — NASA ingestion
> Implement TT-02/TT-03 using `docs/DATA_SOURCES.md`. Obtain actual NASA GPM_3IMERGM monthly Final precipitation for two documented region bounding boxes and 2001–2024 if accessible. Verify original field units before converting. Export versioned CSV + provenance JSON + SHA-256 checksums and import tests. If NASA access fails, report the blocker; do not generate synthetic measurements and label them as NASA.

### Gaja — statistics
> Implement TT-04 using `docs/SCIENTIFIC_METHOD.md`. Write pure Python functions for annual complete-year totals, OLS, Theil–Sen slope and 95% CI, and Mann–Kendall. Add reference tests for rising/falling/constant signals, missing data, leap years and assumption warnings. Ensure the response never claims causation.

### Shinthurie — UI and charts
> Implement TT-06/TT-09 using `docs/API_SPEC.md`. Build a responsive React/TypeScript investigate screen with one real active variable, date range, monthly/annual plots, significance explanation, error/loading states, export and accessible labels. Integrate Kavishanth's map component instead of duplicating it. Do not hardcode trend figures.

### Kavishanth — maps/compare
> Implement TT-07/TT-08: create a Leaflet map showing the two *actual* verified preset regions, then a comparison view that calls `/api/v1/comparisons`. Show independent trend statistics for each region and synchronized year coverage. Do not label those bounding boxes as official districts or claim the slope difference is statistically significant.

### Aiya — smaller non-coding scope
> Review docs and the working demo using `docs/TEST_STRATEGY.md`. Maintain a concise manual QA checklist and issue reports with steps to reproduce. Verify attribution/links and coordinate a short demo walkthrough. Do not undertake a critical code dependency or change another person's implementation.

## 6. Pull request and verification template

```markdown
## GitHub issue / owner
TT-XX — [name]

## What changed
- ...

## Requirements covered
- FR-..., NFR-...

## NASA/analysis impact
- Dataset/version/run/unit/region changes? If no, say "None".

## Tests actually run
- [ ] unit tests — command + outcome
- [ ] API tests — command + outcome
- [ ] UI check — evidence
- [ ] data provenance and missing-data handling checked

## Known limitations
- ...
```

## 7. Stop conditions and escalation

- **No real source?** Stop scientific-demo claims; produce transparent failure state and seek a valid NASA download/workflow.
- **Mismatch in product version/units/ROI/year window?** Halt comparison; resolve with Harith and Gaja.
- **Too few valid years, missing data, or strong temporal dependence?** Mark the result insufficient/assumptions-limited; do not issue a definitive “significant” badge.
- **Contract change?** Pirathee updates API schema first and informs Shinthurie/Kavishanth.
- **Unexpected requests to add login, chatbot, live streaming or Kubernetes?** Mark P2 and do not proceed without explicit scope change.

## 8. Release gate

- Reproducible offline demo with *verified* NASA observations.
- Two locations, same data product/run/version and comparable time window.
- Correct period-to-total conversion and enough complete years.
- No statistically inaccurate claims; tests and CSV export working.
- Clearly labeled NASA attribution, data dates, source, and caveats.
- No secret keys or unlicensed assets committed.
