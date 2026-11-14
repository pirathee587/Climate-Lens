import {
  analysisExportCsvUrl,
  ApiError,
  CLIENT_ERROR_CODES,
  downloadAnalysisCsv,
  getVariables,
  postAnalysis,
} from "../../src/api/client";
import {
  errorBody,
  jsonResponse,
  syntheticVariables,
} from "../fixtures/synthetic";

describe("api client", () => {
  it("returns parsed JSON on success", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(jsonResponse(syntheticVariables));
    await expect(getVariables({ fetchImpl })).resolves.toEqual(
      syntheticVariables,
    );
    expect(fetchImpl.mock.calls[0]?.[0]).toMatch(/\/variables$/);
  });

  it("maps the backend error envelope to ApiError", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(errorBody("DATASET_UNAVAILABLE", "No snapshot."), 503),
      );
    const error = await getVariables({ fetchImpl }).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(503);
    expect((error as ApiError).code).toBe("DATASET_UNAVAILABLE");
    expect((error as ApiError).error.request_id).toMatch(/^1111/);
  });

  it("handles non-JSON error bodies", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response("<html>", { status: 502 }));
    const error = (await getVariables({ fetchImpl }).catch(
      (e: unknown) => e,
    )) as ApiError;
    expect(error.code).toBe(CLIENT_ERROR_CODES.invalidResponse);
  });

  it("reports network failures with a client code", async () => {
    const fetchImpl = vi
      .fn()
      .mockRejectedValue(new TypeError("Failed to fetch"));
    const error = (await getVariables({ fetchImpl }).catch(
      (e: unknown) => e,
    )) as ApiError;
    expect(error.code).toBe(CLIENT_ERROR_CODES.network);
  });

  it("POSTs analysis requests as JSON", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({}));
    await postAnalysis(
      {
        variable_id: "precipitation",
        region_id: "jaffna_area",
        start_year: 2001,
        end_year: 2010,
        alpha: 0.05,
        source_mode: "verified_snapshot",
      },
      { fetchImpl },
    );
    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/analyses$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toMatchObject({
      region_id: "jaffna_area",
    });
  });

  it("times out instead of hanging forever", async () => {
    // A fetch that never resolves until it is aborted.
    const fetchImpl = vi.fn(
      (_url: RequestInfo | URL, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          );
        }),
    );
    const error = (await getVariables({ fetchImpl, timeoutMs: 20 }).catch(
      (e: unknown) => e,
    )) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe(CLIENT_ERROR_CODES.timeout);
  });

  it("re-throws a caller abort untouched", async () => {
    const controller = new AbortController();
    const fetchImpl = vi.fn(
      (_url: RequestInfo | URL, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          );
        }),
    );
    const pending = getVariables({ fetchImpl, signal: controller.signal });
    controller.abort();
    await expect(pending).rejects.toHaveProperty("name", "AbortError");
  });

  it("downloads CSV as a blob and maps export errors", async () => {
    const ok = vi
      .fn()
      .mockResolvedValue(new Response("a,b\n1,2\n", { status: 200 }));
    const blob = await downloadAnalysisCsv("id-1", { fetchImpl: ok });
    // jsdom's Blob lacks .text(); size proves the body was passed through.
    expect(blob.size).toBe("a,b\n1,2\n".length);

    const missing = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(errorBody("NOT_FOUND", "Resource not found."), 404),
      );
    const error = (await downloadAnalysisCsv("id-1", {
      fetchImpl: missing,
    }).catch((e: unknown) => e)) as ApiError;
    expect(error.code).toBe("NOT_FOUND");
  });

  it("builds an encoded export URL", () => {
    expect(analysisExportCsvUrl("a/b")).toMatch(
      /\/analyses\/a%2Fb\/export\.csv$/,
    );
  });
});
