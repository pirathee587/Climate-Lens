import { STANDING_CAVEATS } from "./caveats";

export function WarningsList({ warnings }: { warnings: readonly string[] }) {
  return (
    <section
      aria-labelledby="warnings-heading"
      className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-950"
    >
      <h3 id="warnings-heading" className="text-base font-semibold">
        Warnings and limitations
      </h3>
      {warnings.length > 0 ? (
        <>
          <p className="mt-2 text-sm font-medium">From this analysis:</p>
          <ul
            className="mt-1 list-disc space-y-1 pl-5 text-sm"
            data-testid="analysis-warnings"
          >
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </>
      ) : (
        <p className="mt-2 text-sm">
          The backend returned no analysis-specific warnings.
        </p>
      )}
      <p className="mt-3 text-sm font-medium">Always applies:</p>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
        {STANDING_CAVEATS.map((caveat) => (
          <li key={caveat}>{caveat}</li>
        ))}
      </ul>
    </section>
  );
}
