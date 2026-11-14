# Team plan: six people, bounded responsibilities

**Team:** Pirathee, Harith, Gaja, Shinthurie, Kavishanth, Aiya.  
**Intent:** five technical modules; the sixth member **Aiya** has a deliberately smaller, non-critical-path scope. All timelines are proposed parallel hackathon work blocks, not promises.

## 1. Responsibility table

| Member | Workstream | Must deliver | Not responsible for | Relative scope |
|---|---|---|---|---|
| **Pirathee** | Backend + system integration | FastAPI project, typed schemas, endpoints, error design, integration, CORS, health, final demo deployment | Scientific formula authoring, manual NASA extraction | Large |
| **Harith** | Data engineering | Authenticated/approved access or Giovanni extraction, verified NASA monthly dataset, two ROI snapshots, metadata JSON, `mm/hr` conversion, coverage checks | User-facing frontend | Large |
| **Gaja** | Statistical engine | OLS/Sen/MK implementations, CI, assumptions, stable tests, interpretation schema | NASA collection downloads, React UI | Medium |
| **Shinthurie** | Dashboard UX | React shell, variable selector, date picker, results cards, monthly/annual charts, loading/error/empty states, CSV download | Map geometry and statistical algorithms | Medium |
| **Kavishanth** | Geospatial and comparison | Leaflet map with precise preset bounding boxes, regions service integration, compare screen with synchronized plots | Data extraction and analysis calculations | Medium |
| **Aiya** | Light documentation + QA + demo support | Review README, create manual QA checklist, test guided user flow, register bugs, record demo steps and acknowledgements | Core API, science engine, NASA ingestion, CI ownership | **Small** |

### Aiya — limited checklist (complete without code changes)

1. Maintain a 1-page UI/manual QA checklist: choose Jaffna, analyze, view provenance, compare Colombo, export CSV, test invalid inputs.
2. Review the project README for accuracy and working source links; report broken docs links.
3. Capture 3–5 screenshots only after genuine data appears and identify any placeholders.
4. Help assemble a 60–90-second walkthrough and keep issue status up to date.
5. Log observed issues (steps to reproduce, expected/actual, screenshots); owners fix their respective modules.

**No high-risk feature, dataset integration, coding deadline, or final release approval is dependent solely on Aiya.**

## 2. Boundaries and interfaces

- **Harith → Pirathee/Gaja:** schema-defined `monthly_series.csv` plus provenance JSON, region ID, valid-month flags, product version and units. Harith owns conversion correctness.
- **Gaja → Pirathee:** `analyze_annual(years, totals_mm, alpha)` typed function or Pydantic model, tested with synthetic references. Gaja owns statistical correctness.
- **Pirathee → frontend:** frozen OpenAPI JSON response, error model and stable endpoint paths. Pirathee owns compatibility and integration tests.
- **Kavishanth → Shinthurie:** `<RegionSelector>` and `<ComparisonPanel>` reusable UI components; **only** Kavishanth renders Leaflet map selection and comparison.
- **Shinthurie:** overarching app layout and data fetching shared hook; no duplicate analysis formulas in browser.
- **Aiya:** validates features end to end without taking over owner tasks.

## 3. RACI (R = responsible, A = accountable, C = consulted, I = informed)

| Decision/deliverable | Pirathee | Harith | Gaja | Shinthurie | Kavishanth | Aiya |
|---|---|---|---|---|---|---|
| Architecture/API contracts | A/R | C | C | C | C | I |
| NASA product, provenance | C | A/R | C | I | C | I |
| Scientific accuracy | C | C | A/R | I | I | I |
| Main dashboard | C | I | C | A/R | C | I |
| Map and compare UI | C | C | C | C | A/R | I |
| Final release integration | A/R | R | R | R | R | C |
| Manual QA and docs polish | A | C | C | C | C | R |

## 4. Suggested GitHub issue ownership (see DELIVERY_PLAN.md)

| Issue | Owner | Dependency |
|---|---|---|
| TT-01 repository bootstrap and schema | Pirathee | — |
| TT-02 NASA dataset verification | Harith | — |
| TT-03 snapshots and provenance | Harith | TT-02 |
| TT-04 science functions and unit tests | Gaja | TT-01; sample data interface |
| TT-05 FastAPI analysis/compare endpoints | Pirathee | TT-01, TT-03, TT-04 |
| TT-06 React scaffold/results UI | Shinthurie | TT-01 API schema |
| TT-07 maps and preset region selector | Kavishanth | TT-01 region schema |
| TT-08 comparison frontend | Kavishanth | TT-05, TT-07 |
| TT-09 results charts and CSV UX | Shinthurie | TT-05, TT-06 |
| TT-10 verification and provenance UX | Harith + Gaja | TT-03, TT-04 |
| TT-11 CI/integration/release | Pirathee | TT-05, TT-08, TT-09 |
| TT-12 manual QA, demo guide, docs check | Aiya | first working UI; not blocking backend |

## 5. Lightweight teamwork rules

- `main` is protected; feature branches `feat/tt-xx-short-name`, `fix/tt-xx-short-name`, `docs/tt-xx-short-name`.
- Prefer a small PR per issue. All PRs include: scope, test evidence, example screenshot/API response (when relevant), data version impact.
- Resolve merge conflicts and contract changes before presentation; no new features in the final 8 hours.
- No fabricated NASA measurements, invented p-values, or AI-generated data passed as authentic.
- Update one source-of-truth task board; no one needs to claim future features are complete.

## 6. Suggested 48-hour parallel plan

| Interval | Backend | NASA data | Science | Frontend | Maps/compare | Aiya |
|---|---|---|---|---|---|---|
| H0–H10 | Bootstrap, contracts | Product/ROI validation | Functions + tests | Shell, UX mock | Map scaffold | Read SRS/checklist |
| H10–H20 | Analysis API | Two verified snapshots | Validate on real data | Chart integration | Presets and region selector | Start manual smoke tests |
| H20–H32 | Compare/API/export | Provenance and coverage | Interpretations/caveats | Results refinements | Compare UI | Report bugs/docs review |
| H32–H40 | Integration fixes/CI | Freeze sources | Cross-check results | Bug fixes | Bug fixes | Demo run and screenshots |
| H40–H48 | Release and presentation | Assist defense | Explain methods | Present UI | Present map | Coordinate walkthrough |
