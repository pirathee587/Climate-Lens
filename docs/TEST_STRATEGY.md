# Test strategy, acceptance and quality assurance

**Test plan v1.0 | Scope: 48-hour P0 | Owner of testing:** every technical member. **Aiya's role:** small manual QA and demo support; not a replacement for developer tests.

## 1. Test levels and tools

| Level | Tools/methods | Responsible | Exit criterion |
|---|---|---|---|
| Data validation | Python scripts, manifest checks, SHA-256, spot checks | Harith | Real source and unit consistency verified |
| Unit tests | Pytest, SciPy reference results | Harith + Gaja | Critical conversion/stats tests pass |
| API integration | Pytest + httpx/TestClient | Pirathee | Correct data/schema/error responses |
| UI component | Vitest + React Testing Library | Shinthurie + Kavishanth | Key states/controls work |
| E2E smoke | Browser and curl; manual script | All; Aiya assists | Analyze, compare, export succeed |
| Security/config | Config review, secret scan | Pirathee | No tokens committed/exposed |
| Science review | Cross-check numbers and interpretation with external reference calculations | Gaja + Harith | No unreviewed statistical claims |

## 2. Critical functional cases

| ID | Requirement | Test case | Expected |
|---|---|---|---|
| TC-001 | FR-007 | 1 mm/hr across Feb 2023 | 672 mm total |
| TC-002 | FR-007 | 1 mm/hr across leap Feb 2024 | 696 mm total |
| TC-003 | FR-008 | One missing month | Exclude that year, explicit warning |
| TC-004 | FR-010 | Linear synthetic totals with slope +10 mm/year | Correct OLS slope |
| TC-005 | FR-011 | Linear synthetic totals with slope −5 mm/year | Sen slope −5, correctly computed CI |
| TC-006 | FR-012 | Stable synthetic series | No invented positive significance |
| TC-007 | FR-014 | Too few complete years | 422 or indeterminate (per API contract) |
| TC-008 | FR-002 | Two checked bbox presets | Map matches manifests |
| TC-009 | FR-003 | Unsupported dates | Structured 422; clear UI error |
| TC-010 | FR-004–005 | Valid NASA snapshot | Source ID, version/run, date, unit and hash returned |
| TC-011 | FR-009 | Unsorted input CSV | Backend returns chronological periods or rejects bad source |
| TC-012 | FR-017 | Compare two regions | Same source/run, shared years, independent stats |
| TC-013 | FR-018 | Download data | CSV parseable; rows/units/metadata retained |
| TC-014 | FR-019 | Invalid region ID | No 500; explicit error |
| TC-015 | FR-020 | API unavailable | Readable UI error, no indefinite loading |
| TC-016 | FR-021 | NASA Internet blocked | Prepared snapshot analysis works |
| TC-017 | FR-022 | Analysis appears significant | UI still discloses limitations/no causal claim |
| TC-018 | NFR-007 | Repo/deploy scanning | No Earthdata secrets in source/logs/browser |
| TC-019 | NFR-003/009 | 375px screen, keyboard only | Controls usable and labelled |
| TC-020 | FR-014 | Material serial dependence | Invalid naive-test assumption produces warning/indeterminate |

## 3. NASA source-to-UI reproducibility test

1. Select a verified snapshot with stored source URL, version/run, bbox, units and SHA-256 hash.
2. Independently inspect at least three timestamps/values and one annual total against the source transformation.
3. Run backend result and compare all returned monthly/annual totals with expected processed values.
4. Compare statistics to SciPy or independently verified reference formulas within documented tolerance.
5. Navigate UI and confirm chart axis units, period labels, numerical cards and warnings match API exactly.
6. Export CSV, reopen it, verify row count and values against the displayed analysis.
7. Switch to second region and verify comparison uses compatible years and source version.
8. Disconnect NASA access and rerun; no missing API at runtime for P0.

## 4. Performance and accessibility checks

- Measure p95 analysis latency for 20 cached local requests on documented laptop/runtime; proposed target **≤5 seconds**.
- Load UI at 375px and 1280px, check text overflow and map controls.
- Keyboards: `Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape` where relevant; chart results also available in readable text/table.
- Significance must not be communicated exclusively by red/green coloring.
- Failures must display actionable plain-language messages; no silent fallback to fake data.

## 5. Manual QA checklist — Aiya (smaller scope)

- [ ] Home page loads and clearly states this is a student prototype.
- [ ] Precipitation definition and source visible; disabled future variables not clickable.
- [ ] Jaffna-area and Colombo-area presets map to verified correct rectangles.
- [ ] Analyze Jaffna: charts show real sourced months/years.
- [ ] Numeric slope, p-value, confidence interval and sample years displayed with units.
- [ ] Compare Colombo: both regions displayed, years aligned, no unsupported cross-region significance claim.
- [ ] CSV downloads; rows and headers readable.
- [ ] Invalid date / no valid data gives friendly error message.
- [ ] NASA attribution and scientific limitations visible.
- [ ] Mobile width and keyboard navigation checked; screenshot issues logged.

For each bug log: issue title, environment, steps to reproduce, expected, actual, screenshot/log, severity, owner. Aiya does **not** have to write automated tests or change critical backend code.

## 6. Release / presentation exit gate

- [ ] All P0 features from SCOPE.md complete or openly declared incomplete.
- [ ] Source is genuine NASA-derived data and provenance reproducible.
- [ ] Four core challenge questions directly answered by UI.
- [ ] No misleading 'significance' claims, fabricated numbers, or unsupported attribution.
- [ ] Backend + UI build checks pass, critical tests green.
- [ ] No P0-severity bug known at presentation time.
- [ ] Offline demo verified and explanation prepared for dataset choice + caveats.
- [ ] NASA resources/license and map attribution correctly handled.

## 7. Requirements traceability

`SRS.md` section 10 maps SRS requirement ranges to test levels and GitHub issues. Every PR should name at least one `FR-` or `NFR-` ID, or mark itself as documentation/infrastructure with rationale. Every P0 requirement must have a demonstrated manual or automated acceptance test before final release.
