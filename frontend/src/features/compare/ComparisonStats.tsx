import type { IndependentComparisonAnalysis } from "./comparisonTypes";

export interface ComparisonStatsProps {
  analysis: IndependentComparisonAnalysis;
  commonYears: readonly number[];
}

function formatNumber(value: number | null | undefined, suffix = "") {
  return value === null || value === undefined || !Number.isFinite(value)
    ? "Unavailable"
    : `${value}${suffix}`;
}

function formatText(value: string | null | undefined) {
  return value === null || value === undefined || value.length === 0
    ? "Unavailable"
    : value;
}

export function ComparisonStats({
  analysis,
  commonYears,
}: ComparisonStatsProps) {
  const { region, statistics, source } = analysis;
  const confidenceInterval =
    statistics.sen_slope_ci95_mm_per_year ?? [null, null];

  return (
    <section
      aria-labelledby={`${region.id}-comparison-heading`}
      className="comparison-result-column"
    >
      <h3 id={`${region.id}-comparison-heading`}>{region.name}</h3>
      <dl>
        <div>
          <dt>Sample years</dt>
          <dd>{formatNumber(statistics.sample_years)}</dd>
        </div>
        <div>
          <dt>OLS slope</dt>
          <dd>{formatNumber(statistics.ols_slope_mm_per_year, " mm/year")}</dd>
        </div>
        <div>
          <dt>Sen slope</dt>
          <dd>{formatNumber(statistics.sen_slope_mm_per_year, " mm/year")}</dd>
        </div>
        <div>
          <dt>Sen slope 95% CI</dt>
          <dd>
            {formatNumber(confidenceInterval[0])} to{" "}
            {formatNumber(confidenceInterval[1])} mm/year
          </dd>
        </div>
        <div>
          <dt>Mann–Kendall p-value</dt>
          <dd>{formatNumber(statistics.mann_kendall_p_value)}</dd>
        </div>
        <div>
          <dt>Significance status</dt>
          <dd>{formatText(statistics.significance_status)}</dd>
        </div>
        <div>
          <dt>Direction</dt>
          <dd>{formatText(statistics.direction)}</dd>
        </div>
        <div>
          <dt>Common complete years</dt>
          <dd>{commonYears.length ? commonYears.join(", ") : "Unavailable"}</dd>
        </div>
      </dl>

      <h4>Annual precipitation</h4>
      <table>
        <caption>{region.name} annual precipitation totals</caption>
        <thead>
          <tr>
            <th scope="col">Year</th>
            <th scope="col">Total (mm)</th>
            <th scope="col">Valid months</th>
          </tr>
        </thead>
        <tbody>
          {(analysis.annual ?? []).map((record, index) => {
            if (record === null || typeof record !== "object") {
              return (
                <tr key={`invalid-${index}`}>
                  <th scope="row">Unavailable</th>
                  <td>Unavailable</td>
                  <td>Unavailable</td>
                </tr>
              );
            }

            return (
              <tr key={`${record.year}-${index}`}>
                <th scope="row">{formatNumber(record.year)}</th>
                <td>{formatNumber(record.precipitation_total_mm)}</td>
                <td>{formatNumber(record.valid_months)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h4>Source and provenance</h4>
      <dl>
        <div>
          <dt>Collection</dt>
          <dd>{formatText(source.collection_id)}</dd>
        </div>
        <div>
          <dt>Version / run</dt>
          <dd>
            {formatText(source.version)} / {formatText(source.run_type)}
          </dd>
        </div>
        <div>
          <dt>Original variable / unit</dt>
          <dd>
            {formatText(source.original_variable)} /{" "}
            {formatText(source.original_unit)}
          </dd>
        </div>
        <div>
          <dt>Snapshot</dt>
          <dd>{formatText(source.snapshot_id)}</dd>
        </div>
        <div>
          <dt>Snapshot SHA-256</dt>
          <dd>{formatText(source.snapshot_sha256)}</dd>
        </div>
        <div>
          <dt>Retrieved at</dt>
          <dd>{formatText(source.retrieved_at)}</dd>
        </div>
        <div>
          <dt>Source URI</dt>
          <dd>{formatText(source.source_uri)}</dd>
        </div>
        <div>
          <dt>Aggregation method</dt>
          <dd>{formatText(source.aggregation_method)}</dd>
        </div>
      </dl>

      <p>
        Method: {formatText(statistics.mann_kendall_method)}. Assumptions
        status: {" "}
        {formatText(statistics.assumptions_status)}.
      </p>
    </section>
  );
}
