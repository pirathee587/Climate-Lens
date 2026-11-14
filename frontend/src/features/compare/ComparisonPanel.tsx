import { useMemo, useRef, useState } from "react";

import { ComparisonControls } from "./ComparisonControls";
import { ComparisonStats } from "./ComparisonStats";
import {
  DEFAULT_ALPHA,
  VERIFIED_SOURCE_MODE,
  type CompareRequest,
  type ComparisonApiError,
  type ComparisonRegion,
  type ComparisonResponse,
} from "./comparisonTypes";
import {
  getAvailableYears,
  getCommonCompleteYears,
  hasIncompatibleDataset,
  MINIMUM_COMPLETE_YEARS,
  type ComparisonSelection,
  validateComparisonSelection,
} from "./comparisonValidation";

export interface ComparisonPanelProps {
  regions: readonly ComparisonRegion[];
  availableYears: readonly number[];
  requestComparison: CompareRequest;
  initialSelection?: Partial<ComparisonSelection>;
}

type ComparisonState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; response: ComparisonResponse }
  | { status: "error"; error: ComparisonApiError };

function getInitialSelection(
  years: readonly number[],
  initialSelection: Partial<ComparisonSelection> | undefined,
): ComparisonSelection {
  const available = getAvailableYears(years);
  return {
    leftRegionId: initialSelection?.leftRegionId ?? "",
    rightRegionId: initialSelection?.rightRegionId ?? "",
    startYear: initialSelection?.startYear ?? available[0] ?? "",
    endYear:
      initialSelection?.endYear ?? available[available.length - 1] ?? "",
  };
}

function toApiError(error: unknown): ComparisonApiError {
  if (
    typeof error === "object" &&
    error !== null &&
    "error" in error &&
    typeof error.error === "object" &&
    error.error !== null &&
    "message" in error.error &&
    typeof error.error.message === "string"
  ) {
    const apiError = error.error as Partial<ComparisonApiError>;
    return {
      code: typeof apiError.code === "string" ? apiError.code : undefined,
      message: apiError.message,
      details: apiError.details,
      request_id:
        typeof apiError.request_id === "string"
          ? apiError.request_id
          : undefined,
    };
  }

  if (typeof error === "object" && error !== null && "message" in error) {
    const candidate = error as Partial<ComparisonApiError>;
    if (typeof candidate.message === "string") {
      return {
        code: typeof candidate.code === "string" ? candidate.code : undefined,
        message: candidate.message,
        details: candidate.details,
        request_id:
          typeof candidate.request_id === "string"
            ? candidate.request_id
            : undefined,
      };
    }
  }

  return { message: "The comparison request could not be completed." };
}

export function ComparisonPanel({
  regions,
  availableYears,
  requestComparison,
  initialSelection,
}: ComparisonPanelProps) {
  const [selection, setSelection] = useState(() =>
    getInitialSelection(availableYears, initialSelection),
  );
  const [validationMessage, setValidationMessage] = useState<string | null>(
    null,
  );
  const [state, setState] = useState<ComparisonState>({ status: "idle" });
  const requestGeneration = useRef(0);
  const years = useMemo(
    () => getAvailableYears(availableYears),
    [availableYears],
  );
  const supportedRegionIds = new Set(
    regions
      .filter(
        (region) => region.id === "jaffna_area" || region.id === "colombo_area",
      )
      .map((region) => region.id),
  );

  const handleSubmit = async () => {
    const validationError = validateComparisonSelection(selection, years);
    if (validationError) {
      setValidationMessage(validationError);
      return;
    }

    if (
      selection.leftRegionId === "" ||
      selection.rightRegionId === "" ||
      selection.startYear === "" ||
      selection.endYear === ""
    ) {
      setValidationMessage("Select two regions and a complete year range.");
      return;
    }

    setValidationMessage(null);
    setState({ status: "loading" });
    const generation = ++requestGeneration.current;

    try {
      const response = await requestComparison({
        variable_id: "precipitation",
        left_region_id: selection.leftRegionId,
        right_region_id: selection.rightRegionId,
        start_year: selection.startYear,
        end_year: selection.endYear,
        alpha: DEFAULT_ALPHA,
        source_mode: VERIFIED_SOURCE_MODE,
      });
      if (generation === requestGeneration.current) {
        setState({ status: "success", response });
      }
    } catch (error) {
      if (generation === requestGeneration.current) {
        setState({ status: "error", error: toApiError(error) });
      }
    }
  };

  if (years.length === 0 || supportedRegionIds.size < 2) {
    return <p role="status">Verified comparison data are unavailable.</p>;
  }

  const response = state.status === "success" ? state.response : null;
  const commonYears = response ? getCommonCompleteYears(response) : [];
  const insufficientCommonYears =
    response !== null && commonYears.length < MINIMUM_COMPLETE_YEARS;
  const incompatibleDataset =
    response !== null && hasIncompatibleDataset(response.dataset_compatibility);

  return (
    <section aria-labelledby="comparison-panel-heading">
      <h2 id="comparison-panel-heading">Regional comparison</h2>
      <ComparisonControls
        availableYears={years}
        disabled={state.status === "loading"}
        onSelectionChange={(nextSelection) => {
          setSelection(nextSelection);
          setValidationMessage(null);
        }}
        onSubmit={handleSubmit}
        regions={regions}
        selection={selection}
        validationMessage={validationMessage}
      />

      {state.status === "idle" ? (
        <p role="status">Select two verified regions to compare.</p>
      ) : null}
      {state.status === "loading" ? (
        <p role="status" aria-live="polite">
          Loading independent regional analyses…
        </p>
      ) : null}
      {state.status === "error" ? (
        <p role="alert">
          {state.error.code ? `${state.error.code}: ` : ""}
          {state.error.message}
        </p>
      ) : null}

      {response ? (
        <>
          <p>
            Requested period: {response.shared_requested_period.start_year}–
            {response.shared_requested_period.end_year}.
          </p>
          {incompatibleDataset ? (
            <p role="alert">
              The returned datasets are not fully compatible for a like-for-like
              comparison.
            </p>
          ) : null}
          {insufficientCommonYears ? (
            <p role="alert">
              Fewer than {MINIMUM_COMPLETE_YEARS} common complete years were
              returned; interpret the comparison as insufficient data.
            </p>
          ) : null}
          {(response.warnings ?? []).map((warning, index) => (
            <p key={`${index}-${warning}`} role="note">
              {warning}
            </p>
          ))}
          <p role="note">
            The two trend tests are independent. This interface does not test
            whether the two slopes differ significantly.
          </p>
          <div>
            <ComparisonStats
              analysis={response.left}
              commonYears={commonYears}
            />
            <ComparisonStats
              analysis={response.right}
              commonYears={commonYears}
            />
          </div>
        </>
      ) : null}
    </section>
  );
}
