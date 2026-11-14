import { useCallback, useEffect, useState } from "react";

import { getRegionPresets, getVariables } from "../api/client";
import type { RegionDescriptor, VariableDescriptor } from "../types/api";

export type CatalogState =
  | { status: "loading" }
  | { status: "error"; error: unknown }
  | {
      status: "ready";
      variables: VariableDescriptor[];
      regions: RegionDescriptor[];
    };

/**
 * Loads the verified catalog (variables + region presets). Until the
 * backend has reviewed snapshots it answers 503 DATASET_UNAVAILABLE, which
 * surfaces as the `error` state — never as placeholder data.
 */
export function useCatalog(): CatalogState & { reload: () => void } {
  const [state, setState] = useState<CatalogState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });

    Promise.all([
      getVariables({ signal: controller.signal }),
      getRegionPresets({ signal: controller.signal }),
    ])
      .then(([variables, regions]) => {
        setState({
          status: "ready",
          variables: variables.variables.filter((v) => v.supported),
          regions: regions.regions,
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({ status: "error", error });
      });

    return () => controller.abort();
  }, [attempt]);

  const reload = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...state, reload };
}
