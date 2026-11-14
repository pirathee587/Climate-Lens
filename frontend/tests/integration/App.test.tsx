import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "../../src/app/App";
import {
  errorBody,
  jsonResponse,
  syntheticAnalysis,
  syntheticRegions,
  syntheticVariables,
} from "../fixtures/synthetic";

// Leaflet's SVG renderer cannot run in jsdom, so the map (owned by
// features/regions and covered by its own tests) is replaced with a stub
// here. Everything else in the regions feature — including the real
// RegionSelector — is used unchanged.
vi.mock("../../src/features/regions/RegionMap", () => ({
  RegionMap: () => <div data-testid="region-map-stub" />,
}));

type Route = (url: string, init?: RequestInit) => Response;

function stubFetch(route: Route) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
    Promise.resolve(route(String(input), init)),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const readyCatalog: Route = (url) => {
  if (url.endsWith("/variables")) return jsonResponse(syntheticVariables);
  if (url.endsWith("/regions/presets")) return jsonResponse(syntheticRegions);
  return jsonResponse(errorBody("NOT_FOUND", "Resource not found."), 404);
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("shows the dataset-unavailable state when the catalog returns 503", async () => {
    stubFetch(() =>
      jsonResponse(
        errorBody("DATASET_UNAVAILABLE", "Verified dataset is not available."),
        503,
      ),
    );
    render(<App />);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Verified NASA data is not available yet");
    expect(alert).toHaveTextContent("DATASET_UNAVAILABLE");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByText(/Trend findings/)).not.toBeInTheDocument();
  });

  it("always shows the prototype disclaimer and NASA attribution", async () => {
    stubFetch(readyCatalog);
    render(<App />);
    expect(
      screen.getByText(/not an official NASA product/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/GPM IMERG Final monthly product/),
    ).toBeInTheDocument();
    await screen.findByRole("heading", { name: "Precipitation" });
  });

  it("runs an analysis and renders results returned by the API", async () => {
    const fetchMock = stubFetch((url, init) =>
      url.endsWith("/analyses") && init?.method === "POST"
        ? jsonResponse(syntheticAnalysis)
        : readyCatalog(url, init),
    );
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Analyze" }));

    const results = await screen.findByRole("region", { name: /Results:/ });
    expect(
      within(results).getByTestId("significance-status"),
    ).toHaveTextContent("Not statistically significant");
    expect(
      within(results).getByText(/Excluded incomplete year/),
    ).toHaveTextContent("2005 (11/12 months)");
    expect(within(results).getByTestId("analysis-warnings")).toHaveTextContent(
      "2005 excluded",
    );
    expect(
      within(results).getByRole("button", { name: "Download CSV" }),
    ).toBeEnabled();

    const post = fetchMock.mock.calls.find(
      ([, init]) => init?.method === "POST",
    );
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({
      variable_id: "precipitation",
      region_id: "jaffna_area",
      start_year: 2001,
      end_year: 2012,
      alpha: 0.05,
      source_mode: "verified_snapshot",
    });
  });

  it("shows a structured error and no results when analysis fails", async () => {
    stubFetch((url, init) =>
      url.endsWith("/analyses") && init?.method === "POST"
        ? jsonResponse(
            errorBody(
              "INSUFFICIENT_DATA",
              "At least 10 complete calendar years are needed.",
            ),
            422,
          )
        : readyCatalog(url, init),
    );
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Analyze" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Not enough complete years");
    expect(
      screen.queryByRole("region", { name: /Results:/ }),
    ).not.toBeInTheDocument();
  });

  it("blocks spans shorter than 10 years before calling the API", async () => {
    const fetchMock = stubFetch(readyCatalog);
    const user = userEvent.setup();
    render(<App />);
    // Scope to the Investigate panel: the (hidden) Compare panel also has a
    // "Start year" field now that both panels stay mounted.
    const investigatePanel = await screen.findByRole("tabpanel", {
      name: "Investigate",
    });
    await user.selectOptions(
      within(investigatePanel).getByLabelText("Start year"),
      "2005",
    );
    await user.click(screen.getByRole("button", { name: "Analyze" }));
    expect(
      await screen.findByText(/at least 10 calendar years/),
    ).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([, init]) => init?.method === "POST"),
    ).toBe(false);
  });

  it("switches to the comparison view", async () => {
    stubFetch(readyCatalog);
    const user = userEvent.setup();
    render(<App />);
    await user.click(
      await screen.findByRole("tab", { name: "Compare regions" }),
    );
    expect(
      screen.getByRole("tab", { name: "Compare regions" }),
    ).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByRole("heading", { name: "Regional comparison" }),
    ).toBeVisible();
  });

  it("keeps analysis results when switching tabs and back", async () => {
    stubFetch((url, init) =>
      url.endsWith("/analyses") && init?.method === "POST"
        ? jsonResponse(syntheticAnalysis)
        : readyCatalog(url, init),
    );
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Analyze" }));
    await screen.findByRole("region", { name: /Results:/ });

    await user.click(screen.getByRole("tab", { name: "Compare regions" }));
    await user.click(screen.getByRole("tab", { name: "Investigate" }));

    expect(
      screen.getByRole("region", { name: /Results:/ }),
    ).toBeInTheDocument();
  });

  it("supports arrow-key navigation between tabs", async () => {
    stubFetch(readyCatalog);
    const user = userEvent.setup();
    render(<App />);
    const investigate = await screen.findByRole("tab", {
      name: "Investigate",
    });
    investigate.focus();
    await user.keyboard("{ArrowRight}");
    const compare = screen.getByRole("tab", { name: "Compare regions" });
    expect(compare).toHaveFocus();
    expect(compare).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{Home}");
    expect(investigate).toHaveAttribute("aria-selected", "true");
  });

  it("shows a CSV export failure in-app instead of leaving the page", async () => {
    stubFetch((url, init) => {
      if (url.endsWith("/analyses") && init?.method === "POST") {
        return jsonResponse(syntheticAnalysis);
      }
      if (url.endsWith("/export.csv")) {
        return jsonResponse(errorBody("NOT_FOUND", "Resource not found."), 404);
      }
      return readyCatalog(url, init);
    });
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Analyze" }));
    await user.click(
      await screen.findByRole("button", { name: "Download CSV" }),
    );

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Not available on this server");
    expect(
      screen.getByRole("region", { name: /Results:/ }),
    ).toBeInTheDocument();
  });
});
