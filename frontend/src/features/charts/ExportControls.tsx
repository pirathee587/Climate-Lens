import { useState } from "react";

import { downloadAnalysisCsv } from "../../api/client";
import { ErrorNotice } from "../../components/common/StatusMessage";

export interface ExportControlsProps {
  analysisId: string | null;
}

type ExportState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; error: unknown };

function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/**
 * CSV export from the server endpoint GET /analyses/{id}/export.csv
 * (docs/API_SPEC.md §7). The browser never builds or recomputes the CSV,
 * so the file always matches the backend's provenance-stamped result.
 * It is fetched (not linked) so failures stay in-app (FR-018, FR-020).
 */
export function ExportControls({ analysisId }: ExportControlsProps) {
  const [state, setState] = useState<ExportState>({ status: "idle" });

  if (!analysisId) {
    return (
      <button
        type="button"
        disabled
        className="cursor-not-allowed rounded-md border border-slate-300 bg-slate-100 px-4 py-2 text-sm text-slate-500"
      >
        Download CSV (run an analysis first)
      </button>
    );
  }

  const handleDownload = async () => {
    setState({ status: "loading" });
    try {
      const blob = await downloadAnalysisCsv(analysisId);
      saveBlob(blob, `terratrend-analysis-${analysisId}.csv`);
      setState({ status: "idle" });
    } catch (error) {
      setState({ status: "error", error });
    }
  };

  const busy = state.status === "loading";

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => void handleDownload()}
          disabled={busy}
          className="rounded-md bg-sky-700 px-4 py-2 text-sm font-medium text-white hover:bg-sky-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-600 focus-visible:ring-offset-2 disabled:cursor-wait disabled:bg-slate-400"
        >
          {busy ? "Preparing CSV…" : "Download CSV"}
        </button>
        <span className="text-xs text-slate-600">
          Monthly series with region, units and snapshot ID. Source metadata is
          shown in the provenance panel.
        </span>
      </div>
      {state.status === "error" ? (
        <ErrorNotice
          error={state.error}
          onRetry={() => void handleDownload()}
        />
      ) : null}
    </div>
  );
}
