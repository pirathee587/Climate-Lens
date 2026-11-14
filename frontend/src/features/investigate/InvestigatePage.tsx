import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";

import { postAnalysis } from "../../api/client";
import { toRegionPresets } from "../../app/adapters";
import {
  EmptyState,
  ErrorNotice,
  LoadingState,
} from "../../components/common/StatusMessage";
import { RegionMap, RegionSelector } from "../regions";
import type { RegionId, RegionPreset } from "../regions";
import type {
  AnalysisResponse,
  RegionDescriptor,
  VariableDescriptor,
} from "../../types/api";
import { AnalysisResults } from "./AnalysisResults";
import { ALPHA_OPTIONS, DEFAULT_ALPHA } from "./constants";
import { VariableCard } from "./VariableCard";
import { selectableYears, validateYearSelection } from "./yearRange";

export interface InvestigatePageProps {
  variable: VariableDescriptor;
  regions: readonly RegionDescriptor[];
  analyze?: typeof postAnalysis;
}

type AnalysisState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; error: unknown }
  | { status: "success"; analysis: AnalysisResponse };

const fieldClass =
  "mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-sky-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600";

export function InvestigatePage({
  variable,
  regions,
  analyze = postAnalysis,
}: InvestigatePageProps) {
  const presets = useMemo(() => toRegionPresets(regions), [regions]);
  const years = useMemo(
    () =>
      selectableYears(
        variable.first_available_period,
        variable.last_available_period,
      ),
    [variable.first_available_period, variable.last_available_period],
  );

  const [regionId, setRegionId] = useState<RegionId | undefined>(
    presets[0]?.id,
  );
  const [startYear, setStartYear] = useState<number>(years[0] ?? 0);
  const [endYear, setEndYear] = useState<number>(years[years.length - 1] ?? 0);
  const [alpha, setAlpha] = useState<number>(DEFAULT_ALPHA);
  const [validation, setValidation] = useState<string | null>(null);
  const [state, setState] = useState<AnalysisState>({ status: "idle" });
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => () => controllerRef.current?.abort(), []);

  const runAnalysis = async () => {
    const message = !regionId
      ? "Choose a verified region."
      : validateYearSelection(startYear, endYear, years);
    setValidation(message);
    if (message || !regionId) return;

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState({ status: "loading" });

    try {
      const analysis = await analyze(
        {
          variable_id: variable.id,
          region_id: regionId,
          start_year: startYear,
          end_year: endYear,
          alpha,
          source_mode: "verified_snapshot",
        },
        { signal: controller.signal },
      );
      if (!controller.signal.aborted) setState({ status: "success", analysis });
    } catch (error) {
      if (!controller.signal.aborted) setState({ status: "error", error });
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void runAnalysis();
  };

  const handleRegionSelect = (region: RegionPreset) => setRegionId(region.id);
  const busy = state.status === "loading";

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <div className="space-y-4">
          <VariableCard variable={variable} />
          <form
            onSubmit={handleSubmit}
            aria-labelledby="investigate-form-heading"
            className="space-y-4 rounded-lg border border-slate-200 bg-white p-4"
            noValidate
          >
            <h2 id="investigate-form-heading" className="text-lg font-semibold">
              Investigate one region
            </h2>

            <RegionSelector
              regions={presets}
              selectedRegionId={regionId}
              onSelect={handleRegionSelect}
              disabled={busy}
            />

            <fieldset className="grid grid-cols-2 gap-3" disabled={busy}>
              <legend className="col-span-2 text-sm font-medium">
                Complete calendar years
              </legend>
              <label className="text-sm">
                Start year
                <select
                  className={fieldClass}
                  value={startYear}
                  onChange={(e) => setStartYear(Number(e.target.value))}
                >
                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm">
                End year
                <select
                  className={fieldClass}
                  value={endYear}
                  onChange={(e) => setEndYear(Number(e.target.value))}
                >
                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </label>
            </fieldset>

            <label className="block text-sm">
              Significance level (α, two-sided)
              <select
                className={fieldClass}
                value={alpha}
                disabled={busy}
                onChange={(e) => setAlpha(Number(e.target.value))}
              >
                {ALPHA_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                    {option === DEFAULT_ALPHA ? " (default)" : ""}
                  </option>
                ))}
              </select>
            </label>

            {validation ? (
              <p role="alert" className="text-sm text-red-800">
                {validation}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={busy || years.length === 0 || presets.length === 0}
              className="w-full rounded-md bg-sky-700 px-4 py-2 font-medium text-white hover:bg-sky-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {busy ? "Analyzing…" : "Analyze"}
            </button>
          </form>
        </div>

        <div className="min-h-[20rem] overflow-hidden rounded-lg border border-slate-200 bg-white">
          <RegionMap
            regions={presets}
            selectedRegionId={regionId}
            onRegionSelect={handleRegionSelect}
            className="h-full min-h-[20rem]"
          />
        </div>
      </div>

      {state.status === "idle" ? (
        <EmptyState title="No analysis yet">
          Choose a region and years, then select Analyze. Results come only from
          the verified NASA snapshot on the server.
        </EmptyState>
      ) : null}
      {state.status === "loading" ? (
        <LoadingState label="Running analysis on the verified snapshot…" />
      ) : null}
      {state.status === "error" ? (
        <ErrorNotice error={state.error} onRetry={() => void runAnalysis()} />
      ) : null}
      {state.status === "success" ? (
        <AnalysisResults analysis={state.analysis} />
      ) : null}
    </div>
  );
}
