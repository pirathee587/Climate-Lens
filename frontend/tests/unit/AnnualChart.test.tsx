import { render, screen } from "@testing-library/react";

import { AnnualChart, SeriesTable } from "../../src/features/charts";
import { hasFittedTrend } from "../../src/features/charts/series";
import type { AnnualItem } from "../../src/types/api";

// SYNTHETIC TEST VALUES — NOT NASA DATA. Shape-only checks.
const withoutFitted: AnnualItem[] = [
  { year: 2001, precipitation_total_mm: 100, valid_months: 12 },
  { year: 2002, precipitation_total_mm: 100, valid_months: 12 },
];

const withFitted: AnnualItem[] = [
  {
    year: 2001,
    precipitation_total_mm: 100,
    valid_months: 12,
    ols_fitted_mm: 90,
  },
  {
    year: 2002,
    precipitation_total_mm: null,
    valid_months: 11,
    ols_fitted_mm: null,
  },
];

describe("OLS fitted trend line", () => {
  it("is hidden until the API supplies ols_fitted_mm", () => {
    expect(hasFittedTrend(withoutFitted)).toBe(false);
    expect(
      hasFittedTrend(withoutFitted.map((r) => ({ ...r, ols_fitted_mm: null }))),
    ).toBe(false);
    render(<AnnualChart annual={withoutFitted} regionName="Test region" />);
    expect(screen.queryByTestId("trend-line-note")).not.toBeInTheDocument();
  });

  it("is shown and labelled as not a forecast when fitted values exist", () => {
    expect(hasFittedTrend(withFitted)).toBe(true);
    render(<AnnualChart annual={withFitted} regionName="Test region" />);
    expect(screen.getByTestId("trend-line-note")).toHaveTextContent(
      /OLS fitted trend.*not a forecast/,
    );
  });

  it("adds the fitted column to the accessible table only when present", () => {
    const { unmount } = render(
      <SeriesTable monthly={[]} annual={withoutFitted} />,
    );
    expect(
      screen.queryByRole("columnheader", { name: "OLS fitted trend (mm)" }),
    ).not.toBeInTheDocument();
    unmount();

    render(<SeriesTable monthly={[]} annual={withFitted} />);
    expect(
      screen.getByRole("columnheader", {
        name: "OLS fitted trend (mm)",
        hidden: true,
      }),
    ).toBeInTheDocument();
  });
});
