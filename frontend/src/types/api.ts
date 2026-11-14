/**
 * TypeScript mirrors of the backend Pydantic contracts.
 *
 * Source of truth: backend/app/schemas/{common,source,analysis}.py and
 * docs/API_SPEC.md. Any change there must be reflected here in the same PR.
 * Scientific values that are undefined are explicit `null` — never NaN.
 */

export type BBox = readonly [
  west: number,
  south: number,
  east: number,
  north: number,
];

/** `YYYY-MM` monthly period string. */
export type Period = string;

export interface HealthResponse {
  status: "ok";
  service: "terratrend-api";
  api_version: "v1";
}

export interface ErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
  request_id: string;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface VariableDescriptor {
  id: "precipitation";
  display_name: string;
  description: string;
  source_dataset_id: string;
  source_version: string;
  source_run: "Final";
  aggregation_units: "mm";
  time_resolution: "monthly";
  first_available_period: Period;
  last_available_period: Period;
  supported: true;
}

export interface VariablesResponse {
  variables: VariableDescriptor[];
}

export interface RegionDescriptor {
  id: string;
  name: string;
  bbox: BBox;
  label_type: "bbox_area_near_city";
  geometry_source: string;
}

export interface RegionsResponse {
  regions: RegionDescriptor[];
}

export interface SourceDescriptor {
  collection_id: string;
  version: string;
  run_type: "Final";
  original_variable: string;
  original_unit: string;
  snapshot_id: string;
  snapshot_sha256: string;
  /** ISO 8601 timezone-aware timestamp. */
  retrieved_at: string;
  source_uri: string;
  aggregation_method: string;
}

export type SourceMode = "verified_snapshot";
export type SignificanceStatus =
  | "significant"
  | "not_significant"
  | "indeterminate";
export type Direction = "increasing" | "decreasing" | "no_clear_direction";

export interface YearRange {
  start_year: number;
  end_year: number;
}

export interface AnalysisParameters extends YearRange {
  variable_id: "precipitation";
  alpha: number;
  source_mode: SourceMode;
}

export interface AnalysisRequest extends AnalysisParameters {
  region_id: string;
}

export interface ComparisonRequest extends AnalysisParameters {
  left_region_id: string;
  right_region_id: string;
}

export interface MonthlyItem {
  period: Period;
  precipitation_total_mm: number | null;
  valid_fraction: number | null;
}

export interface AnnualItem {
  year: number;
  precipitation_total_mm: number | null;
  valid_months: number;
}

export interface Statistics {
  sample_years: number | null;
  ols_slope_mm_per_year: number | null;
  ols_r_squared: number | null;
  sen_slope_mm_per_year: number | null;
  sen_slope_ci95_mm_per_year: readonly [number | null, number | null];
  mann_kendall_p_value: number | null;
  mann_kendall_method: string;
  alpha: number;
  direction: Direction | null;
  significance_status: SignificanceStatus;
  assumptions_status: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  request: AnalysisRequest;
  region: RegionDescriptor;
  source: SourceDescriptor;
  monthly: MonthlyItem[];
  annual: AnnualItem[];
  statistics: Statistics;
  warnings: string[];
  algorithm_version: string;
}

export interface DatasetCompatibility {
  same_product: boolean;
  same_version: boolean;
  same_run: boolean;
}

export interface ComparisonResponse {
  shared_requested_period: YearRange;
  shared_analyzed_years: number[];
  dataset_compatibility: DatasetCompatibility;
  left: AnalysisResponse;
  right: AnalysisResponse;
  warnings: string[];
}
