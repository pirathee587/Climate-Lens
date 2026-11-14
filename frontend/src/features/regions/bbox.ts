import type { LatLngBoundsExpression } from "leaflet";

import type { BBox, RegionPreset } from "./regionTypes";

export type LeafletRegionBounds = LatLngBoundsExpression;

export function isValidBBox(bbox: BBox | null): bbox is BBox {
  if (bbox === null) {
    return false;
  }

  const [west, south, east, north] = bbox;
  return (
    [west, south, east, north].every(Number.isFinite) &&
    west >= -180 &&
    east <= 180 &&
    south >= -90 &&
    north <= 90 &&
    west < east &&
    south < north
  );
}

/** Converts [west, south, east, north] to [[south, west], [north, east]]. */
export function bboxToLeafletBounds(
  bbox: BBox | null,
): LeafletRegionBounds | null {
  if (!isValidBBox(bbox)) {
    return null;
  }

  const [west, south, east, north] = bbox;
  return [
    [south, west],
    [north, east],
  ];
}

export function getCombinedLeafletBounds(
  regions: readonly RegionPreset[],
): LeafletRegionBounds | null {
  const validBBoxes = regions
    .map((region) => region.bbox)
    .filter(isValidBBox);

  if (validBBoxes.length === 0) {
    return null;
  }

  const west = Math.min(...validBBoxes.map(([value]) => value));
  const south = Math.min(...validBBoxes.map(([, value]) => value));
  const east = Math.max(...validBBoxes.map(([, , value]) => value));
  const north = Math.max(...validBBoxes.map(([, , , value]) => value));

  return [
    [south, west],
    [north, east],
  ];
}
