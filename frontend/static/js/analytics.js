(function(global){
  function sid() {
    try {
      var s = sessionStorage.getItem("sid");
      if (!s) {
        s = "sid-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        sessionStorage.setItem("sid", s);
      }
      return s;
    } catch(e){ return null; }
  }

  function apiBase(){
    try {
      var o = location.origin || "";
      if (o.includes(":5173") || o.includes(":5174")) return "http://127.0.0.1:8001";
    } catch(e){}
    return ""; // same-origin
  }

  async function log(event, meta, opts){
    meta = meta || {};
    opts = opts || {};
    var body = {
      event: event,
      meta: meta,
      project_id: opts.projectId || null,
      user_id: opts.userId || null,
      session_id: sid()
    };
    try {
      var res = await fetch(apiBase() + "/analytics/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        mode: "cors",
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        console.warn("analytics/log failed:", res.status, await res.text());
      }
      return res.ok;
    } catch(e){
      console.warn("analytics/log error:", e);
      return false;
    }
  }

  global.StratgenAnalytics = { log: log };
})(window);
