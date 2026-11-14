import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AnnualItem } from "../../types/api";
import { formatNumber } from "../../utils/format";
import { hasFittedTrend, isCompleteYear } from "./series";

export interface AnnualChartProps {
  annual: readonly AnnualItem[];
  regionName: string;
}

const OBSERVED_LABEL = "Annual total (mm)";
const FITTED_LABEL = "OLS fitted trend (mm)";

/**
 * Annual precipitation totals (mm). Only years with 12 valid months carry a
 * total; incomplete years are listed but not plotted as values (FR-008).
 *
 * The OLS fitted trend line is drawn ONLY from `annual[].ols_fitted_mm`
 * values computed by the backend — the browser never computes regression
 * (AGENTS.md). Until the API supplies that field the line stays hidden.
 */
export function AnnualChart({ annual, regionName }: AnnualChartProps) {
  const incomplete = annual.filter((item) => !isCompleteYear(item));
  const showTrend = hasFittedTrend(annual);
  const data = annual.map((item) => ({
    year: item.year,
    total: isCompleteYear(item) ? item.precipitation_total_mm : null,
    fitted: typeof item.ols_fitted_mm === "number" ? item.ols_fitted_mm : null,
  }));

  return (
    <figure className="rounded-lg border border-slate-200 bg-white p-4">
      <figcaption className="mb-2">
        <h3 className="text-base font-semibold">Annual precipitation totals</h3>
        <p className="text-sm text-slate-600">
          {regionName} · unit: mm per calendar year · only years with 12 valid
          months are totalled
        </p>
        {showTrend ? (
          <p className="text-sm text-slate-600" data-testid="trend-line-note">
            Dashed line: OLS fitted trend calculated by the backend. It
            describes the past period and is not a forecast.
          </p>
        ) : null}
      </figcaption>
      <div className="h-64 w-full" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            margin={{ top: 8, right: 16, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} minTickGap={16} />
            <YAxis
              tick={{ fontSize: 12 }}
              width={64}
              label={{
                value: "mm",
                angle: -90,
                position: "insideLeft",
                fontSize: 12,
              }}
            />
            <Tooltip
              formatter={(value, name) => [
                `${formatNumber(typeof value === "number" ? value : null)} mm`,
                name,
              ]}
            />
            {showTrend ? <Legend wrapperStyle={{ fontSize: 12 }} /> : null}
            <Bar
              dataKey="total"
              name={OBSERVED_LABEL}
              fill="#0369a1"
              isAnimationActive={false}
            />
            {showTrend ? (
              <Line
                type="linear"
                dataKey="fitted"
                name={FITTED_LABEL}
                stroke="#b45309"
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
                connectNulls={false}
                isAnimationActive={false}
              />
            ) : null}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {incomplete.length > 0 ? (
        <p className="mt-2 text-sm text-amber-800">
          Excluded incomplete year(s):{" "}
          {incomplete
            .map((item) => `${item.year} (${item.valid_months}/12 months)`)
            .join(", ")}
        </p>
      ) : null}
    </figure>
  );
}
