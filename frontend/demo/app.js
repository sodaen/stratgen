function getSessionId() {
  try {
    let s = sessionStorage.getItem("sid");
    if (!s) {
      s = "sid-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem("sid", s);
    }
    return s;
  } catch { return null; }
}

function apiBase() {
  try {
    const o = location.origin;
    if (o.includes(":5173") || o.includes(":5174")) return "http://127.0.0.1:8001";
  } catch {}
  return ""; // same-origin
}

async function logAnalytics(event, meta={}, {projectId=null, userId=null, baseUrl} = {}) {
  const body = {
    event,
    meta,
    type: "analytics",
    session_id: getSessionId(),
    project_id: projectId,
    user_id: userId
  };
  const base = baseUrl || apiBase();
  try {
    const res = await fetch(base + "/analytics/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body)
    });
    const ok = res.ok;
    const txt = await res.text();
    console.log("POST /analytics/log ->", res.status, txt);
    return ok;
  } catch (e) {
    console.warn("analytics/log error:", e);
    return false;
  }
}

// page_view on load
logAnalytics("page_view", { route: location.pathname }, { projectId: "demo123" });

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn");
  btn?.addEventListener("click", () => {
    logAnalytics("preview_clicked", { btn: "demo" }, { userId: "u1" });
  });
});
