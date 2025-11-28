import React from "react";
import { api, downloadApi } from "./lib/api";
import { PipelineProgress, Step } from "./components/PipelineProgress";
import UploadDrop from "./components/UploadDrop";
import "./styles.css";
import './lib/patchV1';

// --- STRATGEN_FORCE_V1_BEGIN ---
// idempotent shim: v2-Frontend-Calls lokal auf v1-Backend routen (ohne UI-Änderung)
async function __post(path: string, body: any) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}
const __V1_MODULES = ["gtm_basics","personas","market_sizing","competitive","value_proof","channel_mix","funnel","kpis","execution_roadmap","risks_mitigations","guardrails","go_no_go"];

// weiche Überschreibungen, falls im importierten api-Objekt vorhanden
try {
  // @ts-ignore
  const _api: any = (typeof api!=="undefined") ? (api as any) : null;
  if (_api && !_api.__force_v1) {
    _api.__force_v1 = true;

    // previewV2: stub, damit UI-Optik erhalten bleibt
    if (typeof _api.previewV2 === "function") {
      _api.previewV2 = async (topic: string, k: any) => ({
        outline: { title: topic }, citations: [], diagnostics: { citations_count: 0 }
      });
    }

    // agentGenerateV2 -> v1 /projects/save + /projects/{id}/generate
    if (typeof _api.agentGenerateV2 === "function") {
      _api.agentGenerateV2 = async (opts: any) => {
        const topic = opts?.topic || "Untitled";
        const slides = Math.max(5, Math.min(Number(opts?.slides || 30) || 30, 200));
        const org = opts?.org || "Global";
        const saved = await __post("/projects/save", { customer_name: org, topic });
        const pid = saved?.project?.id;
        if (!pid) throw new Error("no project.id from /projects/save");
        const gen = await __post(`/projects/${pid}/generate`, { modules: __V1_MODULES, slides });
        return { project: gen?.project, text: "ok" };
      };
    }

    // exportMakeV2 -> v1 /pptx/render_from_project/{id}
    if (typeof _api.exportMakeV2 === "function") {
      _api.exportMakeV2 = async (opts: any) => {
        const topic = opts?.topic || "Untitled";
        const org = opts?.org || "Global";
        const slides = Math.max(5, Math.min(Number(opts?.slides || 30) || 30, 200));
        let pid = opts?.project?.id;
        if (!pid) {
          const saved = await __post("/projects/save", { customer_name: org, topic });
          pid = saved?.project?.id;
        }
        if (!pid) throw new Error("no project.id available");
        const exp = await __post(`/pptx/render_from_project/${pid}`, {
          slides, brand_theme: opts?.brand_theme, briefing: opts?.briefing, lang: opts?.lang, k: opts?.k
        });
        const name = (exp?.path || "export.pptx").split("/").pop();
        return { name, url: exp?.url, path: exp?.path, citations_count: 0 };
      };
    }
  }
} catch { /* noop */ }
// --- STRATGEN_FORCE_V1_END ---


type StepState = "pending" | "running" | "done" | "error";
type DeckTier = "short" | "mid" | "long";
const DEFAULT_PREFER = "ollama:mistral|ollama:llama3:8b|heuristic";

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "";

