import { useCallback, useEffect, useRef } from "react";
import { logAnalytics } from "./analytics";
export function useAnalytics(opts = {}) {
    const { autoPageView = true, projectId = null, userId = null } = opts;
    const mounted = useRef(false);
    useEffect(() => {
        var _a, _b;
        if (!mounted.current) {
            mounted.current = true;
            if (autoPageView && typeof window !== "undefined") {
                logAnalytics("page_view", { route: (_b = (_a = window.location) === null || _a === void 0 ? void 0 : _a.pathname) !== null && _b !== void 0 ? _b : "/" }, projectId, userId);
            }
        }
    }, [autoPageView, projectId, userId]);
    const logEvent = useCallback((event, meta = {}, overrides) => {
        var _a, _b, _c, _d;
        return logAnalytics(event, meta, (_b = (_a = overrides === null || overrides === void 0 ? void 0 : overrides.projectId) !== null && _a !== void 0 ? _a : projectId) !== null && _b !== void 0 ? _b : null, (_d = (_c = overrides === null || overrides === void 0 ? void 0 : overrides.userId) !== null && _c !== void 0 ? _c : userId) !== null && _d !== void 0 ? _d : null);
    }, [projectId, userId]);
    return { logEvent };
}
export default useAnalytics;
//# sourceMappingURL=useAnalytics.js.map