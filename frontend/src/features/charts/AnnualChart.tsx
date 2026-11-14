import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AnnualItem } from "../../types/api";
import { formatNumber } from "../../utils/format";
import { isCompleteYear } from "./series";

export interface AnnualChartProps {
  annual: readonly AnnualItem[];
  regionName: string;
}

/**
 * Annual precipitation totals (mm). Only years with 12 valid months carry a
 * total; incomplete years are listed but not plotted as values (FR-008).
 *
 * NOTE: no fitted OLS line is drawn yet. The API returns the OLS slope but
 * not its intercept, and the frontend must not compute regression itself
 * (AGENTS.md: "frontend only displays returned results"). See PR notes.
 */
export function AnnualChart({ annual, regionName }: AnnualChartProps) {
  const incomplete = annual.filter((item) => !isCompleteYear(item));
  const data = annual.map((item) => ({
    year: item.year,
    total: isCompleteYear(item) ? item.precipitation_total_mm : null,
  }));

  return (
    <figure className="rounded-lg border border-slate-200 bg-white p-4">
      <figcaption className="mb-2">
        <h3 className="text-base font-semibold">Annual precipitation totals</h3>
        <p className="text-sm text-slate-600">
          {regionName} · unit: mm per calendar year · only years with 12 valid
          months are totalled
        </p>
      </figcaption>
      <div className="h-64 w-full" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
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
              formatter={(value) => [
                `${formatNumber(typeof value === "number" ? value : null)} mm`,
                "Annual total",
              ]}
            />
            <Bar
              dataKey="total"
              name="Annual total (mm)"
              isAnimationActive={false}
            >
              {data.map((entry) => (
                <Cell key={entry.year} fill="#0369a1" />
              ))}
            </Bar>
          </BarChart>
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