export default function App() {
  // Form-States
  const [topic, setTopic] = React.useState("go to market plan 2026");
  const [org, setOrg] = React.useState("Customized Whatever");
  const [project, setProject] = React.useState("Stratgen");
  const [briefing, setBriefing] = React.useState("Bitte CI nutzen.");
  const [lang, setLang] = React.useState<"de" | "en">("de");
  const [k, setK] = React.useState(6);
  const [deck, setDeck] = React.useState<DeckTier>("short"); // "short"≈15, "mid"≈50, "long"≈100+
  const [brand, setBrand] = React.useState({ primary: "#0A84FF", secondary: "#111111", accent: "#FF2D55" });

  // Pipeline
  const initSteps: Step[] = [
    { label: "Knowledge", state: "pending" },
    { label: "Preview", state: "pending" },
    { label: "Generate (LLM)", state: "pending" },
    { label: "Export PPTX", state: "pending" },
    { label: "Download bereit", state: "pending" },
  ];
  const [steps, setSteps] = React.useState<Step[]>(initSteps);
  const upd = (i: number, patch: Partial<Step>) =>
    setSteps((s) => s.map((x, idx) => (idx === i ? { ...x, ...patch } : x)));

  const [result, setResult] = React.useState<any>(null);
  const [downloadInfo, setDownloadInfo] = React.useState<{ path: string; name: string } | null>(null);
  const [running, setRunning] = React.useState(false);
  const [showDetails, setShowDetails] = React.useState(false);

  function deckSlides(tier: DeckTier) {
    if (tier === "short") return 15;
    if (tier === "mid") return 50;
    return 100;
  }

  async function runPipeline() {
    if (running) return;
    setRunning(true);
    setDownloadInfo(null);
    setSteps([
      { label: "Knowledge", state: "running" },
      { label: "Preview", state: "pending" },
      { label: "Generate (LLM)", state: "pending" },
      { label: "Export PPTX", state: "pending" },
      { label: "Download bereit", state: "pending" },
    ]);

    // Deck-Länge freundlich ins Briefing übernehmen (bis Backend eigenes Feld parst)
    const desiredSlides = deckSlides(deck);
    const briefingWithLen =
      `${briefing}\n\nDeck-Länge: ca. ${desiredSlides} Folien.`.trim();

    try {
      // 1) Knowledge (RAG)
      const know = await api.knowledge(topic, k, true);
      upd(0, { state: "done", detail: JSON.stringify(know.results.slice(0, 6), null, 2) });

      // 2) Preview
      upd(1, { state: "running" });
      const prev = await api.previewV2(topic, k);
      const cc = prev?.diagnostics?.citations_count ?? (prev?.citations?.length ?? 0);
      upd(1, { state: "done", detail: JSON.stringify({ citations_count: cc, outline: prev?.outline?.title }, null, 2) });

      // 3) Generate (LLM) – OLLAMA/Mistral/OpenAI bevorzugt in genau dieser Reihenfolge
      upd(2, { state: "running" });
      const gen = await api.agentGenerateV2({
        topic,
        k,
        use_knowledge: true,
        prefer: DEFAULT_PREFER,
        // Schiebe die gewünschte Länge auch hier in den Prompt-Kontext
        prompt: `Erzeuge Inhalte für ein Deck mit ca. ${desiredSlides} Folien. Beziehe dich auf die recherchierten Zitate/Quellen.`,
      });
      upd(2, { state: "done", detail: (gen.text || "").slice(0, 500) });

      // 4) Export PPTX
      upd(3, { state: "running" });
      const exp = await api.exportMakeV2({
        topic, org, project, briefing: briefingWithLen, lang, k,
        brand_theme: brand,
        prefer: DEFAULT_PREFER,
        // zukunftssicher – falls Backend später 'slides' versteht:
        slides: desiredSlides,
      });
      setResult({ know, prev, gen, exp });
      upd(3, { state: "done", detail: JSON.stringify({ name: exp.name, citations: exp.citations_count }, null, 2) });

      // 5) Download
      setDownloadInfo({ path: `${API_BASE}${exp.url}`, name: exp.name });
      upd(4, { state: "done", detail: exp.url });
    } catch (e: any) {
      const msg = e?.message || String(e);
      const idx = steps.findIndex((s) => s.state === "running");
      if (idx >= 0) upd(idx, { state: "error", detail: msg });
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="container">
      <header className="header">
        <img src="/stratgen-logo.svg" alt="Stratgen" />
        <h1>STRATEGY DECK BUILDER</h1>
      </header>

      <div className="stack">
        <section className="card">
          <h3 style={{ marginTop: 0 }}>Projekt</h3>
          <div className="row">
            <div>
              <label>Firma (org)</label>
              <input value={org} onChange={(e) => setOrg(e.target.value)} placeholder="Organisation" />
            </div>
            <div>
              <label>Projekt</label>
              <input value={project} onChange={(e) => setProject(e.target.value)} placeholder="Projekt" />
            </div>
          </div>

          <div className="row">
            <div>
              <label>Sprache</label>
              <select value={lang} onChange={(e) => setLang(e.target.value as any)}>
                <option value="de">Deutsch</option>
                <option value="en">English</option>
              </select>
            </div>

            <div>
              <label>Deck-Länge</label>
              <select value={deck} onChange={(e) => setDeck(e.target.value as DeckTier)}>
                <option value="short">Kurz · ca. 15</option>
                <option value="mid">Mittel · ca. 50</option>
                <option value="long">Lang · 100+</option>
              </select>
              <div className="help">Legt die Zielgröße des PPTX fest. Unabhängig von k.</div>
            </div>
          </div>

          <div className="krow">
            <div style={{ flex: 1 }}>
              <label>K (Quellen-Anzahl für Retrieval/RAG)</label>
              <input
                type="range"
                min={1}
                max={12}
                value={k}
                onChange={(e) => setK(Number(e.target.value))}
              />
              <div className="help">
                K = wie viele Top-Dokumente inhaltlich herangezogen werden (RAG).
                Niedriger: fokussierter/schneller. Höher: breiter/robuster.
                Empfehlung: 6–8.
              </div>
            </div>
            <span className="badge">k={k}</span>
          </div>

          <div className="grid-full">
            <label>Briefing</label>
            <textarea value={briefing} onChange={(e) => setBriefing(e.target.value)} placeholder="kurzes Briefing" />
          </div>
          <div className="grid-full">
            <label>Topic</label>
            <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="z. B. go to market plan 2026" />
          </div>

          <div className="grid-full">
            <label>CI-Farben</label>
            <div className="row">
              <div><label>Primary</label><input type="color" value={brand.primary} onChange={(e) => setBrand({ ...brand, primary: e.target.value })} /></div>
              <div><label>Secondary</label><input type="color" value={brand.secondary} onChange={(e) => setBrand({ ...brand, secondary: e.target.value })} /></div>
              <div><label>Accent</label><input type="color" value={brand.accent} onChange={(e) => setBrand({ ...brand, accent: e.target.value })} /></div>
            </div>
          </div>

          <div className="actions" style={{ marginTop: 12 }}>
            <button className={`btn primary ${running ? "loading" : ""}`} onClick={runPipeline} disabled={running}>
              🚀 Generieren
            </button>
            <button
              className="btn"
              disabled={!downloadInfo || running}
              onClick={() => downloadInfo && downloadApi(downloadInfo.path, downloadInfo.name)}
              title={downloadInfo ? downloadInfo.name : "Noch kein Export vorhanden"}
            >
              ⬇️ Download PPTX
            </button>
          </div>
        </section>

        {/* Upload-Sektion */}
        <UploadDrop
          tags="knowledge"
          org={org}
          project={project}
          onUploaded={() => { /* optional: nach Upload /knowledge/scan triggern */ }}
        />

        <section className="card">
          <PipelineProgress steps={steps} />
        </section>

        <section className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>Details</h3>
            <button className="btn" onClick={() => setShowDetails((v) => !v)}>{showDetails ? "verbergen" : "anzeigen"}</button>
          </div>
          {showDetails ? <pre className="detail">{JSON.stringify(result, null, 2)}</pre> : null}
        </section>
      </div>
    </div>
  );
}
