# Project scope, MVP boundaries and acceptance

**Baseline:** SCOPE-1.0 | **Challenge:** Earth Systems Trend Detective | **Timebox:** 48-hour hackathon.

## 1. Problem and target outcome

Finding a statistically defensible trend in Earth observations ordinarily requires dataset discovery, spatial subsetting, time processing, unit conversions and appropriate statistical testing. TerraTrend packages those steps into a simple reproducible investigation for student users.

The MVP target is **regional long-term precipitation trends**, not a general Earth science platform. The general platform is the roadmap, not the 48-hour commitment.

## 2. P0: Must-have features (release gate)

| ID | Feature | Concrete deliverable | Owner | Acceptance |
|---|---|---|---|---|
| P0-01 | NASA data provenance | Real IMERG Final monthly product and source metadata | Harith | Two documented snapshots with NASA collection/version/run/date/units, verification path and no fabricated observations |
| P0-02 | Region presets | Jaffna-area and Colombo-area *bounding boxes*, clearly labeled | Kavishanth | Visible on map, server validates selected supported IDs |
| P0-03 | Data transformation | Monthly rate → total (where required) → annual total | Harith | Leap years correct, no silent missing-data imputation, tests |
| P0-04 | Statistics | OLS, Theil–Sen slope + CI, Mann–Kendall p-value | Gaja | Deterministic reference tests pass, outputs correctly labeled |
| P0-05 | API | Variables, regions, analysis, compare, CSV, health | Pirathee | OpenAPI published by FastAPI, consistent 4xx/5xx errors |
| P0-06 | Investigate screen | Variable info, region/year selection, chart, findings | Shinthurie | Responsive UI renders verified results and source attribution |
| P0-07 | Geographic compare | Compare two preset regions with independent results | Kavishanth | Shows synchronized years and independent slope/p-value |
| P0-08 | Integrity | Limitations, assumption warnings, coverage/quality flags | Gaja + Harith | No false statistical significance claims or fabricated evidence |
| P0-09 | Reliability | Offline demo with local verified snapshots | Pirathee | Demo usable with NASA network inaccessible |
| P0-10 | Release QA | Unit/integration/E2E smoke checks and demo walkthrough | Each owner; Aiya assists | Checklist passes; no severe known bug |

**Note:** Region rectangle drawing is *not* mandatory for P0. Map markers/rectangles show actual preset areas. Support for any arbitrary user-drawn box is P1 because real data extraction would otherwise be unavailable.

## 3. P1: Only after P0 passes

- Optional bounded rectangular ROI extraction from the installed monthly source, subject to limits and sufficient cached coverage.
- Refresh selected observations from an approved NASA Cloud interface with Earthdata credentials held server-side.
- PDF or static image report; one more verifiable regional preset.
- Responsive polish, accessibility improvements beyond the baseline, Docker Compose packaging.

## 4. P2: Explicitly excluded from this hackathon

- AI recommendations or chatbots; forecasts, predictions, flood-risk alarms.
- User accounts, logins, roles, payments, social features or collaboration.
- Live satellite streaming, 30-minute processing, data lakes or geospatial big-data clusters.
- All-variable scientific catalogs; temperature, vegetation, streamflow and soil moisture integration.
- Pixel-level statistical significance maps or formal cross-region slope-difference inference.
- Automated attribution of observed changes to climate change or a particular cause.
- Mobile app, complex Docker/Kubernetes distributed architecture, and large-scale PostGIS infrastructure.

## 5. P0 operational constraints

- **Region type:** curated NASA-derived preset bounding boxes in WGS84, presented as **areas near** city names unless certified district polygons are used. Example bounds are design placeholders until Harith verifies actual extraction coordinates.
- **Data:** same GPM IMERG collection/version/run for all P0 comparisons; **2001–2024** proposed default and must be validated against snapshot timestamps and availability.
- **Temporal output:** monthly totals and complete annual totals; not an annual mean precipitation *rate*.
- **Min valid series:** at least 10 complete calendar years for exploratory testing; recommend at least 15+ for meaningful interpretation. The UI should display sample size and caution about short series.
- **Significance:** default two-sided alpha 0.05. State any violation of independence/autocorrelation assumptions and suppress a definitive significance label when assumptions are not met.
- **Internet:** backend may be offline for demo; no automated external data refresh is guaranteed.
- **User data:** no profiles, tracking or personally identifiable data required.

## 6. Definition of done

Each feature is complete only when: code is merged; acceptance criteria met; unit/integration tests passed as applicable; a clear error and empty state exists; API schema or screenshot/demo evidence provided; NASA provenance kept accurate; reviewer has approved the PR.

## 7. Non-goals and change control

Requirements identified as P1/P2 are not implementation obligations. For a new feature: create a GitHub issue, specify user value, dependencies and science impact, estimate effort, and explicitly move another task out of scope if needed. Pirathee manages the integration freeze and approval of interface changes. NASA dataset/version changes require joint Harith/Gaja approval and rerunning validation.
