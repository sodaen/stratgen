const API_BASE = (import.meta.env.VITE_API_BASE || "http://127.0.0.1:8011").replace(/\/$/, "");

async function j<T=any>(path: string, opt: RequestInit = {}): Promise<T> {
  const res = await fetch(API_BASE + path, {
    method: "GET",
    ...opt,
    headers: { "Content-Type": "application/json", ...(opt.headers||{}) },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  health:      () => j("/health"),
  knowledge:   (q: string, k=6, dedup=true) =>
                  j("/knowledge/search_semantic_v2", { method: "POST", body: JSON.stringify({ q, k, dedup }) }),
  previewV2:   (topic: string, k=6) =>
                  j("/content/preview_with_sources_v2", { method: "POST", body: JSON.stringify({ topic, k }) }),
  agentGenerateV2: (body: any) =>
                  j("/agent/generate_v2", { method: "POST", body: JSON.stringify(body) }),
  exportMakeV2: (body: any) =>
                  j("/exports/make_v2", { method: "POST", body: JSON.stringify(body) }),
};

export async function downloadApi(path: string, filename = "export.pptx") {
  const url = API_BASE + path;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed: HTTP ${res.status}`);
  const blob = await res.blob();
  const a = document.createElement("a");
  const href = URL.createObjectURL(blob);
  a.href = href;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}

export { API_BASE };
