import { useEffect } from "react";

import {
  MapContainer,
  Rectangle,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";

import {
  bboxToLeafletBounds,
  getCombinedLeafletBounds,
  isValidBBox,
} from "./bbox";
import { isRegionId } from "./regionTypes";
import type { RegionPreset } from "./regionTypes";

export interface RegionMapProps {
  regions: readonly RegionPreset[];
  selectedRegionId?: RegionPreset["id"];
  onRegionSelect?: (region: RegionPreset) => void;
  loading?: boolean;
  error?: string | null;
  className?: string;
}

interface MapViewportProps {
  bounds: ReturnType<typeof getCombinedLeafletBounds>;
}

function MapViewport({ bounds }: MapViewportProps) {
  const map = useMap();

  useEffect(() => {
    if (bounds !== null) {
      map.fitBounds(bounds);
    }
  }, [bounds, map]);

  return null;
}

function getSelectableRegions(
  regions: readonly RegionPreset[],
): readonly RegionPreset[] {
  return regions.filter(
    (region) => isRegionId(region.id) && isValidBBox(region.bbox),
  );
}

export function RegionMap({
  regions,
  selectedRegionId,
  onRegionSelect,
  loading = false,
  error = null,
  className,
}: RegionMapProps) {
  if (loading) {
    return <p role="status">Loading verified regions…</p>;
  }

  if (error) {
    return <p role="alert">Unable to load verified regions: {error}</p>;
  }

  const selectableRegions = getSelectableRegions(regions);
  const mapBounds = getCombinedLeafletBounds(selectableRegions);

  if (mapBounds === null) {
    return <p role="status">Verified region geometry is unavailable.</p>;
  }

  return (
    <div
      aria-label="Verified city-adjacent region map"
      className={className}
      role="application"
    >
      <MapContainer bounds={mapBounds} style={{ minHeight: "320px" }}>
        <MapViewport bounds={mapBounds} />
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {selectableRegions.map((region) => {
          const bounds = bboxToLeafletBounds(region.bbox);
          if (bounds === null) {
            return null;
          }

          const selected = region.id === selectedRegionId;
          return (
            <Rectangle
              bounds={bounds}
              eventHandlers={
                onRegionSelect
                  ? { click: () => onRegionSelect(region) }
                  : undefined
              }
              key={region.id}
              pathOptions={{
                color: selected ? "#1d4ed8" : "#64748b",
                fillOpacity: selected ? 0.25 : 0.12,
              }}
            >
              <Tooltip>{region.name} — area near city</Tooltip>
            </Rectangle>
          );
        })}
      </MapContainer>
    </div>
  );
}
