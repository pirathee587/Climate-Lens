# Software Requirements Specification (SRS)

**Project:** TerraTrend — Earth Systems Trend Detective  
**Version:** 1.0 | **Status:** Proposed/baselined for build | **Date:** 2026-11-14  
**Requirements approach:** IEEE/ISO/IEC 29148-inspired structure; adapted to a short NASA Space Apps Challenge implementation. This is **not an IEEE certification**.  
**Product owner / integrator:** Pirathee | **Scientific reviewers:** Harith and Gaja  
**Related:** [Scope](SCOPE.md), [Architecture](ARCHITECTURE.md), [API](API_SPEC.md), [Science](SCIENTIFIC_METHOD.md), [Verification](TEST_STRATEGY.md).

## 1. Introduction

### 1.1 Purpose
Specify a consistent, testable set of functional and nonfunctional requirements for a browser-based Earth-science trend investigation application. The software helps users discover, display and evaluate regional changes in authentic satellite-derived environmental observations.

### 1.2 Problem statement
Scientific datasets have many variables, different spatial and temporal resolutions, seasonal patterns and missing values. Without an integrated workflow, a learner may incorrectly infer a trend from a plot or misread a significance test. The product must provide verified time-series data, clear units, trend magnitude, significance and limitations for a region.

### 1.3 Vision and scope
The *general vision* is a flexible Earth-science trend explorer. The **release v1.0 MVP** implements only **GPM IMERG Final monthly precipitation** for two supported region presets, with a reproducible offline data source. A two-region comparison is included. No AI model is required. `SCOPE.md` controls mandatory versus stretch priorities.

### 1.4 Intended audience and stakeholders
- **Primary users:** high-school / university learners, hackathon judges, scientifically curious public.
- **Secondary users:** educators and students practicing remote sensing and statistics.
- **Build stakeholders:** Pirathee (integration), Harith (data), Gaja (science), Shinthurie (UI), Kavishanth (maps), Aiya (light QA/docs).
- **External stakeholders:** NASA data providers as cited sources, not as sponsors or approving entities.

### 1.5 Definitions
| Term | Meaning |
|---|---|
| Variable | Scientific measure being investigated; for MVP, precipitation |
| ROI | Region of interest, here a supported geographic bounding box |
| BBox | `[west, south, east, north]` in WGS84 longitude/latitude degrees |
| IMERG | NASA's Integrated Multi-satellitE Retrievals for GPM |
| Time series | Observations aggregated and ordered over historical time |
| OLS | Ordinary least squares linear regression |
| MK | Mann–Kendall nonparametric trend significance test |
| Sen/Theil–Sen | Median of pairwise slopes, with confidence limits when supported |
| p-value | Measure of evidence against a specified no-trend null hypothesis, under model/test assumptions |
| alpha | Chosen decision threshold, default 0.05 |
| Complete year | Calendar year with 12 valid monthly totals for the selected region |
| Snapshot | Real NASA-derived, locally stored dataset with reproducible provenance |
| P0/P1/P2 | Mandatory / optional / deferred scope classes |

### 1.6 References
See [RESOURCES.md](RESOURCES.md). The original supplied NASA challenge description supplies the four objectives: identify variables; retrieve regional data; show long time series; statistically evaluate rate/significance. This SRS refines that challenge into a feasible hackathon scope.

## 2. Overall system description

### 2.1 Product perspective
Single-page browser app calling a stateless HTTP JSON service. Backend loads an authenticated/prepared, versioned NASA data snapshot and computes statistical analyses. Optional server metadata storage uses SQLite. No user account or personalized profile is required.

### 2.2 User classes
| ID | User | Skills | Needs |
|---|---|---|---|
| U-01 | Student investigator | Basic graphs and numbers | Guided UI, tooltips, clear units, explain results |
| U-02 | Educator or judge | Comfortable with science concepts | Reproducible data source, visible methods, exported CSV |
| U-03 | Data developer | Python/data processing | Snapshot generation and provenance |
| U-04 | Maintainer | Full-stack engineer | Logs, stable schema, automatic tests |

