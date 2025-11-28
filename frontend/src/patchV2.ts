/**
 * patchV2.ts
 * - Killt /agent/generate_v2 & /content/preview_with_sources_v2 clientseitig.
 * - Lässt /knowledge/search_semantic_v2 zu (gut für RAG).
 * - Export läuft über /exports/make_v2 -> wurde im Backend auf Heavy verdrahtet.
 */
(function(){
  const w = window as any;
  if ((w.__STRATGEN_FORCE_HEAVY ?? false) === true) return;
  w.__STRATGEN_FORCE_HEAVY = true;

  const origFetch = (window.fetch ? window.fetch.bind(window) : null);
  if (!origFetch) return;

  const block = (url: string) =>
    url.includes("/agent/generate_v2") ||
    url.includes("/content/preview_with_sources_v2");

  const stub = (url: string) => {
    // Minimal-JSON das die UI zufriedenstellt (Preview wird ohnehin übersprungen)
    const body = JSON.stringify({ ok: true, skipped: true, note: "Heavy mode: preview_v2 disabled" });
    return new Response(body, { status: 200, headers: { "Content-Type": "application/json" }});
  };

  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    try {
      const url = (typeof input === "string") ? input : (input as URL).toString();
      if (block(url)) return Promise.resolve(stub(url));
    } catch {}
    return origFetch!(input as any, init);
  };
})();
