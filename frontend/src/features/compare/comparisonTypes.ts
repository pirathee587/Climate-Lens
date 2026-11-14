export const COMPARISON_REGION_IDS = ["jaffna_area", "colombo_area"] as const;
export const DEFAULT_ALPHA = 0.05;
export const VERIFIED_SOURCE_MODE = "verified_snapshot" as const;

export type ComparisonRegionId = (typeof COMPARISON_REGION_IDS)[number];

export interface ComparisonRegion {
  id: ComparisonRegionId;
  name: string;
}

export interface ComparisonRequest {
  variable_id: "precipitation";
  left_region_id: ComparisonRegionId;
  right_region_id: ComparisonRegionId;
  start_year: number;
  end_year: number;
  alpha: number;
  source_mode: typeof VERIFIED_SOURCE_MODE;
}

export interface ComparisonPeriod {
  start_year: number;
  end_year: number;
}

export interface ComparisonDatasetCompatibility {
  same_product: boolean;
  same_version: boolean;
  same_run: boolean;
}

export interface ComparisonRegionSummary {
  id: ComparisonRegionId;
  name: string;
  bbox: readonly [number, number, number, number] | null;
  label_type: string;
}

export interface ComparisonMonthlyRecord {
  period: string;
  precipitation_total_mm: number | null;
  valid_fraction: number | null;
}

export interface ComparisonAnnualRecord {
  year: number;
  precipitation_total_mm: number | null;
  valid_months: number;
}

export type SenSlopeConfidenceInterval = readonly [
  number | null,
  number | null,
];

export interface ComparisonStatistics {
  sample_years: number | null;
  ols_slope_mm_per_year: number | null;
  ols_r_squared: number | null;
  sen_slope_mm_per_year: number | null;
  sen_slope_ci95_mm_per_year: SenSlopeConfidenceInterval;
  mann_kendall_p_value: number | null;
  mann_kendall_method: string;
  alpha: number;
  direction: "increasing" | "decreasing" | "no_clear_direction" | null;
  significance_status: "significant" | "not_significant" | "indeterminate";
  assumptions_status: string;
}

export interface ComparisonSourceMetadata {
  collection_id: string;
  version: string;
  run_type: string;
  original_variable: string;
  original_unit: string;
  snapshot_id: string;
  snapshot_sha256: string;
  retrieved_at: string | null;
  source_uri: string;
  aggregation_method: string;
}

export interface IndependentComparisonAnalysis {
  analysis_id: string;
  region: ComparisonRegionSummary;
  monthly: readonly ComparisonMonthlyRecord[];
  annual: readonly ComparisonAnnualRecord[];
  statistics: ComparisonStatistics;
  source: ComparisonSourceMetadata;
}

/** Mirrors POST /api/v1/comparisons from docs/API_SPEC.md. */
export interface ComparisonResponse {
  shared_requested_period: ComparisonPeriod;
  /** Backend-provided intersection of complete years; optional for adapter compatibility. */
  shared_analyzed_years?: readonly number[];
  dataset_compatibility: ComparisonDatasetCompatibility;
  left: IndependentComparisonAnalysis;
  right: IndependentComparisonAnalysis;
  warnings: readonly string[];
}

export interface ComparisonApiError {
  code?: string;
  message: string;
  details?: Record<string, unknown>;
  request_id?: string;
}

export type CompareRequest = (
  request: ComparisonRequest,
) => Promise<ComparisonResponse>;
