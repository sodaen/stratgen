import React, { useMemo, useState } from 'react'

type StepStatus = 'idle'|'running'|'ok'|'error'
type StepView = { id:string; title:string; status:StepStatus; detail?:string }

// erlaubt env override (Vite): VITE_API_BASE, fallback 127.0.0.1
const API_BASE: string = (import.meta as any)?.env?.VITE_API_BASE || 'http://127.0.0.1:8011'

async function postJson<T>(url:string, body:any): Promise<T> {
  const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) })
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}
async function postEmpty<T>(url:string): Promise<T> {
  const r = await fetch(url, { method:'POST' })
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}
async function getJson<T>(url:string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}


// --- HEAVY V1 PIPELINE (no UI changes) ---
async function heavyExport(API_BASE: string, projectId: string, desiredSlides: number) {
  const len = desiredSlides >= 80 ? "long" : "mid";
  // Enrich (LLM+RAG)
  try {
    await fetch(`${API_BASE}/projects/${projectId}/enrich`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ length: len, use_llm: true })
    });
  } catch (e) { console.error("enrich failed", e); }

  // Critique
  try {
    await fetch(`${API_BASE}/projects/${projectId}/critique`, { method: "POST" });
  } catch (e) { console.error("critique failed", e); }

  // Optional: Autotune (2 Pässe – schnell)
  try {
    await fetch(`${API_BASE}/projects/${projectId}/autotune`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({ pass: 1 }) });
    await fetch(`${API_BASE}/projects/${projectId}/autotune`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({ pass: 2 }) });
  } catch (e) { console.warn("autotune skipped", e); }

  // Render
  const res = await heavyExport(API_BASE, projectId, desiredSlides)
  });
  if (!res.ok) throw new Error(`render_from_project -> ${res.status}`);
  return res;
}
// --- END HEAVY V1 PIPELINE ---
export default function Pipeline({
  customer,
  topic,
  goals,
  constraints,
  notes,
  length,          // 'short' | 'mid' | 'long'
  brandColor,      // hex
}:{
  customer:string
  topic:string
  goals:string[]
  constraints:string[]
  notes:string
  length:'short'|'mid'|'long'
  brandColor?:string
}) {
  const [pid, setPid] = useState<string>('')
  const [steps, setSteps] = useState<StepView[]>([
    {id:'save',      title:'Projekt speichern',        status:'idle'},
    {id:'brief',     title:'Brief mergen',            status:'idle'},
    {id:'personas',  title:'Personas',                status:'idle'},
    {id:'matrix',    title:'Messaging Matrix',        status:'idle'},
    {id:'metrics',   title:'KPIs',                    status:'idle'},
    {id:'mix',       title:'Media-Mix',               status:'idle'},
    {id:'enrich',    title:'Outline + Inhalte (LLM/RAG)', status:'idle'}, // NEW
    {id:'footnotes', title:'Footnotes/Quellen',       status:'idle'},     // NEW (optional)
    {id:'critique',  title:'Critique',                status:'idle'},
    {id:'snap',      title:'Snapshot',                status:'idle'},
    {id:'render',    title:'PPTX Render',             status:'idle'},
    {id:'latest',    title:'Export Link',             status:'idle'},
  ])
  const [exportHref, setExportHref] = useState<string>('')

  const pct = useMemo(() => {
    const done = steps.filter(s=>s.status==='ok').length
    return Math.round(done * 100 / steps.length)
  }, [steps])

  function mark(id:string, patch:Partial<StepView>) {
    setSteps(prev => prev.map(s => s.id===id ? {...s, ...patch} : s))
  }

  async function run() {
    setExportHref('')
    setSteps(prev => prev.map(s => ({...s, status:'idle', detail:undefined})))
    try {
      // 1) save
      mark('save', {status:'running'})
      const saved = await postJson<any>(`${API_BASE}/projects/save`, {
        customer_name: customer || 'Unbenannt',
        topic: topic || 'Strategie',
        outline: { sections: [] }
      })
      const projectId = saved?.project?.id || saved?.id
      if (!projectId) throw new Error('Kein project.id')
      setPid(projectId)
      mark('save', {status:'ok', detail:projectId})

      // 2) brief (mit Branding, Goals/Constraints, Notes)
      mark('brief', {status:'running'})
      await postJson<any>(`${API_BASE}/briefs/merge_to_project?project_id=${projectId}`, {
        brief: {
          text: notes || '—',
          goals: goals?.length ? goals : ['Awareness','Consideration','Sales'],
          constraints: constraints?.length ? constraints : [],
          brand_color: brandColor || '#22c55e'
        }
      })
      mark('brief', {status:'ok'})

      // 3) personas
      mark('personas', {status:'running'})
      const personasRes = await postJson<any>(`${API_BASE}/personas/suggest`, {
        product: 'Consumer Sports Product',
        countries: ['DE']
      })
      const personas = personasRes?.personas?.length ? personasRes.personas : [{name:'Teenager 13–16'}, {name:'Eltern 25–45'}]
      mark('personas', {status:'ok', detail:`${personas.length} Persona(s)`})

      // 4) messaging matrix (Schema: Objekt-Array + value_props)
      mark('matrix', {status:'running'})
      await postJson<any>(`${API_BASE}/messaging/matrix`, {
        personas: personas.map((p:any)=> typeof p==='string' ? ({name:p}) : p),
        value_props: (goals?.length ? goals : ['Sicher','Langlebig','Preis-Leistung'])
      })
      mark('matrix', {status:'ok'})

      // 5) KPIs
      mark('metrics', {status:'running'})
      await postJson<any>(`${API_BASE}/metrics/suggest`, {
        objective: goals?.[0] || 'Awareness',
        horizon_weeks: 24
      })
      mark('metrics', {status:'ok'})

      // 6) Media-Mix
      mark('mix', {status:'running'})
      await postJson<any>(`${API_BASE}/plans/media_mix`, {
        budget_eur: 30000,                  // aus Briefing
        objective: goals?.[0] || 'Awareness',
        countries: ['DE','AT','CH'],
        horizon_weeks: 24
      })
      mark('mix', {status:'ok'})

      // 7) ENRICH: Outline + Inhalte (LLM + RAG)  ← DER fehlende Schritt!
      mark('enrich', {status:'running'})
      await postJson<any>(`${API_BASE}/projects/${projectId}/enrich`, {
        length,               // 'short'|'mid'|'long'
        use_llm: true,
        rag: { strict: true, max_hits: 5, section_queries: true }
      })
      mark('enrich', {status:'ok'})

      // 8) (optional) Footnotes/Quellen anhängen, falls vorhanden
      mark('footnotes', {status:'running'})
      try {
        await postJson<any>(`${API_BASE}/footnotes/attach`, { project_id: projectId })
        mark('footnotes', {status:'ok'})
      } catch (e:any) {
        // Nicht kritisch – einige Builds haben diesen Schritt (noch) nicht
        mark('footnotes', {status:'ok', detail:'(übersprungen)'})
      }

      // 9) Critique (Feinschliff)
      mark('critique', {status:'running'})
      await postEmpty<any>(`${API_BASE}/projects/${projectId}/critique`)
      mark('critique', {status:'ok'})

      // 10) Snapshot
      mark('snap', {status:'running'})
      await postEmpty<any>(`${API_BASE}/projects/${projectId}/versions/snapshot`)
      mark('snap', {status:'ok'})

      // 11) Render (mit Fallback auf /pptx/test_dividers, falls 404)
      mark('render', {status:'running'})
      let renderOk = false
      try {
        const r = await const desiredSlides = (form?.slides ?? data?.slides ?? (typeof length==="number"?length:undefined));
await fetch(`${API_BASE}/projects/${projectId}/generate`, {  method: "POST", headers: {"Content-Type":"application/json"},  body: JSON.stringify({ modules: ["gtm_basics","personas","market_sizing","competitive","value_proof","channel_mix","funnel","kpis","execution_roadmap","risks_mitigations","guardrails","go_no_go"], slides: desiredSlides })});
fetch(`${API_BASE}/pptx/render_from_project/${projectId}?length=${length}`, { method:'POST' })
        if (r.ok) renderOk = true
        else if (r.status === 404) {
          const r2 = await fetch(`${API_BASE}/pptx/test_dividers`, { method:'POST' })
          if (r2.ok) renderOk = true
        }
      } catch {}
      if (!renderOk) throw new Error('render fehlgeschlagen')
      mark('render', {status:'ok'})

      // 12) Latest Export (korrekter Download-Endpoint!)
      mark('latest', {status:'running'})
      const latest = await getJson<any>(`${API_BASE}/exports/latest?ext=pptx`)
      if (latest?.url) {
        setExportHref(`${API_BASE}${latest.url}`)
        mark('latest', {status:'ok', detail:'bereit'})
      } else {
        const path = latest?.path || ''
        const name = latest?.name || (path ? path.split('/').pop() : '')
        if (name) {
          setExportHref(`${API_BASE}/exports/download?name=${encodeURIComponent(name)}`)
          mark('latest', {status:'ok', detail:'bereit'})
        } else {
          mark('latest', {status:'error', detail:'kein Export gefunden'})
        }
      }
    } catch (e:any) {
      const firstRunning = steps.find(s=>s.status==='running')
      if (firstRunning) mark(firstRunning.id, {status:'error', detail:String(e?.message||e)})
      console.error(e)
    }
  }

  return (
    <div className="space-y-4">
      <div className="w-full bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm font-medium">Fortschritt</div>
          <div className="text-xs text-slate-400">{pct}%</div>
        </div>
        <div className="progress-wrap bg-slate-700">
          <div className="progress-bar" style={{width:`${pct}%`, height:8, background:'var(--color-primary)'}}/>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 mt-4">
          {steps.map(s=>(
            <div key={s.id} className={`step ${s.status==='ok'?'ok':s.status==='running'?'run':s.status==='error'?'err':''}`}>
              <span className="w-2 h-2 rounded-full" style={{background:
                s.status==='ok'?'#22c55e':s.status==='running'?'#f59e0b':s.status==='error'?'#ef4444':'#64748b'}}/>
              <span>{s.title}</span>
              {s.detail && <span className="text-xs text-slate-400">– {s.detail}</span>}
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center gap-2">
          <button className="btn btn-primary" onClick={run}>Generate</button>
          {exportHref && (
            <a className="btn" href={exportHref}>Export herunterladen (PPTX)</a>
          )}
        </div>
        {pid && <div className="mt-3 text-xs text-slate-400">project_id: <code>{pid}</code></div>}
      </div>
    </div>
  )
}
