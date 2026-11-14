import {
  AnnualChart,
  ExportControls,
  isCompleteYear,
  MonthlyChart,
  SeriesTable,
  TrendSummary,
  WarningsList,
} from "../charts";
import type { AnalysisResponse } from "../../types/api";
import { ProvenancePanel } from "./ProvenancePanel";

/** Ready state of the investigate screen (FR-009, FR-013, FR-015, FR-018). */
export function AnalysisResults({ analysis }: { analysis: AnalysisResponse }) {
  const analyzedYears = analysis.annual
    .filter(isCompleteYear)
    .map((item) => item.year);
  const sourceLabel = `${analysis.source.collection_id} ${analysis.source.version} ${analysis.source.run_type}`;

  return (
    <section aria-labelledby="results-heading" className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="results-heading" className="text-xl font-semibold">
          Results: {analysis.region.name}
        </h2>
        <ExportControls analysisId={analysis.analysis_id} />
      </div>
      <TrendSummary
        statistics={analysis.statistics}
        regionName={analysis.region.name}
        analyzedYears={analyzedYears}
        sourceLabel={sourceLabel}
      />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <MonthlyChart
          monthly={analysis.monthly}
          regionName={analysis.region.name}
        />
        <AnnualChart
          annual={analysis.annual}
          regionName={analysis.region.name}
        />
      </div>
      <SeriesTable monthly={analysis.monthly} annual={analysis.annual} />
      <WarningsList warnings={analysis.warnings} />
      <ProvenancePanel
        source={analysis.source}
        region={analysis.region}
        algorithmVersion={analysis.algorithm_version}
      />
    </section>
  );
}
