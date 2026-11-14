import type { ReactNode } from "react";

import type { RegionDescriptor, SourceDescriptor } from "../../types/api";
import { formatBBox, formatTimestamp, humanize } from "../../utils/format";

export interface ProvenancePanelProps {
  source: SourceDescriptor;
  region: RegionDescriptor;
  algorithmVersion: string;
}

/** FR-005: every result shows its full source provenance. */
export function ProvenancePanel({
  source,
  region,
  algorithmVersion,
}: ProvenancePanelProps) {
  const rows: [string, ReactNode][] = [
    ["Collection", source.collection_id],
    ["Version / run", `${source.version} · ${source.run_type}`],
    ["Original variable", <code key="v">{source.original_variable}</code>],
    ["Original unit", source.original_unit],
    ["Spatial aggregation", source.aggregation_method],
    ["Region", `${region.name} (${humanize(region.label_type)})`],
    ["Bounding box (WGS84)", formatBBox(region.bbox)],
    ["Geometry source", region.geometry_source],
    ["Snapshot ID", <code key="s">{source.snapshot_id}</code>],
    [
      "Snapshot SHA-256",
      <code key="h" className="break-all">
        {source.snapshot_sha256}
      </code>,
    ],
    ["Retrieved", formatTimestamp(source.retrieved_at)],
    ["Algorithm version", algorithmVersion],
  ];

  return (
    <section
      aria-labelledby="provenance-heading"
      className="rounded-lg border border-slate-200 bg-white p-4"
    >
      <h3 id="provenance-heading" className="text-base font-semibold">
        Data provenance
      </h3>
      <dl className="mt-2 grid grid-cols-1 gap-x-4 gap-y-1 text-sm sm:grid-cols-[max-content_1fr]">
        {rows.map(([label, value]) => (
          <div key={label} className="contents">
            <dt className="text-slate-500">{label}</dt>
            <dd className="min-w-0">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-sm">
        Source:{" "}
        <a
          href={source.source_uri}
          target="_blank"
          rel="noreferrer noopener"
          className="text-sky-800 underline hover:text-sky-950"
        >
          {source.source_uri}
        </a>
      </p>
    </section>
  );
}
