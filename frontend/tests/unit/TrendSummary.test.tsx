import { render, screen } from "@testing-library/react";

import { TrendSummary } from "../../src/features/charts";
import type { Statistics } from "../../src/types/api";
import { syntheticAnalysis } from "../fixtures/synthetic";

const base = syntheticAnalysis.statistics;

function renderWith(statistics: Statistics) {
  render(
    <TrendSummary
      statistics={statistics}
      regionName="Test region A"
      analyzedYears={[2001, 2002]}
      sourceLabel="TEST"
    />,
  );
}

describe("TrendSummary", () => {
  it("labels significance in text, not only colour", () => {
    renderWith({ ...base, significance_status: "significant" });
    expect(screen.getByTestId("significance-status")).toHaveTextContent(
      "Statistically significant",
    );
  });

  it("shows indeterminate and dashes for undefined statistics", () => {
    renderWith({
      ...base,
      significance_status: "indeterminate",
      sen_slope_mm_per_year: null,
      sen_slope_ci95_mm_per_year: [null, null],
      mann_kendall_p_value: null,
    });
    expect(screen.getByTestId("significance-status")).toHaveTextContent(
      "Indeterminate",
    );
    expect(screen.getByText("Sen slope").parentElement).toHaveTextContent("—");
  });

  it("always states that the result is not causal", () => {
    renderWith(base);
    expect(screen.getByTestId("interpretation")).toHaveTextContent(
      /not the cause/,
    );
  });

  it("keeps direction separate from significance", () => {
    renderWith({
      ...base,
      direction: "increasing",
      significance_status: "not_significant",
    });
    expect(screen.getByText("Increasing (estimated)")).toBeInTheDocument();
    expect(screen.getByTestId("significance-status")).toHaveTextContent(
      "Not statistically significant",
    );
  });
});
