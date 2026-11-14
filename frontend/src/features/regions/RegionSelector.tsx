import type { ChangeEvent } from "react";

import { isValidBBox } from "./bbox";
import { isRegionId } from "./regionTypes";
import type { RegionPreset } from "./regionTypes";

export interface RegionSelectorProps {
  regions: readonly RegionPreset[];
  selectedRegionId?: RegionPreset["id"];
  onSelect: (region: RegionPreset) => void;
  loading?: boolean;
  error?: string | null;
  disabled?: boolean;
  label?: string;
}

function getSelectableRegions(
  regions: readonly RegionPreset[],
): readonly RegionPreset[] {
  return regions.filter(
    (region) => isRegionId(region.id) && isValidBBox(region.bbox),
  );
}

export function RegionSelector({
  regions,
  selectedRegionId,
  onSelect,
  loading = false,
  error = null,
  disabled = false,
  label = "Verified region",
}: RegionSelectorProps) {
  if (loading) {
    return <p role="status">Loading verified regions…</p>;
  }

  if (error) {
    return <p role="alert">Unable to load verified regions: {error}</p>;
  }

  const selectableRegions = getSelectableRegions(regions);
  if (selectableRegions.length === 0) {
    return <p role="status">Verified region data are unavailable.</p>;
  }

  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const selectedRegion = selectableRegions.find(
      (region) => region.id === event.target.value,
    );

    if (selectedRegion) {
      onSelect(selectedRegion);
    }
  };

  return (
    <label>
      {label}
      <select
        aria-label={label}
        disabled={disabled}
        onChange={handleChange}
        value={selectedRegionId ?? ""}
      >
        <option disabled value="">
          Select a verified area
        </option>
        {selectableRegions.map((region) => (
          <option key={region.id} value={region.id}>
            {region.name}
          </option>
        ))}
      </select>
    </label>
  );
}
