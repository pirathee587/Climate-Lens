import { ApiError, CLIENT_ERROR_CODES } from "../api/client";

export interface UserFacingError {
  title: string;
  message: string;
  nextStep: string;
  code: string;
  requestId: string | null;
}

const GUIDANCE: Record<string, { title: string; nextStep: string }> = {
  DATASET_UNAVAILABLE: {
    title: "Verified NASA data is not available yet",
    nextStep:
      "No results are shown because no reviewed snapshot is installed. Nothing has been estimated or filled in.",
  },
  INSUFFICIENT_DATA: {
    title: "Not enough complete years",
    nextStep:
      "Choose a longer period with at least 10 complete calendar years.",
  },
  INVALID_ARGUMENT: {
    title: "The request was not accepted",
    nextStep: "Check the region, years and significance level, then try again.",
  },
  INCOMPATIBLE_DATA: {
    title: "These regions cannot be compared",
    nextStep:
      "The two snapshots do not share the same product, version or run.",
  },
  NOT_FOUND: {
    title: "Not available on this server",
    nextStep:
      "This feature or result is not available from the backend yet. Try again later.",
  },
  ANALYSIS_ERROR: {
    title: "The analysis failed",
    nextStep:
      "An internal error occurred. No substitute result is shown. Quote the request ID when reporting it.",
  },
  [CLIENT_ERROR_CODES.network]: {
    title: "Cannot reach the TerraTrend API",
    nextStep:
      "Start the backend (or check VITE_API_BASE_URL), then select Retry.",
  },
  [CLIENT_ERROR_CODES.timeout]: {
    title: "The request timed out",
    nextStep:
      "The server took too long to answer. Nothing was shown in its place. Please retry.",
  },
};

export function toUserFacingError(error: unknown): UserFacingError {
  if (error instanceof ApiError) {
    const guidance = GUIDANCE[error.code] ?? {
      title: "Something went wrong",
      nextStep: "Please retry. If it keeps failing, report the request ID.",
    };
    return {
      title: guidance.title,
      message: error.message,
      nextStep: guidance.nextStep,
      code: error.code,
      requestId: error.error.request_id || null,
    };
  }
  return {
    title: "Something went wrong",
    message: "An unexpected error occurred in the browser.",
    nextStep: "Please retry.",
    code: "UNKNOWN",
    requestId: null,
  };
}
