import {
  selectableYears,
  validateYearSelection,
} from "../../src/features/investigate/yearRange";

describe("selectableYears", () => {
  it("returns every full calendar year inside the coverage", () => {
    expect(selectableYears("2001-01", "2024-12")).toHaveLength(24);
    expect(selectableYears("2001-01", "2024-12")[0]).toBe(2001);
  });

  it("drops partial first and last years", () => {
    expect(selectableYears("2000-06", "2025-09")).toEqual(
      Array.from({ length: 24 }, (_, i) => 2001 + i),
    );
  });

  it("returns nothing for malformed or too-short coverage", () => {
    expect(selectableYears("bad", "2024-12")).toEqual([]);
    expect(selectableYears("2024-03", "2024-11")).toEqual([]);
  });
});

describe("validateYearSelection", () => {
  const years = Array.from({ length: 24 }, (_, i) => 2001 + i);

  it("accepts a valid span of at least 10 years", () => {
    expect(validateYearSelection(2001, 2010, years)).toBeNull();
  });

  it("rejects reversed, out-of-range and short spans", () => {
    expect(validateYearSelection(2010, 2001, years)).toMatch(/start year/);
    expect(validateYearSelection(1990, 2010, years)).toMatch(/coverage/);
    expect(validateYearSelection(2001, 2009, years)).toMatch(/at least 10/);
  });

  it("explains when no years are available", () => {
    expect(validateYearSelection(2001, 2010, [])).toMatch(/No verified/);
  });
});
