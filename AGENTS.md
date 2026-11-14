# AGENTS.md — TerraTrend repository agent rules

> **Warp recognizes this uppercase file as project-scoped rules.** Read `WARP.md` for the fuller workflow and `docs/SRS.md` for product requirements.

## Mission and limits
- Build the **48-hour MVP** described in `docs/SCOPE.md`: real NASA IMERG precipitation, two verified region presets, time series, annual trends, independent region comparison, and CSV.
- Do **not** implement out-of-scope P1/P2 features without a task issue and explicit permission.
- Do **not** fabricate observations, significance values, citations, region geometries or test results. Never substitute mocked data for a real-data deliverable without conspicuous labels.
- `NASA Earthdata` credentials must never appear in source, browser bundles, logs, test fixtures, or Git history.

## Structure and stack
- Proposed future monorepo: React/TypeScript/Vite frontend; FastAPI/Python backend; versioned real-data snapshots; SQLite metadata if needed.
- Backend owns scientific calculations, conversion, dataset metadata and validation; frontend only displays returned results.
- Keep interfaces aligned with `docs/API_SPEC.md`; changes to API payloads must update schema, tests, SRS traceability and the frontend client.

## Development protocol
1. Identify the GitHub issue and owner from `docs/DELIVERY_PLAN.md` before editing.
2. Read affected documentation and existing tests; explain planned files and constraints.
3. Make minimal scoped changes; preserve agreed filenames and stable contracts.
4. Add or update tests: unit conversion, leap-year handling, missing data, statistics, API validation, UI empty/error states.
5. Run targeted checks locally and report exactly what passed/failed; no claims without evidence.
6. Update docs for changed behavior; submit a PR summary with tests and source provenance.

## Scientific integrity
- Verify **variable units in file metadata**. For monthly mean rainfall rate in `mm/hr`, monthly `mm = rate × 24 × actual_days_in_month`.
- Annual totals require 12 valid monthly totals. No silently filled months.
- OLS and Sen slope must have `mm/year` units; a p-value is not an effect size or causal evidence.
- Use data product/version/run consistently across comparison regions and warn when assumptions (serial correlation, short period, measurement quality) limit confidence.
- City-area rectangles are **not district boundaries**; do not label as administrative districts without official polygons.

## Quality, security and communication
- Typed Python and TypeScript interfaces, small functions, descriptive names, consistent error JSON, formatters/linters.
- Prefer reproducible offline snapshots over a fragile network-dependent demo.
- No secrets, arbitrary shell scripts from remote websites, or destructive repo commands.
- Never create external services, GitHub issues, commits or deployments without explicit user/team authorization.
- Do not claim an implementation already exists; this package is documentation only until code is written.
