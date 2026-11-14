# Gaja TT-10 — Scientific Data, Conversion, and Interface Audit Report

## 1. Status and Scope

**AUDIT MODULE & SCIENTIFIC INTERFACE VERIFICATION COMPLETE; REAL-DATA SIGN-OFF PENDING HARITH SNAPSHOTS.** 14 November 2026.

- **Owner:** Gaja (Statistical Analysis & Scientific Validation), in coordination with Harith (`TT-02`/`TT-03`/`TT-10`).
- **Branch:** `feat/tt-10-gaja-scientific-audit`
- **Requirements Covered:** `FR-007`, `FR-008`, `FR-010`, `FR-011`, `FR-012`, `FR-013`, `FR-014`, `FR-015`, `FR-017`, `FR-022`, `NFR-004`, `NFR-011`, `NFR-013`, `NFR-014`.
- **Scientific Integrity Statement:** All test observations in automated unit tests are explicitly labeled synthetic verification fixtures. No fabricated NASA observations or real-world regional climate claims are made.

---

## 2. Delivered Scientific & Audit Enhancements

1. **`backend/app/statistics/audit.py`** (exported via `backend/app/statistics/__init__.py`):
   - `verify_monthly_conversion(period, raw_value, original_units, reported_total_mm)`: Independently verifies `FR-007` calendar-month conversion (`mm/hr * 24 * actual_days_in_month`, including leap-year February `696h` vs non-leap `672h`) and prevents double-conversion when `original_units` is already `mm` or `mm/month`.
   - `verify_annual_sum(year, monthly_totals_mm, reported_total_mm)`: Independently verifies `FR-008` complete 12-month summation via `math.fsum` and rejects incomplete (<12 month) calendar years.
   - `audit_regional_trend(monthly, *, policy, year_range, alpha, diagnostic_alpha)`: Executes the end-to-end `TT-10` aggregation, trend analysis, first-complete-year spot-check, OLS fitted series generation, and guardrail invariant checks (confirming non-causation warnings and `indeterminate` gating whenever lag-1 residual dependence or assumption checks fail).
2. **OLS Fitted Trend Line Helpers in `backend/app/statistics/models.py`**:
   - Added `OLSResult.fitted_mm(year)` and `TrendResult.ols_fitted_mm(year)` / `TrendResult.ols_fitted_series()` so the backend can populate `AnnualItem.ols_fitted_mm` for analyzed complete years without duplicating regression arithmetic outside `app.statistics`.
3. **Automated `TT-10` Unit & Reference Test Suite (`backend/tests/unit/test_tt10_scientific_audit.py`)**:
   - Covers `ST-01`..`ST-10` and `TC-001`..`TC-020` conversion checks, double-conversion rejection, 12-month completeness enforcement, OLS fitted series accuracy, and end-to-end cross-checks against `scipy.stats.linregress`, `scipy.stats.theilslopes`, and `pymannkendall.original_test`.

---

## 3. Cross-Module Interface & Frontend Guardrail Audit (`TT-10`)

Audited the backend services (`analysis_service.py`, `comparison_service.py`, `export_service.py`) and frontend displays (`frontend/src/features/compare/` and `origin/feat/tt-06-frontend-scaffold`) against `docs/SCIENTIFIC_METHOD.md` and `docs/SRS.md`:

| Requirement / Guardrail | Backend & Frontend Verification | Audit Result |
|---|---|---|
| **FR-007** (`mm/hr` → `mm` conversion) | `imerg_processor.py` and `audit.py` use `24 * calendar.monthrange(year, month)[1]` for `mm/hr` and preserve `mm` / `mm/month` unchanged. | **PASS** |
| **FR-008** (12 valid months only) | `annual_aggregation.py` and frontend `series.ts` (`isCompleteYear`) exclude `<12` valid-month years and report excluded years explicitly. | **PASS** |
| **FR-010 / AGENTS.md** (No browser math) | Frontend `AnnualChart.tsx` never computes regression in TypeScript; `TrendResult.ols_fitted_series()` provides backend-authoritative fitted values. | **PASS** |
| **FR-011** (Sen slope + 95% CI label) | `TrendSummary.tsx` and `ComparisonStats.tsx` explicitly label `"Sen slope 95% CI"` in `mm/year`. | **PASS** |
| **FR-013 / FR-014** (`indeterminate` gate) | Lag-1 Ljung–Box residual dependence, gapped years, or constant/exact-linear residuals force `significance_status = "indeterminate"`. | **PASS** |
| **FR-017** (Independent two-region compare) | `comparison_service.py` and `ComparisonPanel.tsx` state that separate regional tests do not test whether the two slopes differ significantly. | **PASS** |
| **FR-022 / BR-06** (Non-causation & BBox) | `caveats.ts` (`STANDING_CAVEATS`), `TrendSummary.tsx` (§9 copy template), and `export_service.py` (`scientific_limitations`) include all required disclaimers. | **PASS** |

---

## 4. Joint Harith + Gaja Real-Data Sign-Off Checklist (When `data/demo` Snapshots Arrive)

Before activating `SNAPSHOT_APPROVALS` and `SNAPSHOT_QUALITY_POLICIES` in production:

- [ ] **Source & Version Lock:** Both `jaffna_area` and `colombo_area` manifests specify `collection_id = "GPM_3IMERGM_07"`, `version_label = "V07B"`, `run_type = "Final"`, and matching `spatial_aggregation`.
- [ ] **Unit Verification:** Confirm `original_units` in raw export metadata (`mm/hr` vs `mm/month`) and run `verify_monthly_conversion` on at least 3 monthly timestamps (including a leap-year February).
- [ ] **Annual Sum Spot-Check:** Run `verify_annual_sum` on at least 1 complete calendar year per region (`abs_diff_mm <= 1e-9`).
- [ ] **Quality Policy Attestation (`ReviewedQualityPolicy`):** Bind each region's `output_sha256` to `accepted_quality_flags: ["valid"]`, agreed `minimum_valid_fraction`, and a `ProvenanceReview` timestamped after `retrieved_at_utc`.
