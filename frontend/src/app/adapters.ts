/**
 * Glue between the shared API types (src/types/api.ts) and the feature
 * component types owned by Kavishanth (features/regions, features/compare).
 * Those features narrow region IDs to the two verified presets, so anything
 * the backend returns outside that list is dropped here, not cast.
 */
import { ApiError, postComparison } from "../api/client";
import type {
  ComparisonRegion,
  ComparisonResponse as PanelComparisonResponse,
} from "../features/compare";
import type { ComparisonRequest as PanelComparisonRequest } from "../features/compare";
import { isRegionId } from "../features/regions";
import type { RegionPreset } from "../features/regions";
import type {
  AnalysisResponse,
  ComparisonResponse,
  RegionDescriptor,
} from "../types/api";

export function toRegionPresets(
  regions: readonly RegionDescriptor[],
): RegionPreset[] {
  return regions.flatMap((region) =>
    isRegionId(region.id)
      ? [
          {
            id: region.id,
            name: region.name,
            label_type: region.label_type,
            bbox: region.bbox,
            geometry_source: region.geometry_source,
          },
        ]
      : [],
  );
}

export function toComparisonRegions(
  regions: readonly RegionDescriptor[],
): ComparisonRegion[] {
  return toRegionPresets(regions).map((region) => ({
    id: region.id,
    name: region.name,
  }));
}

function toPanelAnalysis(
  analysis: AnalysisResponse,
): PanelComparisonResponse["left"] {
  const { region } = analysis;
  if (!isRegionId(region.id)) {
    throw new ApiError(409, {
      code: "INCOMPATIBLE_DATA",
      message: "The comparison returned an unsupported region.",
      details: {},
      request_id: "",
    });
  }
  return {
    analysis_id: analysis.analysis_id,
    region: {
      id: region.id,
      name: region.name,
      bbox: region.bbox,
      label_type: region.label_type,
    },
    monthly: analysis.monthly,
    annual: analysis.annual,
    statistics: analysis.statistics,
    source: analysis.source,
  };
}

export function toPanelComparison(
  response: ComparisonResponse,
): PanelComparisonResponse {
  return {
    shared_requested_period: response.shared_requested_period,
    dataset_compatibility: response.dataset_compatibility,
    left: toPanelAnalysis(response.left),
    right: toPanelAnalysis(response.right),
    warnings: response.warnings,
  };
}

/** `requestComparison` implementation handed to Kavishanth's ComparisonPanel. */
export async function requestComparison(
  request: PanelComparisonRequest,
): Promise<PanelComparisonResponse> {
  return toPanelComparison(await postComparison(request));
}