### 2.3 Assumptions and dependencies
- Internet access is needed for **initial** official NASA data retrieval or Giovanni use, but not for the P0 demo runtime.
- Data product variable and units must be validated against **downloaded file metadata**, not assumed from generic product descriptions.
- Study periods and real region bounding boxes are confirmed during preprocessing.
- V07 Final record was announced to end in September 2025; the MVP intentionally targets earlier complete years. V08 availability should be verified independently before future upgrades.
- Source code, real observations and data transformation scripts do **not** exist in this docs-only package.

### 2.4 Operating environment
Modern Chromium/Firefox/Safari desktop and responsive mobile browser; Python 3.12 target, FastAPI server, React + TypeScript + Vite client. Local offline snapshot/data cache; managed cloud hosting optional.

### 2.5 Constraints
- 48-hour hackathon build, six-member team and limited external API reliability.
- Data must be geospatially and temporally comparable across regions.
- Significance tests require an adequate time span and disclosed assumptions.
- No external service accounts should be exposed to browsers or committed to Git.
- Student prototype must be labeled as such; not an official NASA interface.

## 3. Use cases and required flows

### UC-01 — Inspect supported data
**Actor:** learner. **Precondition:** app running. **Trigger:** open investigation page. **Main flow:** display active precipitation variable, definition, product, expected units, available verified date range and data source. **Postcondition:** user knows what can be investigated. **Exceptions:** no snapshot => show unavailable state, no invented data.

### UC-02 — Investigate one region
**Actor:** learner. **Precondition:** verified snapshot exists. **Main flow:** choose Jaffna-area or Colombo-area preset; choose available full-year span; click Analyze; backend validates request, filters regional monthly records, produces monthly/annual totals, statistics and provenance; frontend shows charts, findings and warnings. **Exceptions:** invalid range (422), fewer than 10 complete years (422), missing snapshot (503/404 as specified), backend timeout (retry option).

### UC-03 — Compare two regions
**Actor:** learner. **Main flow:** choose two distinct supported presets and one common date range; app requests paired analysis; plots synchronized time ranges, independent results, and region labels with maps. **Exceptions:** incompatible source/version/run, unequal valid year coverage; show explicit warning or refuse invalid comparison.

### UC-04 — Download results
**Actor:** learner. **Main flow:** export the time series, annual totals, source metadata and scientific method summary. CSV export must include units and definitions in accompanying metadata. **Exceptions:** no completed analysis => disable export; missing result => 404.

### UC-05 — Recover gracefully from data/assumption issues
**Actor:** learner. **Main flow:** see concise human-readable status, issue type and next step. The system must not display a "significant" conclusion if data or a required model assumption is invalid.

## 4. Functional requirements

**Rule:** `FR-###` identifiers remain stable through issue tracking. P0 = required, P1 = stretch. Every P0 row is testable.

