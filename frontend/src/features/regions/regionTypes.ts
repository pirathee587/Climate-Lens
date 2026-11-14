export const REGION_IDS = ["jaffna_area", "colombo_area"] as const;

export type RegionId = (typeof REGION_IDS)[number];

export type BBox = readonly [
  west: number,
  south: number,
  east: number,
  north: number,
];

/** Mirrors the RegionPreset object in docs/API_SPEC.md. */
export interface RegionPreset {
  id: RegionId;
  name: string;
  label_type: string;
  bbox: BBox | null;
  geometry_source: string;
}

/** Mirrors GET /api/v1/regions/presets. */
export interface RegionPresetsResponse {
  regions: readonly RegionPreset[];
}

export function isRegionId(value: string): value is RegionId {
  return REGION_IDS.includes(value as RegionId);
}
