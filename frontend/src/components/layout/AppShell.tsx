import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:shadow"
      >
        Skip to main content
      </a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <div>
            <p className="text-xl font-bold tracking-tight text-sky-900">
              TerraTrend
            </p>
            <p className="text-sm text-slate-600">
              Earth Systems Trend Detective
            </p>
          </div>
          <span className="rounded-full border border-amber-400 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">
            Student prototype · not an official NASA product
          </span>
        </div>
      </header>

      <div role="note" className="border-b border-sky-100 bg-sky-50">
        <p className="mx-auto max-w-6xl px-4 py-2 text-sm text-sky-950">
          Explore how rainfall has changed using NASA satellite-derived
          estimates. Results are exploratory and statistical significance does
          not imply causation.
        </p>
      </div>

      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        {children}
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl space-y-1 px-4 py-4 text-xs text-slate-600">
          <p>
            Precipitation data: NASA/JAXA GPM IMERG Final monthly product,
            courtesy of NASA. See the{" "}
            <a
              className="underline hover:text-slate-900"
              href="https://gpm.nasa.gov/data/imerg"
              target="_blank"
              rel="noreferrer noopener"
            >
              GPM IMERG documentation
            </a>
            . NASA does not endorse this project.
          </p>
          <p>
            NASA Space Apps Challenge 2026 student team project. Map tiles ©
            OpenStreetMap contributors.
          </p>
        </div>
      </footer>
    </div>
  );
}
