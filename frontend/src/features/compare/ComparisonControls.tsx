import type { FormEvent } from "react";

import type { ComparisonRegion, ComparisonRegionId } from "./comparisonTypes";
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
        supportedRegions.findIndex(
          (candidate) => candidate.id === region.id,
        ) === index,
    );

  return (
    <form
      aria-describedby={validationMessage ? "comparison-error" : undefined}
      className="rounded-lg border border-slate-200 bg-slate-50 p-4 shadow-sm sm:p-5"
      onSubmit={handleSubmit}
    >
      <fieldset className="space-y-4" disabled={disabled || years.length === 0}>
        <legend className="text-base font-semibold text-slate-900">
          Compare two verified regions
        </legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-medium text-slate-800">
            <span className="mb-1 block">Left region</span>
            <select
              aria-label="Left region"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 shadow-sm focus:border-sky-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 disabled:cursor-not-allowed disabled:bg-slate-100 sm:text-sm"
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

          <label className="block text-sm font-medium text-slate-800">
            <span className="mb-1 block">Right region</span>
            <select
              aria-label="Right region"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 shadow-sm focus:border-sky-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 disabled:cursor-not-allowed disabled:bg-slate-100 sm:text-sm"
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

          <label className="block text-sm font-medium text-slate-800">
            <span className="mb-1 block">Start year</span>
            <select
              aria-label="Start year"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 shadow-sm focus:border-sky-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 disabled:cursor-not-allowed disabled:bg-slate-100 sm:text-sm"
              onChange={(event) =>
                updateSelection({
                  startYear: event.target.value
                    ? Number(event.target.value)
                    : "",
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

          <label className="block text-sm font-medium text-slate-800">
            <span className="mb-1 block">End year</span>
            <select
              aria-label="End year"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 shadow-sm focus:border-sky-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 disabled:cursor-not-allowed disabled:bg-slate-100 sm:text-sm"
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
        </div>

        <div className="text-sm text-slate-600">
          <p>Two-sided alpha: 0.05</p>
          <p>Source mode: verified snapshot</p>
        </div>
        <button
          className="w-full rounded-md bg-sky-700 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-sky-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 disabled:cursor-not-allowed disabled:bg-slate-400 sm:w-auto"
          type="submit"
        >
          Compare regions
        </button>
      </fieldset>
      {validationMessage ? (
        <p
          className="mt-3 text-sm font-medium text-red-700"
          id="comparison-error"
          role="alert"
        >
          {validationMessage}
        </p>
      ) : null}
    </form>
  );
}
