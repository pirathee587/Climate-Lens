import type { AnnualItem } from "../../types/api";

/** A year counts as complete only with 12 valid months and a total (FR-008). */
export function isCompleteYear(item: AnnualItem): boolean {
  return item.valid_months === 12 && item.precipitation_total_mm !== null;
}

/**
 * True when the backend supplied at least one OLS fitted value. Until then
 * the trend line stays hidden (PR #6 review decision).
 */
export function hasFittedTrend(annual: readonly AnnualItem[]): boolean {
  return annual.some(
    (item) =>
      typeof item.ols_fitted_mm === "number" &&
      Number.isFinite(item.ols_fitted_mm),
  );
}
