import type { Period } from "../../types/api";

const PERIOD_PATTERN = /^(\d{4})-(0[1-9]|1[0-2])$/;

function parsePeriod(period: Period): { year: number; month: number } | null {
  const match = PERIOD_PATTERN.exec(period);
  if (!match) return null;
  return { year: Number(match[1]), month: Number(match[2]) };
}

/**
 * Calendar years the user may select, derived ONLY from the verified
 * coverage the catalog returns (FR-003). A partial first or last year is
 * not offered, because annual totals require a full January–December
 * window. This is UI range-limiting, not data validation: the backend
 * still decides which years have 12 valid months.
 */
export function selectableYears(
  firstAvailable: Period,
  lastAvailable: Period,
): number[] {
  const first = parsePeriod(firstAvailable);
  const last = parsePeriod(lastAvailable);
  if (!first || !last) return [];

  const startYear = first.month === 1 ? first.year : first.year + 1;
  const endYear = last.month === 12 ? last.year : last.year - 1;
  if (startYear > endYear) return [];

  return Array.from(
    { length: endYear - startYear + 1 },
    (_, index) => startYear + index,
  );
}

/** Pragmatic P0 minimum from docs/SCOPE.md; the backend enforces it too. */
export const MINIMUM_COMPLETE_YEARS = 10;

export function validateYearSelection(
  startYear: number,
  endYear: number,
  years: readonly number[],
): string | null {
  if (years.length === 0) {
    return "No verified complete calendar years are available.";
  }
  if (!years.includes(startYear) || !years.includes(endYear)) {
    return "Choose years inside the verified data coverage.";
  }
  if (startYear > endYear) {
    return "The start year must not be after the end year.";
  }
  if (endYear - startYear + 1 < MINIMUM_COMPLETE_YEARS) {
    return `Choose a span of at least ${MINIMUM_COMPLETE_YEARS} calendar years.`;
  }
  return null;
}
