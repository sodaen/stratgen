// Lightweight analytics helper (TypeScript, same-origin or cross-origin)
export type AnalyticsMeta = Record<string, any>;
export interface AnalyticsOptions {
  projectId?: string | null;
  userId?: string | null;
}

function getSessionId(): string | null {
  try {
    let s = sessionStorage.getItem("sid");
    if (!s) {
      s = "sid-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem("sid", s);
    }
    return s;
  } catch {
    return null;
  }
}

function apiBase(): string {
  try {
    if (typeof window !== "undefined") {
      const o = window.location.origin || "";
      if (o.includes(":5173") || o.includes(":5174")) return "http://127.0.0.1:8001";
    }
  } catch { /* noop */ }
  return ""; // same-origin
}

export async function logAnalytics(
  event: string,
  meta: AnalyticsMeta = {},
  opts: AnalyticsOptions = {}
): Promise<boolean> {
  const body = {
    event,
    meta,
    project_id: opts.projectId ?? null,
    user_id: opts.userId ?? null,
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
  } catch (e) {
    if (typeof console !== "undefined") console.warn("analytics/log error:", e);
    return false;
  }
}

export default logAnalytics;