| ID | Priority | Requirement | Acceptance test / observable behavior | Owner |
|---|---|---|---|---|
| FR-001 | P0 | System shall present a catalog with only supported active variables; precipitation must be selectable and defined | GET variables reports `supported=true`; UI labels definition and output unit | Pirathee + Shinthurie |
| FR-002 | P0 | System shall provide two **real-data-backed** region presets with WGS84 bounding boxes | Region endpoint returns distinct IDs and checked bounds; map displays exact extents | Kavishanth + Harith |
| FR-003 | P0 | System shall restrict date selection to verified data coverage, with default 2001–2024 if validated | Out-of-range request rejected with machine-readable error; dates match snapshots | Pirathee |
| FR-004 | P0 | Backend shall read versioned NASA-derived snapshots, not a mock generator | Integration test confirms retrieved observations match committed/source-stored fixtures and manifest | Harith + Pirathee |
| FR-005 | P0 | Every result shall show source collection, version, run, variable name, original units, retrieval date, snapshot ID and region | Result includes source metadata and UI attribution | Harith + Shinthurie |
| FR-006 | P0 | System shall preserve missing values, reject invalid observations and report monthly quality/coverage | Missing month not replaced with zero; warning returned and UI shown | Harith |
| FR-007 | P0 | For original mean precipitation rate in `mm/hr`, system shall compute each month’s total using actual calendar hours | Fixed rate of 1 mm/hr gives 672 mm for non-leap Feb 2023 and 696 mm for leap Feb 2024 | Harith |
| FR-008 | P0 | Annual rainfall total shall sum exactly 12 valid monthly totals; incomplete years excluded and reported | Eleven-month year not analyzed as complete annual total | Harith + Gaja |
| FR-009 | P0 | System shall return monthly/annual time-series arrays in chronological order with explicit units | API schema passes; UI charts match returned periods | Pirathee + Shinthurie |
| FR-010 | P0 | System shall calculate OLS trend slope for annual totals in `mm/year` | Synthetic known-slope tests pass within numeric tolerance | Gaja |
| FR-011 | P0 | System shall calculate Sen's slope and a labeled 95% slope confidence interval | Reference comparison with SciPy `theilslopes` succeeds | Gaja |
| FR-012 | P0 | System shall perform a two-sided Mann–Kendall monotonic-trend significance test with configurable alpha, default 0.05 | Increasing/decreasing/constant cases and p-value behavior tested | Gaja |
| FR-013 | P0 | System shall disclose sample length and cautions about short series, ties, data quality and serial dependence | Warnings visible in result and API; no unconditional conclusion | Gaja |
| FR-014 | P0 | System shall classify outcome as `significant`, `not_significant` or `indeterminate` using verified test status | Invalid assumptions or insufficient data produce `indeterminate` | Gaja + Pirathee |
| FR-015 | P0 | UI shall show both monthly totals and annual totals plus direction, slope, p-value and method | Both charts and labeled numeric cards visible with actual data | Shinthurie |
| FR-016 | P0 | System shall show two preset areas on an interactive, attributed map | Bounds, names and map provider attribution displayed | Kavishanth |
| FR-017 | P0 | System shall compare **independent** analysis outputs from two regions over one requested period | Side-by-side charts/statistics; no false inference on difference between slopes | Kavishanth + Pirathee |
| FR-018 | P0 | System shall export completed series and provenance as CSV plus JSON metadata | Download has timestamps, units, region, product/version/run and warnings | Pirathee + Shinthurie |
| FR-019 | P0 | APIs shall return structured errors and an application health result | Errors contain `code`, `message`, optional `details`, `request_id` | Pirathee |
| FR-020 | P0 | UI shall display loading, empty, successful and error states; labels and keyboard controls present | Manual QA verifies all states, no silent spinners | Shinthurie + Aiya |
| FR-021 | P0 | Offline demo shall succeed after snapshots are prepared, without contacting NASA at runtime | Network-disabled smoke test passes for analysis and compare | Pirathee |
| FR-022 | P0 | Results shall state that NASA data are estimates, analysis is exploratory, and trend significance does not imply causation | Visible disclaimer and per-result limitation | Gaja + Shinthurie |
| FR-023 | P1 | User may select an arbitrary bounded rectangle if matching backend data can be extracted | Custom ROI analysis succeeds from supported source, not a placeholder | Kavishanth + Harith |
| FR-024 | P1 | Backend may refresh data using Earthdata Cloud with secure server-side credentials | Network test verifies official source and secret isolation | Harith + Pirathee |
| FR-025 | P1 | App may export a PDF scientific report | PDF includes charts, sources, units, caveats | Shinthurie |

### 4.1 Business rules

- BR-01: **No unsupported dataset** can be chosen as if active.
- BR-02: **Never fabricate measurements** or p-values. Synthetic test data must be clearly marked and never present in the final investigation result.
- BR-03: Regions must use identical collection/version/run, aligned requested years, and documented spatial method to be comparable.
- BR-04: Default significance threshold = 0.05, two-sided. P-values are neither probabilities the hypothesis is true nor indicators of practical importance.
- BR-05: If data-quality assumptions or serial correlation make a naive p-value unreliable, display a caution and `indeterminate` rather than overstate the conclusion.
- BR-06: Claims about city *areas* must not be promoted to official district-level facts without district boundaries and the appropriate areal aggregation.
- BR-07: NASA credentials are held server-side; never sent to browsers.

## 5. Nonfunctional requirements (measurable)

