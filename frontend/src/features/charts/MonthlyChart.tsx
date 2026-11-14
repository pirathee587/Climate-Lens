import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MonthlyItem } from "../../types/api";
import { formatNumber } from "../../utils/format";

export interface MonthlyChartProps {
  monthly: readonly MonthlyItem[];
  regionName: string;
}

/**
 * Monthly precipitation totals (mm) exactly as returned by the API.
 * Missing months are `null` and drawn as gaps — never as zero (FR-006).
 */
export function MonthlyChart({ monthly, regionName }: MonthlyChartProps) {
  const missing = monthly.filter(
    (m) => m.precipitation_total_mm === null,
  ).length;

  return (
    <figure className="rounded-lg border border-slate-200 bg-white p-4">
      <figcaption className="mb-2">
        <h3 className="text-base font-semibold">
          Monthly precipitation totals
        </h3>
        <p className="text-sm text-slate-600">
          {regionName} · {monthly.length} months · unit: mm per month
          {missing > 0 ? ` · ${missing} missing month(s) shown as gaps` : ""}
        </p>
      </figcaption>
      <div className="h-64 w-full" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={[...monthly]}
            margin={{ top: 8, right: 16, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="period" minTickGap={32} tick={{ fontSize: 12 }} />
            <YAxis
              tick={{ fontSize: 12 }}
              width={56}
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
                "Total",
              ]}
            />
            <Line
              type="monotone"
              dataKey="precipitation_total_mm"
              name="Monthly total (mm)"
              stroke="#0369a1"
              strokeWidth={1.5}
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        The full values are listed in the data table below.
      </p>
    </figure>
  );
}
