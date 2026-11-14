import { useState } from "react";

import type { AnnualItem, MonthlyItem } from "../../types/api";
import { formatNumber, formatPercent } from "../../utils/format";

export interface SeriesTableProps {
  monthly: readonly MonthlyItem[];
  annual: readonly AnnualItem[];
}

/** Text alternative for both charts (NFR-009). Collapsed by default. */
export function SeriesTable({ monthly, annual }: SeriesTableProps) {
  const [view, setView] = useState<"annual" | "monthly">("annual");

  return (
    <details className="rounded-lg border border-slate-200 bg-white p-4">
      <summary className="cursor-pointer font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600">
        Data table (accessible view of the charts)
      </summary>
      <div className="mt-3 flex gap-2" role="group" aria-label="Table level">
        {(["annual", "monthly"] as const).map((option) => (
          <button
            key={option}
            type="button"
            aria-pressed={view === option}
            onClick={() => setView(option)}
            className={`rounded-md border px-3 py-1 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 ${
              view === option
                ? "border-sky-700 bg-sky-700 text-white"
                : "border-slate-300 bg-white"
            }`}
          >
            {option === "annual" ? "Annual" : "Monthly"}
          </button>
        ))}
      </div>
      <div className="mt-3 max-h-80 overflow-auto">
        {view === "annual" ? (
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Annual precipitation totals</caption>
            <thead className="sticky top-0 bg-white">
              <tr>
                <th scope="col" className="py-1 pr-4">
                  Year
                </th>
                <th scope="col" className="py-1 pr-4">
                  Total (mm)
                </th>
                <th scope="col" className="py-1">
                  Valid months
                </th>
              </tr>
            </thead>
            <tbody>
              {annual.map((row) => (
                <tr key={row.year} className="border-t border-slate-100">
                  <td className="py-1 pr-4">{row.year}</td>
                  <td className="py-1 pr-4">
                    {formatNumber(row.precipitation_total_mm)}
                  </td>
                  <td className="py-1">{row.valid_months}/12</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Monthly precipitation totals</caption>
            <thead className="sticky top-0 bg-white">
              <tr>
                <th scope="col" className="py-1 pr-4">
                  Month
                </th>
                <th scope="col" className="py-1 pr-4">
                  Total (mm)
                </th>
                <th scope="col" className="py-1">
                  Valid coverage
                </th>
              </tr>
            </thead>
            <tbody>
              {monthly.map((row) => (
                <tr key={row.period} className="border-t border-slate-100">
                  <td className="py-1 pr-4">{row.period}</td>
                  <td className="py-1 pr-4">
                    {formatNumber(row.precipitation_total_mm)}
                  </td>
                  <td className="py-1">{formatPercent(row.valid_fraction)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </details>
  );
}
