import type {
  ComparisonAnnualRecord,
  ComparisonRegion,
  ComparisonResponse,
} from "./comparisonTypes";

export const MINIMUM_COMPLETE_YEARS = 10;

export interface ComparisonSelection {
  leftRegionId: ComparisonRegion["id"] | "";
  rightRegionId: ComparisonRegion["id"] | "";
  startYear: number | "";
  endYear: number | "";
}

export function validateComparisonSelection(
  selection: ComparisonSelection,
  availableYears: readonly number[],
): string | null {
  if (!selection.leftRegionId || !selection.rightRegionId) {
    return "Select both regions.";
  }

  if (selection.leftRegionId === selection.rightRegionId) {
    return "Select two distinct regions.";
  }

  if (selection.startYear === "" || selection.endYear === "") {
    return "Select a start year and end year.";
  }

  if (
    !availableYears.includes(selection.startYear) ||
    !availableYears.includes(selection.endYear)
  ) {
    return "Select years within the verified available coverage.";
  }

  if (selection.startYear > selection.endYear) {
    return "Start year must be before or equal to end year.";
  }

  return null;
}

function isCompleteAnnualRecord(
  record: ComparisonAnnualRecord | null | undefined,
): record is ComparisonAnnualRecord & { precipitation_total_mm: number } {
  return (
    record !== null &&
    record !== undefined &&
    Number.isInteger(record.year) &&
    record.valid_months === 12 &&
    record.precipitation_total_mm !== null &&
    Number.isFinite(record.precipitation_total_mm)
  );
}

/** Derives display-only common complete years from returned annual records. */
export function getCommonCompleteYears(
  response: ComparisonResponse,
): readonly number[] {
  const { start_year: startYear, end_year: endYear } =
    response.shared_requested_period;
  const leftYears = new Set(
    (response.left?.annual ?? [])
      .filter(isCompleteAnnualRecord)
      .map(({ year }) => year)
      .filter((year) => year >= startYear && year <= endYear),
  );

  return [
    ...new Set(
      (response.right?.annual ?? [])
        .filter(isCompleteAnnualRecord)
        .map(({ year }) => year)
        .filter((year) => leftYears.has(year)),
    ),
  ].sort((left, right) => left - right);
}

export function getAvailableYears(
  availableYears: readonly number[],
): readonly number[] {
  return [...new Set(availableYears)]
    .filter((year) => Number.isInteger(year))
    .sort((left, right) => left - right);
}

export function hasIncompatibleDataset(
  compatibility: ComparisonResponse["dataset_compatibility"],
): boolean {
  return !(
    compatibility.same_product &&
    compatibility.same_version &&
    compatibility.same_run
  );
}
