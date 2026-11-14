# Project Overview — TerraTrend

**Project ID:** TT-NASA-2026 | **Status:** Design baseline, not yet built | **Revision:** 1.0 (14 November 2026)  
**Team:** Pirathee, Harith, Gaja, Shinthurie, Kavishanth, Aiya  
**Category:** Earth science visualization / statistical analytics | **Delivery:** 48-hour hackathon MVP

## Executive summary

TerraTrend is an interactive NASA Earth-observation trend explorer for learners and investigators. It combines an authentic, clearly attributed historical satellite dataset with time-series charts, geographic context and a justified trend significance calculation. Users select a supported area and analysis period and receive four interpretable findings: **what changes, where it changes, how much it changes and whether the trend is statistically significant** under stated assumptions.

The initial release deliberately narrows to **precipitation only**, using verified monthly records from the NASA GPM IMERG Final collection for two areas near Jaffna and Colombo. Both regional time series must use the same product version/run, a consistent aggregation method and a common complete-year analysis range. This focused scope gives the team enough time to validate the science instead of building a superficial all-variable dashboard.

## Problem, solution and value

| Dimension | Description |
|---|---|
| Problem | Earth observation trends require dataset selection, geospatial extraction, correct units, missing-data handling and statistical analysis. Students may mistake visual slopes for statistically supported trends. |
| Solution | One guided web workflow with authentic NASA data, verified regions, charts, OLS/Sen trend magnitude, Mann–Kendall inference, confidence intervals and plain-English cautions. |
| Primary user | High-school and university student investigating long-term environmental changes. |
| Secondary user | Educator, evaluator or citizen scientist wanting reproducible exploratory findings. |
| Differentiator | Built-in **source provenance + significance testing + two-region comparison**, not merely a static climate chart. |
| Research example | Compare the direction and magnitude of annual rainfall trends for a Jaffna-area and Colombo-area bounding box over verified complete calendar years. |
| Delivery principle | Small, reliable, offline-capable MVP with documented boundaries. |

## Goals and measurable outcomes

- **G1 — Reproducible data:** two NASA-derived snapshots with exact product ID, version, dates, ROI, units and SHA-256 hashes.
- **G2 — Correct analytics:** robust month/annual processing, OLS and Sen slope, 95% interval, and MK significance with explicit assumptions; reference tests pass.
- **G3 — Usable investigation:** user selects a supported region, reads monthly/annual chart and interpretation, downloads data.
- **G4 — Geographic comparison:** selected Jaffna and Colombo areas shown on map; paired analysis covers comparable years and independent results.
- **G5 — Reliable demo:** primary investigation and comparison work using local verified snapshots even when external NASA servers cannot be reached.
- **G6 — Responsible claims:** no measured value fabricated, no unsupported causal conclusion, no NASA endorsement asserted.

## Major deliverables

| ID | Output | Evidence |
|---|---|---|
| D-01 | SRS and API contracts | `SRS.md`, `API_SPEC.md` reviewed |
| D-02 | Verified NASA data pipeline | Two real snapshots + manifests after implementation |
| D-03 | Statistical service | Tested OLS / Sen / MK functions |
| D-04 | Web dashboard and regional map | Working UI backed by actual API |
| D-05 | Comparison and CSV export | Reproducible side-by-side results |
| D-06 | Test and presentation evidence | QA report and offline demo |

## Architecture summary

**React + TypeScript (frontend)** → **FastAPI/Python (API & statistics)** → **verified monthly NASA data snapshots + provenance JSON**. Leaflet maps show selected rectangles; Recharts renders the time series. Harith imports/validates satellite data, Gaja implements statistical inference, Pirathee integrates the services, Shinthurie builds the dashboard, Kavishanth builds the map/compare UI, and Aiya contributes a **small** QA/documentation/demo workstream.

## Business and scientific boundaries

This software is **exploratory educational analysis**, not a forecasting system, hazard alert, administrative-district precipitation report, climate-causation engine or official NASA product. Statistical significance alone does not establish practical significance or explain causes. Live data fetching, more variables and AI suggestions are future items.

## Key risks and safeguards

NASA Earthdata service migration/version changes → immutable snapshot manifest and verified access route. Data units or spatial aggregation mistakes → independent data validation and unit tests. Seasonal patterns and serial dependence → complete annual totals and clear inference warnings. Hackathon schedule → features gated by P0/P1/P2 and no extra architecture complexity.

## Document navigation

- Functional and quality requirements: [SRS](SRS.md)
- Scope and exclusions: [SCOPE](SCOPE.md)
- Architecture decisions/diagrams: [ARCHITECTURE](ARCHITECTURE.md)
- Technology selection: [TECH_STACK](TECH_STACK.md)
- Data access and citations: [DATA_SOURCES](DATA_SOURCES.md), [RESOURCES](RESOURCES.md)
- Six-member module plan: [TEAM_PLAN](TEAM_PLAN.md)
- API contracts: [API_SPEC](API_SPEC.md)
- Scientific methods: [SCIENTIFIC_METHOD](SCIENTIFIC_METHOD.md)
- Quality gates and GitHub issues: [TEST_STRATEGY](TEST_STRATEGY.md), [DELIVERY_PLAN](DELIVERY_PLAN.md)
