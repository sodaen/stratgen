import fs from 'fs';

const CANDS = ['src/Pipeline.tsx','Pipeline.tsx'];

function patch(code){
  let s = code;

  // A) sessionCustomer + Projekt-PATCH direkt nach setPid(projectId)
  if (!/sessionCustomer\s*=/.test(s)) {
    s = s.replace(/setPid\(projectId\)\s*;?/,
`setPid(projectId);
      // Session-Kunde für Upload/Asset-Isolation
      const sessionCustomer = \`\${customer}__\${projectId.slice(-6)}\`;
      try {
        await fetch(\`\${API_BASE}/projects/\${projectId}\`, {
          method:'PATCH', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ customer_name: sessionCustomer })
        })
      } catch {}
`);
  }

  // B) GENERATE nach ENRICH einfügen (falls noch nicht vorhanden)
  if (!/\/projects\/\$\{projectId\}\/generate/.test(s)) {
    s = s.replace(
      /mark\('enrich',\s*\{status:'ok'\}\)/,
`mark('enrich',{status:'ok'})
      try {
        await postJson(\`\${API_BASE}/projects/\${projectId}/generate\`, { modules: [] })
      } catch {}`);    
  }

  // C) Footnotes-Block ersetzen: {slides,sources} statt {project_id}
  s = s.replace(
/mark\('footnotes',\s*\{status:'running'\}\)[\s\S]*?mark\('footnotes',\s*\{status:'ok'(?:,[^}]*)?\}\);?/m,
`mark('footnotes',{status:'running'})
      try {
        // Projekt laden → Slides aus slide_plan oder Outline
        const pj = await getJson<any>(\`\${API_BASE}/projects/\${projectId}\`);
        const proj = pj?.project || pj || {};
        const sp = Array.isArray(proj?.meta?.slide_plan) ? proj.meta.slide_plan : [];
        const outline = proj?.outline || {};
        const slides = (sp.length
          ? sp.map((s:any,i:number)=>({ id: s.id || String(i+1), text: s.title || s.kind || \`Slide \${i+1}\` }))
          : (outline.sections||[]).map((s:any,i:number)=>({ id: String(i+1), text: s.title || \`Slide \${i+1}\` })));

        // Quellen auf Session scopen
        let sources:any[] = [];
        try {
          const q = (outline.title || topic || '').toString().slice(0,120) || 'strategy';
          const data = await postJson<any>(\`\${API_BASE}/datasources/query\`, {
            query: q, customer_name: (typeof sessionCustomer!=='undefined' ? sessionCustomer : (customer+'__'+projectId.slice(-6))),
            limit: Math.min(5, slides.length||5)
          });
          sources = (data?.items||[]).map((it:any,idx:number)=>({
            id: String(idx+1),
            title: it?.payload?.title || it?.payload?.file || 'Quelle',
            url: it?.payload?.url || ''
          }));
        } catch {}

        await postJson<any>(\`\${API_BASE}/footnotes/attach\`, { slides, sources });
        mark('footnotes',{status:'ok'})
      } catch (e:any) {
        mark('footnotes',{status:'ok'})
      };`
  );

  return s;
}

for (const p of CANDS) {
  if (!fs.existsSync(p)) continue;
  const before = fs.readFileSync(p,'utf8');
  const after = patch(before);
  if (after !== before) {
    fs.writeFileSync(p, after, 'utf8');
    console.log('✔ Patched', p);
  } else {
    console.log('• No changes for', p);
  }
}
