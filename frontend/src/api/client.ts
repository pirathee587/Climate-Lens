import type {
  AnalysisRequest,
  AnalysisResponse,
  ComparisonRequest,
  ComparisonResponse,
  ErrorDetail,
  RegionsResponse,
  VariablesResponse,
} from "../types/api";

const DEFAULT_BASE_URL = "http://localhost:8000/api/v1";

export function getApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL as string | undefined;
  return (configured?.trim() || DEFAULT_BASE_URL).replace(/\/+$/, "");
}

/**
 * Error raised for every failed request. It carries the backend error
 * envelope under `.error` so components that expect the
 * `{ error: { code, message, details, request_id } }` shape (e.g. the
 * comparison panel) can read it directly.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly error: ErrorDetail;

  constructor(status: number, error: ErrorDetail) {
    super(error.message);
    this.name = "ApiError";
    this.status = status;
    this.error = error;
  }

  get code(): string {
    return this.error.code;
  }
}

/** Client-side codes used when no backend error envelope is available. */
export const CLIENT_ERROR_CODES = {
  network: "NETWORK_ERROR",
  invalidResponse: "INVALID_RESPONSE",
  timeout: "TIMEOUT",
} as const;

/** Upper bound for any API call so the UI never spins forever (TC-015). */
export const DEFAULT_TIMEOUT_MS = 30_000;

function isErrorDetail(value: unknown): value is ErrorDetail {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.code === "string" && typeof candidate.message === "string"
  );
}

function parseErrorBody(status: number, body: unknown): ApiError {
  if (
    typeof body === "object" &&
    body !== null &&
    "error" in body &&
    isErrorDetail((body as { error: unknown }).error)
  ) {
    const detail = (body as { error: ErrorDetail }).error;
    return new ApiError(status, {
      code: detail.code,
      message: detail.message,
      details: detail.details ?? {},
      request_id: detail.request_id ?? "",
    });
  }
  return new ApiError(status, {
    code: CLIENT_ERROR_CODES.invalidResponse,
    message: `The server returned an unexpected response (HTTP ${status}).`,
    details: {},
    request_id: "",
  });
}

export interface RequestOptions {
  signal?: AbortSignal;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

function clientError(code: string, message: string): ApiError {
  return new ApiError(0, { code, message, details: {}, request_id: "" });
}

/**
 * fetch with a timeout. A caller abort is re-thrown as-is (so components can
 * ignore it); a timeout or network failure becomes a retryable ApiError.
 */
async function fetchWithTimeout(
  path: string,
  init: RequestInit,
  { signal, fetchImpl = fetch, timeoutMs = DEFAULT_TIMEOUT_MS }: RequestOptions,
): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const forwardAbort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener("abort", forwardAbort, { once: true });

  try {
    return await fetchImpl(`${getApiBaseUrl()}${path}`, {
      ...init,
      signal: controller.signal,
    });
  } catch (cause) {
    if (timedOut) {
      throw clientError(
        CLIENT_ERROR_CODES.timeout,
        `The TerraTrend API did not respond within ${Math.round(timeoutMs / 1000)} seconds.`,
      );
    }
    if (signal?.aborted) throw cause;
    throw clientError(
      CLIENT_ERROR_CODES.network,
      "Could not reach the TerraTrend API. Check that the backend is running.",
    );
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", forwardAbort);
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function requestJson<T>(
  path: string,
  init: RequestInit,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetchWithTimeout(
    path,
    { ...init, headers: { Accept: "application/json", ...init.headers } },
    options,
  );

  const body = await readJson(response);

  if (!response.ok) {
    throw parseErrorBody(response.status, body);
  }
  if (body === null) {
    throw parseErrorBody(response.status, null);
  }
  return body as T;
}

function postJson<T>(
  path: string,
  payload: unknown,
  options?: RequestOptions,
): Promise<T> {
  return requestJson<T>(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    options,
  );
}

export function getVariables(
  options?: RequestOptions,
): Promise<VariablesResponse> {
  return requestJson<VariablesResponse>(
    "/variables",
    { method: "GET" },
    options,
  );
}

export function getRegionPresets(
  options?: RequestOptions,
): Promise<RegionsResponse> {
  return requestJson<RegionsResponse>(
    "/regions/presets",
    { method: "GET" },
    options,
  );
}

export function postAnalysis(
  request: AnalysisRequest,
  options?: RequestOptions,
): Promise<AnalysisResponse> {
  return postJson<AnalysisResponse>("/analyses", request, options);
}

export function postComparison(
  request: ComparisonRequest,
  options?: RequestOptions,
): Promise<ComparisonResponse> {
  return postJson<ComparisonResponse>("/comparisons", request, options);
}

function exportCsvPath(analysisId: string): string {
  return `/analyses/${encodeURIComponent(analysisId)}/export.csv`;
}

/** URL of the server-side CSV export (docs/API_SPEC.md §7). */
export function analysisExportCsvUrl(analysisId: string): string {
  return `${getApiBaseUrl()}${exportCsvPath(analysisId)}`;
}

/**
 * Fetches the server-built CSV as a Blob. Done via fetch (not a plain link)
 * because the API is cross-origin — browsers ignore `download` there — and
 * so a 404/503 is shown in-app instead of navigating to a raw JSON page.
 */
export async function downloadAnalysisCsv(
  analysisId: string,
  options: RequestOptions = {},
): Promise<Blob> {
  const response = await fetchWithTimeout(
    exportCsvPath(analysisId),
    { method: "GET", headers: { Accept: "text/csv" } },
    options,
  );
  if (!response.ok) {
    throw parseErrorBody(response.status, await readJson(response));
  }
  return response.blob();
}
