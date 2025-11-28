// lightweight analytics helper (same-origin)
(function () {
  function sid() {
    try {
      let s = sessionStorage.getItem("sid");
      if (!s) {
        s = "sid-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        sessionStorage.setItem("sid", s);
      }
      return s;
    } catch(e) { return null; }
  }

  async function logAnalytics(event, meta={}, projectId=null, userId=null) {
    try {
      await fetch("/analytics/log", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          event,
          meta,
          project_id: projectId,
          user_id: userId,
          session_id: sid()
        })
      });
    } catch (e) {
      // bewusst still — Analytics soll die UX nie blockieren
      console.debug("analytics/log failed", e);
    }
  }

  // Auto page_view beim Laden
  try {
    logAnalytics("page_view", { route: location.pathname });
  } catch(e){}

  // global verfügbar machen
  window.logAnalytics = logAnalytics;
})();
