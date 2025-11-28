import { useCallback, useEffect, useRef } from "react";
import { logAnalytics, type AnalyticsMeta } from "./analytics";

type UseAnalyticsOptions = {
  autoPageView?: boolean;
  projectId?: string | null;
  userId?: string | null;
};

export function useAnalytics(opts: UseAnalyticsOptions = {}) {
  const { autoPageView = true, projectId = null, userId = null } = opts;
  const mounted = useRef(false);

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true;
      if (autoPageView && typeof window !== "undefined") {
        logAnalytics("page_view", { route: window.location?.pathname ?? "/" }, projectId, userId);
      }
    }
  }, [autoPageView, projectId, userId]);

  const logEvent = useCallback(
    (event: string, meta: AnalyticsMeta = {}, overrides?: { projectId?: string | null; userId?: string | null }) => {
      return logAnalytics(
        event,
        meta,
        overrides?.projectId ?? projectId ?? null,
        overrides?.userId ?? userId ?? null
      );
    },
    [projectId, userId]
  );

  return { logEvent };
}

export default useAnalytics;
