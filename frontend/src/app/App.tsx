import { useMemo, useState } from "react";
import type { KeyboardEvent } from "react";

import {
  EmptyState,
  ErrorNotice,
  LoadingState,
} from "../components/common/StatusMessage";
import { AppShell } from "../components/layout/AppShell";
import { ComparisonPanel } from "../features/compare";
import { InvestigatePage, selectableYears } from "../features/investigate";
import { useCatalog } from "../hooks/useCatalog";
import type { RegionDescriptor, VariableDescriptor } from "../types/api";
import { requestComparison, toComparisonRegions } from "./adapters";

type Tab = "investigate" | "compare";

const TABS: { id: Tab; label: string }[] = [
  { id: "investigate", label: "Investigate" },
  { id: "compare", label: "Compare regions" },
];

function ComparePage({
  variable,
  regions,
}: {
  variable: VariableDescriptor;
  regions: readonly RegionDescriptor[];
}) {
  const comparisonRegions = useMemo(
    () => toComparisonRegions(regions),
    [regions],
  );
  const years = useMemo(
    () =>
      selectableYears(
        variable.first_available_period,
        variable.last_available_period,
      ),
    [variable.first_available_period, variable.last_available_period],
  );
  return (
    <ComparisonPanel
      regions={comparisonRegions}
      availableYears={years}
      requestComparison={requestComparison}
    />
  );
}

export function App() {
  const catalog = useCatalog();
  const [tab, setTab] = useState<Tab>("investigate");

  // WAI-ARIA tabs pattern: arrows move between tabs, Home/End jump.
  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const index = TABS.findIndex((item) => item.id === tab);
    const nextIndex = {
      ArrowRight: (index + 1) % TABS.length,
      ArrowLeft: (index - 1 + TABS.length) % TABS.length,
      Home: 0,
      End: TABS.length - 1,
    }[event.key];
    const next = nextIndex === undefined ? undefined : TABS[nextIndex];
    if (!next) return;
    event.preventDefault();
    setTab(next.id);
    document.getElementById(`tab-${next.id}`)?.focus();
  };

  let content;
  if (catalog.status === "loading") {
    content = <LoadingState label="Loading the verified data catalog…" />;
  } else if (catalog.status === "error") {
    content = <ErrorNotice error={catalog.error} onRetry={catalog.reload} />;
  } else {
    const variable = catalog.variables[0];
    if (!variable || catalog.regions.length === 0) {
      content = (
        <EmptyState title="No verified data is installed">
          The server has no supported variable or verified region yet, so no
          analysis can be run.
        </EmptyState>
      );
    } else {
      content = (
        <>
          <div
            role="tablist"
            aria-label="Views"
            className="mb-4 flex gap-2 border-b border-slate-200"
          >
            {TABS.map((item) => (
              <button
                key={item.id}
                id={`tab-${item.id}`}
                role="tab"
                type="button"
                aria-selected={tab === item.id}
                aria-controls={`panel-${item.id}`}
                tabIndex={tab === item.id ? 0 : -1}
                onClick={() => setTab(item.id)}
                onKeyDown={handleTabKeyDown}
                className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 ${
                  tab === item.id
                    ? "border-sky-700 text-sky-900"
                    : "border-transparent text-slate-600 hover:text-slate-900"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
          {/* Both panels stay mounted so results survive tab switches. */}
          <div
            role="tabpanel"
            id="panel-investigate"
            aria-labelledby="tab-investigate"
            hidden={tab !== "investigate"}
          >
            <InvestigatePage variable={variable} regions={catalog.regions} />
          </div>
          <div
            role="tabpanel"
            id="panel-compare"
            aria-labelledby="tab-compare"
            hidden={tab !== "compare"}
          >
            <ComparePage variable={variable} regions={catalog.regions} />
          </div>
        </>
      );
    }
  }

  return <AppShell>{content}</AppShell>;
}
