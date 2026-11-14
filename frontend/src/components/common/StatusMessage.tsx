import type { ReactNode } from "react";

import { toUserFacingError } from "../../utils/errorMessages";

export function LoadingState({ label }: { label: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 text-slate-700"
    >
      <span
        aria-hidden="true"
        className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-sky-700"
      />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center text-slate-600">
      <p className="font-medium text-slate-800">{title}</p>
      {children ? <div className="mt-1 text-sm">{children}</div> : null}
    </div>
  );
}

export function ErrorNotice({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const view = toUserFacingError(error);
  return (
    <div
      role="alert"
      className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-950"
    >
      <p className="font-semibold">{view.title}</p>
      <p className="mt-1 text-sm">{view.message}</p>
      <p className="mt-1 text-sm">{view.nextStep}</p>
      <p className="mt-2 text-xs text-amber-800">
        Error code: <code>{view.code}</code>
        {view.requestId ? (
          <>
            {" "}
            · Request ID: <code>{view.requestId}</code>
          </>
        ) : null}
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md border border-amber-400 bg-white px-3 py-1.5 text-sm font-medium hover:bg-amber-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
