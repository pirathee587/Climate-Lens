import type { AnnualItem } from "../../types/api";

/** A year counts as complete only with 12 valid months and a total (FR-008). */
export function isCompleteYear(item: AnnualItem): boolean {
  return item.valid_months === 12 && item.precipitation_total_mm !== null;
}
