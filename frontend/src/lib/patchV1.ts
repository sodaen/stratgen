import { generateOnly, finishAndRender } from "./heavy";

declare global { interface Window { __STRATGEN_V1_WIRED?: boolean; } }

if (!window.__STRATGEN_V1_WIRED) {
  window.__STRATGEN_V1_WIRED = true;

  const origFetch = window.fetch.bind(window);

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = typeof input === "string" ? input : input.toString();

    // Wir wollen KEINE echten v2-Calls mehr absetzen:
    if (url.endsWith("/agent/generate_v2") || url.endsWith("/exports/make_v2")) {
      // Body lesen (falls vorhanden)
      let payload: any = {};
      if (init?.body && typeof init.body === "string") {
        try { payload = JSON.parse(init.body); } catch {}
      } else if (init?.body instanceof Blob) {
        const text = await (init.body as any).text?.();
        try { payload = JSON.parse(text); } catch {}
      }

      if (url.endsWith("/agent/generate_v2")) {
        const res = await generateOnly({
          topic: payload?.topic || payload?.title,
          org: payload?.org || payload?.customer_name,
          slides: Number(payload?.slides ?? 50),
          modules: payload?.modules,
          project_id: payload?.project_id
        });
        return new Response(JSON.stringify(res), { status: 200, headers: { "Content-Type": "application/json" } });
      }

      if (url.endsWith("/exports/make_v2")) {
        const res = await finishAndRender({
          topic: payload?.topic || payload?.title,
          org: payload?.org || payload?.customer_name,
          slides: Number(payload?.slides ?? 50),
          k: Number(payload?.k ?? 12),
          modules: payload?.modules,
          project_id: payload?.project_id
        });
        return new Response(JSON.stringify(res), { status: 200, headers: { "Content-Type": "application/json" } });
      }
    }

    // alle anderen Requests normal
    return origFetch(input as any, init);
  };
}
