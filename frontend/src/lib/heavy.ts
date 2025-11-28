// minimal fetch helper
async function post(path: string, body?: any) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) throw new Error(`POST ${path} -> ${res.status}`);
  try { return await res.json(); } catch { return null; }
}

const DEFAULT_MODULES = [
  "gtm_basics","personas","market_sizing","competitive","value_proof",
  "channel_mix","funnel","kpis","execution_roadmap","risks_mitigations",
  "guardrails","go_no_go"
];

export type HeavyOpts = {
  topic?: string;
  org?: string;
  slides?: number;
  k?: number;
  modules?: string[];
  project_id?: string;
};

export async function generateOnly(opts: HeavyOpts) {
  const topic   = opts.topic   ?? "Untitled";
  const org     = opts.org     ?? "Global";
  const slides  = opts.slides  ?? 50;
  const modules = opts.modules ?? DEFAULT_MODULES;

  let pid = opts.project_id;
  if (!pid) {
    const saved = await post("/projects/save", { customer_name: org, topic });
    pid = saved?.project?.id;
  }
  await post(`/projects/${pid}/generate`, { modules, slides });
  return { ok: true, project_id: pid, slides, modules };
}

export async function finishAndRender(opts: HeavyOpts) {
  const topic   = opts.topic   ?? "Untitled";
  const org     = opts.org     ?? "Global";
  const slides  = opts.slides  ?? 50;
  const modules = opts.modules ?? DEFAULT_MODULES;
  const k       = opts.k       ?? 12;

  let pid = opts.project_id;
  if (!pid) {
    // wenn kein Projekt existiert: voll durchlaufen
    const saved = await post("/projects/save", { customer_name: org, topic });
    pid = saved?.project?.id;
    await post(`/projects/${pid}/generate`, { modules, slides });
  }

  // Optionales Warmup (fehler egal)
  try { await post("/knowledge/search_semantic_v2", { query: topic, k }); } catch {}

  // Heavy Steps
  await post(`/projects/${pid}/enrich`,   { length: "long", use_llm: true });
  await post(`/projects/${pid}/critique`, {});
  try { await post(`/projects/${pid}/autotune`, {}); await post(`/projects/${pid}/autotune`, {}); } catch {}

  const out = await post(`/pptx/render_from_project/${pid}`, {});
  const path = out?.path || out?.file || "";
  const url  = out?.url  || (path ? ("/exports/download/" + path.split("/").pop()) : null);
  return { ok: true, project_id: pid, slides, path, url, name: path?.split("/").pop() };
}
