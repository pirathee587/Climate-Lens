/**
 * ⚠️ SYNTHETIC TEST FIXTURES — NOT NASA DATA. ⚠️
 *
 * Shape-only payloads used to exercise UI states in unit/integration tests.
 * Numbers are arbitrary round values, bounding boxes are deliberately fake
 * (not real Jaffna/Colombo extents), and nothing here is imported by
 * application code under src/. Never copy these into a demo or snapshot.
 */
import type {
  AnalysisResponse,
  ErrorResponse,
  RegionDescriptor,
  RegionsResponse,
  VariablesResponse,
} from "../../src/types/api";

export const SYNTHETIC_LABEL = "SYNTHETIC TEST FIXTURE";

export const syntheticVariables: VariablesResponse = {
  variables: [
    {
      id: "precipitation",
      display_name: "Precipitation",
      description: `${SYNTHETIC_LABEL} variable description`,
      source_dataset_id: "TEST_COLLECTION",
      source_version: "TEST",
      source_run: "Final",
      aggregation_units: "mm",
      time_resolution: "monthly",
      first_available_period: "2001-01",
      last_available_period: "2012-12",
      supported: true,
    },
  ],
};

const syntheticRegionA: RegionDescriptor = {
  id: "jaffna_area",
  name: "Test region A",
  bbox: [10, 10, 11, 11],
  label_type: "bbox_area_near_city",
  geometry_source: SYNTHETIC_LABEL,
};

export const syntheticRegions: RegionsResponse = {
  regions: [
    syntheticRegionA,
    {
      id: "colombo_area",
      name: "Test region B",
      bbox: [20, 20, 21, 21],
      label_type: "bbox_area_near_city",
      geometry_source: SYNTHETIC_LABEL,
    },
  ],
};

const years = Array.from({ length: 12 }, (_, i) => 2001 + i);

export const syntheticAnalysis: AnalysisResponse = {
  analysis_id: "00000000-0000-4000-8000-000000000000",
  request: {
    variable_id: "precipitation",
    region_id: "jaffna_area",
    start_year: 2001,
    end_year: 2012,
    alpha: 0.05,
    source_mode: "verified_snapshot",
  },
  region: syntheticRegionA,
  source: {
    collection_id: "TEST_COLLECTION",
    version: "TEST",
    run_type: "Final",
    original_variable: "test_variable",
    original_unit: "mm/hr",
    snapshot_id: "synthetic-test-snapshot",
    snapshot_sha256: "0".repeat(64),
    retrieved_at: "2026-01-01T00:00:00Z",
    source_uri: "https://example.invalid/synthetic",
    aggregation_method: SYNTHETIC_LABEL,
  },
  monthly: years.flatMap((year) =>
    Array.from({ length: 12 }, (_, m) => ({
      period: `${year}-${String(m + 1).padStart(2, "0")}`,
      // One deliberately missing month to exercise gap handling.
      precipitation_total_mm: year === 2005 && m === 3 ? null : 100,
      valid_fraction: year === 2005 && m === 3 ? null : 1,
    })),
  ),
  annual: years.map((year) => ({
    year,
    precipitation_total_mm: year === 2005 ? null : 1200,
    valid_months: year === 2005 ? 11 : 12,
  })),
  statistics: {
    sample_years: 11,
    ols_slope_mm_per_year: 1,
    ols_r_squared: 0.5,
    sen_slope_mm_per_year: 2,
    sen_slope_ci95_mm_per_year: [-1, 3],
    mann_kendall_p_value: 0.5,
    mann_kendall_method: "two-sided-original-on-annual-totals",
    alpha: 0.05,
    direction: "increasing",
    significance_status: "not_significant",
    assumptions_status: "adequate",
  },
  warnings: [`${SYNTHETIC_LABEL} warning: 2005 excluded (11/12 months).`],
  algorithm_version: "synthetic-test",
};

export function errorBody(code: string, message: string): ErrorResponse {
  return {
    error: {
      code,
      message,
      details: {},
      request_id: "11111111-1111-4111-8111-111111111111",
    },
  };
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
