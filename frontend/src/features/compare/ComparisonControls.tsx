import type { FormEvent } from "react";

import type {
  ComparisonRegion,
  ComparisonRegionId,
} from "./comparisonTypes";
import {
  getAvailableYears,
  type ComparisonSelection,
} from "./comparisonValidation";

export interface ComparisonControlsProps {
  regions: readonly ComparisonRegion[];
  availableYears: readonly number[];
  selection: ComparisonSelection;
  onSelectionChange: (selection: ComparisonSelection) => void;
  onSubmit: () => void;
  disabled?: boolean;
  validationMessage?: string | null;
}

export function ComparisonControls({
  regions,
  availableYears,
  selection,
  onSelectionChange,
  onSubmit,
  disabled = false,
  validationMessage = null,
}: ComparisonControlsProps) {
  const years = getAvailableYears(availableYears);
  const updateSelection = (patch: Partial<ComparisonSelection>) => {
    onSelectionChange({ ...selection, ...patch });
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  const regionOptions = regions
    .filter(
      (region) => region.id === "jaffna_area" || region.id === "colombo_area",
    )
    .filter(
      (region, index, supportedRegions) =>
        supportedRegions.findIndex((candidate) => candidate.id === region.id) ===
        index,
    );

  return (
    <form aria-describedby={validationMessage ? "comparison-error" : undefined} onSubmit={handleSubmit}>
      <fieldset disabled={disabled || years.length === 0}>
        <legend>Compare two verified regions</legend>
        <label>
          Left region
          <select
            aria-label="Left region"
            onChange={(event) =>
              updateSelection({
                leftRegionId: event.target.value as ComparisonRegionId | "",
              })
            }
            value={selection.leftRegionId}
          >
            <option value="">Select a region</option>
            {regionOptions.map((region) => (
              <option key={region.id} value={region.id}>
                {region.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Right region
          <select
            aria-label="Right region"
            onChange={(event) =>
              updateSelection({
                rightRegionId: event.target.value as ComparisonRegionId | "",
              })
            }
            value={selection.rightRegionId}
          >
            <option value="">Select a region</option>
            {regionOptions.map((region) => (
              <option key={region.id} value={region.id}>
                {region.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Start year
          <select
            aria-label="Start year"
            onChange={(event) =>
              updateSelection({
                startYear: event.target.value ? Number(event.target.value) : "",
              })
            }
            value={selection.startYear}
          >
            <option value="">Select a year</option>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>

        <label>
          End year
          <select
            aria-label="End year"
            onChange={(event) =>
              updateSelection({
                endYear: event.target.value ? Number(event.target.value) : "",
              })
            }
            value={selection.endYear}
          >
            <option value="">Select a year</option>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>

        <p>Two-sided alpha: 0.05</p>
        <p>Source mode: verified snapshot</p>
        <button type="submit">Compare regions</button>
      </fieldset>
      {validationMessage ? (
        <p id="comparison-error" role="alert">
          {validationMessage}
        </p>
      ) : null}
    </form>
  );
}
