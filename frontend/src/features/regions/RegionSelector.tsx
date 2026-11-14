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
    <label className="block text-sm font-medium text-slate-800">
      <span className="mb-1 block">{label}</span>
      <select
        aria-label={label}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 shadow-sm focus:border-sky-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 disabled:cursor-not-allowed disabled:bg-slate-100 sm:text-sm"
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
