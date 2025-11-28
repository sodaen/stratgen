import fs from 'fs';

const CANDS = ['App.tsx','src/App.tsx','Pipeline.tsx','src/Pipeline.tsx'];

function patchApp(code){
  let out = code;

  // a) Session-Customer nach save() setzen + Projekt patchen
  out = out.replace(
    /setPid\(projectId\)\s*[\r\n]+\s*mark\('save',\{status:'ok'\}\)/,
    `setPid(projectId)
      // Session-spezifischer Customer für strikt isolierte Assets/Quellen
      const sessionCustomer = \`\${customer}__\${projectId.slice(-6)}\`
      try {
        await fetch(\`\${API_BASE}/projects/\${projectId}\`, {
          method:'PATCH', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ customer_name: sessionCustomer })
        })
      } catch {}
      mark('save',{status:'ok'})`
  );

  // b) Uploads auf sessionCustomer umstellen
  out = out.replace(
    /research\/upload\?customer_name=\$\{encodeURIComponent\(customer\)\}&embed=1/g,
    `research/upload?customer_name=\${encodeURIComponent(sessionCustomer)}&embed=1`
  );

  // c) enrich-Body: rag_strict -> rag-Objekt
  out = out.replace(
    /JSON\.stringify\(\{\s*length,\s*use_llm:\s*true,\s*rag_strict:\s*true\s*\}\)/g,
    `JSON.stringify({ length, use_llm: true, rag: { strict: true, max_hits: 5, section_queries: true } })`
  );

  // d) nach enrich zusätzlich generate aufrufen (robust, optional)
  out = out.replace(
    /mark\('enrich',\{status:'ok'\}\)/g,
    `mark('enrich',{status:'ok'})
      try {
        await fetch(\`\${API_BASE}/projects/\${projectId}/generate\`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ modules: [] })
        })
      } catch {}`
  );

  // e) Footnotes: korrektes Schema {slides,sources} statt {project_id}
  out = out.replace(
    /mark\('footnotes',\{status:'running'\}\)[\s\S]*?mark\('footnotes',\{status:'ok'\}\)/m,
    `mark('footnotes',{status:'running'})
      try {
        // Projekt laden → Slides aus slide_plan oder Outline ableiten
        const pj = await fetch(\`\${API_BASE}/projects/\${projectId}\`).then(r=>r.json()).catch(()=>null)
        const proj = pj?.project || pj || {}
        const sp = (proj?.meta?.slide_plan) || []
        const outline = proj?.outline || {}
        const slides = (Array.isArray(sp) && sp.length
           ? sp.map((s,i)=>({ id: s.id || String(i+1), text: s.title || s.kind || \`Slide \${i+1}\` }))
           : (outline.sections||[]).map((s,i)=>({ id: String(i+1), text: s.title || \`Slide \${i+1}\` })));

        // Quellen strikt auf Session scopen
        let sources = []
        try {
          const q = (outline.title || topic || '').toString().slice(0,120) || 'strategy'
          const qr = await fetch(\`\${API_BASE}/datasources/query\`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ query: q, customer_name: (typeof sessionCustomer!=='undefined'?sessionCustomer:(customer+'__'+projectId.slice(-6))), limit: Math.min(5, slides.length) })
          })
          const data = await qr.json().catch(()=>({}))
          sources = (data?.items||[]).map((it,idx)=>({
            id: String(idx+1),
            title: it?.payload?.title || it?.payload?.file || 'Quelle',
            url: it?.payload?.url || ''
          }))
        } catch {}

        await fetch(\`\${API_BASE}/footnotes/attach\`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ slides, sources })
        })
        mark('footnotes',{status:'ok'})
      } catch (e) {
        // optionaler Schritt → nicht blockieren
        mark('footnotes',{status:'ok'})
      }`
  );

  return out;
}

function patchPipeline(code){
  let out = code;

  // generate nach enrich (falls nicht vorhanden)
  if (!/\/projects\/\$\{projectId\}\/generate/.test(out)) {
    out = out.replace(
      /mark\('enrich',\s*\{status:'ok'\}\)/,
      `mark('enrich',{status:'ok'})
       try {
         await postJson(\`\${API_BASE}/projects/\${projectId}/generate\`, { modules: [] })
       } catch {}`
    );
  }

  // Footnotes korrektes Schema
  out = out.replace(
    /mark\('footnotes',\s*\{status:'running'\}\)[\s\S]*?mark\('footnotes',\s*\{status:'ok',?\s*detail:?'?\(?(?:übersprungen)?\)?'?\}?\)\s*/m,
    `mark('footnotes',{status:'running'})
     try {
       const pj = await getJson(\`\${API_BASE}/projects/\${projectId}\`)
       const proj = pj?.project || pj || {}
       const sp = (proj?.meta?.slide_plan) || []
       const outline = proj?.outline || {}
       const slides = (Array.isArray(sp) && sp.length
          ? sp.map((s,i)=>({ id: s.id || String(i+1), text: s.title || s.kind || \`Slide \${i+1}\` }))
          : (outline.sections||[]).map((s,i)=>({ id: String(i+1), text: s.title || \`Slide \${i+1}\` })));
       const sessionCustomer = \`\${customer}__\${projectId.slice(-6)}\`
       let sources = []
       try{
         const q = (outline.title || topic || '').toString().slice(0,120) || 'strategy'
         const data = await postJson(\`\${API_BASE}/datasources/query\`, { query: q, customer_name: sessionCustomer, limit: Math.min(5, slides.length) })
         sources = (data?.items||[]).map((it,idx)=>({ id:String(idx+1), title: it?.payload?.title || it?.payload?.file || 'Quelle', url: it?.payload?.url || '' }))
       }catch{}
       await postJson(\`\${API_BASE}/footnotes/attach\`, { slides, sources })
       mark('footnotes',{status:'ok'})
     } catch {
       mark('footnotes',{status:'ok'})
     }`
  );

  return out;
}

for (const p of CANDS) {
  if (!fs.existsSync(p)) continue;
  const src = fs.readFileSync(p,'utf8');
  let out = src;
  if (/export default function App/.test(src)) out = patchApp(src);
  if (/export default function Pipeline/.test(src)) out = patchPipeline(out);
  if (out !== src) {
    fs.writeFileSync(p, out, 'utf8');
    console.log('✔ Patched', p);
  } else {
    console.log('• No changes for', p);
  }
}