| ID | Category | Requirement / proposed measurement | Evidence |
|---|---|---|---|
| NFR-001 | Availability | P0 snapshot demo operates without NASA connectivity | Offline integration test |
| NFR-002 | Response time | On a typical 2026 development laptop and loaded local snapshots, one cached analysis returns within 5 seconds at p95 over 20 trials | Timed test results; hardware documented |
| NFR-003 | UI responsiveness | Main dashboard responds at 375px and 1280px browser widths with no overlapping controls | Visual/manual QA |
| NFR-004 | Accuracy | Unit conversion agrees with hand-calculated reference cases; statistical results pass regression/reference tests | Pytest fixtures |
| NFR-005 | Reproducibility | A data manifest includes source, retrieval, processing steps, SHA-256 hashes, ROI and exact date range | Manifest check |
| NFR-006 | Validation | All API requests enforce Pydantic schema, known regions and supported dates, alpha in `(0,1)` | Invalid-input API tests |
| NFR-007 | Security | No tokens/credentials in Git, UI, API responses or logs; CORS restricted by environment | Secret scan/review |
| NFR-008 | Observability | Every request logs timestamp, endpoint, duration, status and request ID without data-access secrets | Log inspection |
| NFR-009 | Accessibility | Keyboard operability, focus visibility, accessible labels, sufficient contrast; charts include readable table/summary | Manual audit |
| NFR-010 | Maintainability | Python/TS type checking and linting; module boundaries and public APIs documented | CI/PR checks |
| NFR-011 | Integrity | Missing months, coverage and questionable test assumptions cannot be silently suppressed | Regression tests |
| NFR-012 | Compatibility | Current Firefox and Chromium on desktop; mobile viewport usability | Browser smoke tests |
| NFR-013 | Explainability | Show method, slope units, p-value, interval, n and caveats in every analysis | QA checklist |
| NFR-014 | Data consistency | Comparison always uses the same source version/run and explicit common years | Integration tests |
| NFR-015 | Portability | Local environment uses documented commands and sample `.env.example`; no hard-coded absolute paths | Fresh-clone smoke test |
| NFR-016 | Privacy | No accounts/PII required; optional server logs exclude IP retention by default unless hosting demands it | Config review |

## 6. External interface requirements

### 6.1 Browser interface
- Investigate screen: supported variable definition, region preset picker/map, date controls, Analyze button and source attribution.
- Results: two time-series charts, numeric metrics, sample size, significant/not/indeterminate label, caveats and export.
- Compare: side-by-side independent region findings with synchronized period. Map attribution visible.
- Accessible loading/error/empty states, keyboard focus and non-color-only significance encoding.

### 6.2 HTTP service
See [API_SPEC.md](API_SPEC.md). JSON REST under `/api/v1`, standardized status codes, stable error schema, automatic OpenAPI schema. MVP read-only analysis plus optional ephemeral cache.

### 6.3 Dataset interface
Verified snapshot canonical columns `region_id, period, precipitation_total_mm, valid_fraction, observation_status`, accompanied by manifest containing source units, whether conversion took place, acquisition details, bbox, time convention, algorithm version, checksums, and attribution. If snapshots contain mean rates rather than totals, use explicit alternate schema and a documented conversion step; do **not** double-convert.

### 6.4 External dependencies
NASA Earthdata / Giovanni for preparation, GPM data product documentation, Leaflet map tiles under provider terms, standard scientific Python libraries. Live remote API calls are optional P1.

## 7. Data requirements and logical entities

| Entity | Fields | Invariants |
|---|---|---|
| DatasetManifest | `dataset_id`, `collection_id`, `version`, `run_type`, `source_url`, `variable`, `original_unit`, `derived_unit`, `retrieved_at`, `transform_version`, `checksums` | Source metadata immutable for given snapshot hash |
| RegionPreset | `region_id`, `name`, `bbox`, `label_type`, `geometry_source` | Bounding boxes valid WGS84 and checked |
| MonthlyObservation | `region_id`, `period`, `total_mm`, `coverage_fraction`, `quality_flag` | Unique region+period in snapshot; finite nonnegative rainfall except explicit missing |
| AnnualObservation | `region_id`, `year`, `total_mm`, `valid_month_count` | Only 12-month years enter analysis |
| AnalysisResult | `analysis_id`, `region`, `date_range`, `statistics`, `source`, `warnings` | Reproducible for same snapshot, algorithm version and request |
| ComparisonResult | `left`, `right`, `shared_period`, `limitations` | Two independently computed region results; common data product/version |

