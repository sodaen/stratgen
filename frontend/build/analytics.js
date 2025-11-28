function getSessionId() {
    try {
        let s = sessionStorage.getItem("sid");
        if (!s) {
            s = "sid-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
            sessionStorage.setItem("sid", s);
        }
        return s;
    }
    catch {
        return null;
    }
}
function apiBase() {
    try {
        if (typeof window !== "undefined") {
            const o = window.location.origin || "";
            if (o.includes(":5173") || o.includes(":5174"))
                return "http://127.0.0.1:8001";
        }
    }
    catch { /* noop */ }
    return ""; // same-origin
}
export async function logAnalytics(event, meta = {}, opts = {}) {
    var _a, _b;
    const body = {
        event,
        meta,
        project_id: (_a = opts.projectId) !== null && _a !== void 0 ? _a : null,
        user_id: (_b = opts.userId) !== null && _b !== void 0 ? _b : null,
        session_id: getSessionId(),
    };
    try {
        const res = await fetch(apiBase() + "/analytics/log", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            mode: "cors",
            body: JSON.stringify(body),
        });
        if (!res.ok && typeof console !== "undefined") {
            console.warn("analytics/log failed:", res.status, await res.text());
        }
        return res.ok;
    }
    catch (e) {
        if (typeof console !== "undefined")
            console.warn("analytics/log error:", e);
        return false;
    }
}
export default logAnalytics;
//# sourceMappingURL=analytics.js.map