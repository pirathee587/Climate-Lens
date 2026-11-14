import { describe, expect, it } from "vitest";

import {
  getCommonCompleteYears,
  validateComparisonSelection,
} from "./comparisonValidation";
import type { ComparisonResponse } from "./comparisonTypes";

describe("comparison validation", () => {
  it("rejects identical regions and out-of-coverage years", () => {
    expect(
      validateComparisonSelection(
        {
          leftRegionId: "jaffna_area",
          rightRegionId: "jaffna_area",
          startYear: 2001,
          endYear: 2024,
        },
        [2001, 2024],
      ),
    ).toBe("Select two distinct regions.");

    expect(
      validateComparisonSelection(
        {
          leftRegionId: "jaffna_area",
          rightRegionId: "colombo_area",
          startYear: 1999,
          endYear: 2024,
        },
        [2001, 2024],
      ),
    ).toBe("Select years within the verified available coverage.");

    expect(
      validateComparisonSelection(
        {
          leftRegionId: "jaffna_area",
          rightRegionId: "colombo_area",
          startYear: 2024,
          endYear: 2001,
        },
        [2001, 2024],
      ),
    ).toBe("Start year must be before or equal to end year.");
  });

  it("derives only common complete years from returned annual records", () => {
    const response = {
      left: {
        annual: [
          { year: 2001, precipitation_total_mm: 100, valid_months: 12 },
          { year: 2002, precipitation_total_mm: 100, valid_months: 11 },
          { year: 2004, precipitation_total_mm: Number.NaN, valid_months: 12 },
        ],
      },
      right: {
        annual: [
          { year: 2001, precipitation_total_mm: 120, valid_months: 12 },
          { year: 2001, precipitation_total_mm: 120, valid_months: 12 },
          { year: 2003, precipitation_total_mm: 120, valid_months: 12 },
        ],
      },
      shared_requested_period: { start_year: 2001, end_year: 2003 },
    } as unknown as ComparisonResponse;

    expect(getCommonCompleteYears(response)).toEqual([2001]);
  });

  it("returns no common years for empty or invalid annual records", () => {
    const response = {
      shared_requested_period: { start_year: 2001, end_year: 2024 },
      left: {
        annual: [
          null,
          { year: Number.NaN, precipitation_total_mm: 1, valid_months: 12 },
        ],
      },
      right: { annual: [] },
    } as unknown as ComparisonResponse;

    expect(getCommonCompleteYears(response)).toEqual([]);
  });

  it("uses backend shared years when present and rejects inconsistent values", () => {
    const response = {
      shared_requested_period: { start_year: 2001, end_year: 2002 },
      shared_analyzed_years: [2001, 2002],
      left: {
        annual: [
          { year: 2001, precipitation_total_mm: 100, valid_months: 12 },
          { year: 2002, precipitation_total_mm: 110, valid_months: 12 },
        ],
      },
      right: {
        annual: [
          { year: 2001, precipitation_total_mm: 120, valid_months: 12 },
          { year: 2002, precipitation_total_mm: 130, valid_months: 12 },
        ],
      },
    } as unknown as ComparisonResponse;

    expect(getCommonCompleteYears(response)).toEqual([2001, 2002]);
    expect(
      getCommonCompleteYears({
        ...response,
        shared_analyzed_years: [2002, 2001],
      }),
    ).toEqual([]);
  });
});