**Data retention:** source snapshot and manifest stored versioned; analysis results may be in-memory or short-lived SQLite. No personal user data is needed. Delete or regenerate analytical caches without changing the canonical source data.

## 8. Statistical requirements and caveats

1. Use actual year/calendar time as `x`, not unlabeled list index where years may be missing.
2. Compute annual totals from **12** valid months only, and report excluded years.
3. OLS estimates annual total trend (`mm/year`), not instantaneous precipitation rate.
4. Report Sen slope and its 95% interval with a method label; a confidence interval is not a guarantee.
5. A two-sided MK test evaluates a monotonic temporal trend under statistical assumptions. Use diagnostics, especially persistence/autocorrelation, and state limitations.
6. Never claim a significant difference between two regional slopes without a separate validated two-sample inference method.
7. An observed trend is not evidence of a specific underlying mechanism without independent research.

Complete algorithm and unit-test detail: [SCIENTIFIC_METHOD.md](SCIENTIFIC_METHOD.md).

## 9. Acceptance scenarios (system-level)

| Scenario | Given | When | Then |
|---|---|---|---|
| AT-01 | Official verified snapshots | User investigates Jaffna-area | Real monthly/annual data appear with product metadata |
| AT-02 | Verified Colombo and Jaffna snapshots | User compares both | Shared years and independent statistics are displayed |
| AT-03 | 1 mm/hour mean rate in Feb 2024 | Converted | Total = 696 mm |
| AT-04 | An 11-month calendar year | Aggregate annual | Year excluded and warning returned |
| AT-05 | Deterministic increasing annual synthetic series in tests | Compute trend | Positive slope with validated test output |
| AT-06 | Constant series or too few years | Compute significance | No invented strong-significance claim |
| AT-07 | Unsupported region | Request analysis | Valid structured error, not server crash |
| AT-08 | NASA service unavailable, local snapshot present | Run demo | Both investigate and compare still work |
| AT-09 | User exports results | Open CSV and manifest | Units, region, source and year range preserved |
| AT-10 | Statistically questionable series | Display analysis | Explicit assumptions warning and indeterminate classification where appropriate |

## 10. Requirement-to-test traceability

| Requirement set | Planned tests | GitHub issues |
|---|---|---|
| FR-001–003 | API catalog/region/date validation + UI smoke | TT-01, TT-06, TT-07 |
| FR-004–008 | Provenance, conversion, leap-year, incomplete-year | TT-02, TT-03, TT-10 |
| FR-009–014 | Known-series statistics, short/constant data, API schema | TT-04, TT-05 |
| FR-015–018 | Chart/compare/export integration + browser QA | TT-06, TT-08, TT-09 |
| FR-019–022 | API errors, offline, ethics/caveats, accessibility | TT-05, TT-11, TT-12 |
| NFR-001–016 | Reliability, accuracy, performance, quality and security checks | TT-10, TT-11, TT-12 |

## 11. Risk, prioritization and sign-off

Top risks are NASA access/migration, unit confusion, too-short records, inappropriate significance conclusions, data provenance gaps, and frontend/backend integration delays. Mitigation: verified offline snapshots first, fixed schema, unit tests, science review, scope freeze and no P2 work. Detailed risk register: [DELIVERY_PLAN.md](DELIVERY_PLAN.md).

### Approval checklist (proposed)

- [ ] Pirathee confirms backend and integration requirements are implementable.
- [ ] Harith confirms selected NASA source, product, source variable and conversion.
- [ ] Gaja confirms statistical methods and interpretation constraints.
- [ ] Shinthurie/Kavishanth confirm UI/API mapping and map labels.
- [ ] Aiya reviews that manual QA/demo is concise and scope is manageable.

**Change procedure:** Update SRS version and affected requirement IDs; document rationale; update API and tests; note product scope impact in GitHub issue. No approval has been asserted in this documentation package.
