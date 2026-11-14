import type { VariableDescriptor } from "../../types/api";

/** FR-001: the single supported variable, its definition and output unit. */
export function VariableCard({ variable }: { variable: VariableDescriptor }) {
  return (
    <section
      aria-labelledby="variable-heading"
      className="rounded-lg border border-slate-200 bg-white p-4"
    >
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Variable
      </p>
      <h2 id="variable-heading" className="text-lg font-semibold">
        {variable.display_name}
      </h2>
      <p className="mt-1 text-sm text-slate-700">{variable.description}</p>
      <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <dt className="text-slate-500">Output unit</dt>
        <dd>{variable.aggregation_units} (monthly and annual totals)</dd>
        <dt className="text-slate-500">Resolution</dt>
        <dd>{variable.time_resolution}</dd>
        <dt className="text-slate-500">Dataset</dt>
        <dd>
          {variable.source_dataset_id} · {variable.source_version} ·{" "}
          {variable.source_run}
        </dd>
        <dt className="text-slate-500">Verified coverage</dt>
        <dd>
          {variable.first_available_period} to {variable.last_available_period}
        </dd>
      </dl>
      <p className="mt-3 text-xs text-slate-500">
        Other variables (temperature, vegetation, soil moisture) are not
        supported in this prototype.
      </p>
    </section>
  );
}
