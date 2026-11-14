import type {
  Direction,
  SignificanceStatus,
  Statistics,
} from "../../types/api";
import {
  formatInterval,
  formatNumber,
  formatPValue,
  formatSigned,
  humanize,
  NOT_AVAILABLE,
} from "../../utils/format";

export interface TrendSummaryProps {
  statistics: Statistics;
  regionName: string;
  analyzedYears: readonly number[];
  sourceLabel: string;
}

const SIGNIFICANCE_VIEW: Record<
  SignificanceStatus,
  { label: string; symbol: string; className: string; explanation: string }
> = {
  significant: {
    label: "Statistically significant",
    symbol: "●",
    className: "border-emerald-700 bg-emerald-50 text-emerald-900",
    explanation:
      "Evidence of a monotonic trend at the chosen threshold. This is not evidence of its cause.",
  },
  not_significant: {
    label: "Not statistically significant",
    symbol: "○",
    className: "border-slate-500 bg-slate-50 text-slate-900",
    explanation:
      "The data do not show strong enough evidence of a monotonic trend at this threshold.",
  },
  indeterminate: {
    label: "Indeterminate",
    symbol: "◇",
    className: "border-amber-600 bg-amber-50 text-amber-950",
    explanation:
      "The trend cannot be evaluated reliably (insufficient data or test assumptions not satisfied). Any p-value is indicative only.",
  },
};

const DIRECTION_LABEL: Record<Direction, string> = {
  increasing: "Increasing (estimated)",
  decreasing: "Decreasing (estimated)",
  no_clear_direction: "No clear direction",
};

function MetricCard({
  label,
  value,
  unit,
  hint,
}: {
  label: string;
  value: string;
  unit?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="mt-1 text-lg font-semibold text-slate-900">
        {value}
        {unit && value !== NOT_AVAILABLE ? (
          <span className="ml-1 text-sm font-normal text-slate-600">
            {unit}
          </span>
        ) : null}
      </dd>
      {hint ? <dd className="mt-0.5 text-xs text-slate-500">{hint}</dd> : null}
    </div>
  );
}

function yearSpan(years: readonly number[]): string {
  if (years.length === 0) return "no complete years";
  return `${years[0]}–${years[years.length - 1]} (${years.length} complete years)`;
}

/**
 * Trend findings cards + plain-language interpretation
 * (docs/SCIENTIFIC_METHOD.md §9). Every number comes from the API.
 */
export function TrendSummary({
  statistics,
  regionName,
  analyzedYears,
  sourceLabel,
}: TrendSummaryProps) {
  const significance = SIGNIFICANCE_VIEW[statistics.significance_status];
  const pValue = formatPValue(statistics.mann_kendall_p_value);

  return (
    <section aria-labelledby="trend-summary-heading" className="space-y-3">
      <h3 id="trend-summary-heading" className="text-base font-semibold">
        Trend findings
      </h3>

      <div
        className={`rounded-lg border-l-4 p-3 ${significance.className}`}
        data-testid="significance-status"
      >
        <p className="font-semibold">
          <span aria-hidden="true" className="mr-2">
            {significance.symbol}
          </span>
          {significance.label}
          <span className="ml-2 text-sm font-normal">
            (two-sided Mann–Kendall, α = {statistics.alpha})
          </span>
        </p>
        <p className="mt-1 text-sm">{significance.explanation}</p>
      </div>

      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          label="Sen slope"
          value={formatSigned(statistics.sen_slope_mm_per_year)}
          unit="mm/year"
          hint="Robust trend magnitude"
        />
        <MetricCard
          label="Sen slope 95% CI"
          value={formatInterval(statistics.sen_slope_ci95_mm_per_year)}
          unit="mm/year"
          hint="Confidence interval of the slope"
        />
        <MetricCard
          label="OLS slope"
          value={formatSigned(statistics.ols_slope_mm_per_year)}
          unit="mm/year"
          hint={`R² = ${formatNumber(statistics.ols_r_squared, 2)} (descriptive fit)`}
        />
        <MetricCard
          label="Mann–Kendall p-value"
          value={pValue}
          hint={humanize(statistics.mann_kendall_method)}
        />
        <MetricCard
          label="Direction"
          value={
            statistics.direction
              ? DIRECTION_LABEL[statistics.direction]
              : NOT_AVAILABLE
          }
          hint="Direction is not significance"
        />
        <MetricCard
          label="Sample size"
          value={
            statistics.sample_years === null
              ? NOT_AVAILABLE
              : String(statistics.sample_years)
          }
          unit="complete years"
          hint={`Assumptions: ${humanize(statistics.assumptions_status)}`}
        />
      </dl>

      <p
        className="rounded-lg bg-slate-100 p-3 text-sm text-slate-800"
        data-testid="interpretation"
      >
        In the <strong>{regionName}</strong> during{" "}
        <strong>{yearSpan(analyzedYears)}</strong>, the estimated annual
        rainfall total trend was{" "}
        <strong>
          {formatSigned(statistics.sen_slope_mm_per_year)} mm/year
        </strong>{" "}
        (Sen slope). The Mann–Kendall test returned{" "}
        <strong>p = {pValue}</strong>, classified as{" "}
        <strong>{significance.label.toLowerCase()}</strong> at α ={" "}
        {statistics.alpha}. These results describe statistical evidence in
        satellite-derived estimates ({sourceLabel}),{" "}
        <strong>not the cause</strong> of any change.
      </p>
    </section>
  );
}
