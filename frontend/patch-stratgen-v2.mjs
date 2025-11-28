import fs from 'fs';

const CANDS = ['src/App.tsx','App.tsx','src/Pipeline.tsx','Pipeline.tsx'];

function exists(p){ try{ fs.accessSync(p); return true; } catch { return false; } }
function read(p){ return fs.readFileSync(p,'utf8'); }
function write(p,s){ fs.writeFileSync(p,s,'utf8'); console.log('✔ Patched', p); }

for (const p of CANDS.filter(exists)) {
  let s = read(p);

  // A) sessionCustomer direkt nach setPid(projectId) einfügen + Projekt auf Session-Kunden patchen
  {
    const pat = /setPid\(projectId\)\s*;?/;
    if (pat.test(s) && !/sessionCustomer\s*=/.test(s)) {
      const ins = String.raw`setPid(projectId);
      // Session-spezifischer Kunde für Upload-/Asset-Isolation
      const sessionCustomer = \`${'${customer}'}__\${projectId.slice(-6)}\`;
      try {
        fetch(\`${'${API_BASE}'}/projects/\${projectId}\`, {
          method: 'PATCH',
          headers: {'Content-Type':'application/json', ...(apiKey?{'X-API-Key':apiKey}:{})},
          body: JSON.stringify({ customer_name: sessionCustomer })
        });
      } catch {}
      `;
      s = s.replace(pat, ins);
    }
  }

  // B) Upload-Endpunkte auf sessionCustomer umstellen
  s = s.replace(/customer_name=\${\s*customer\s*}/g, 'customer_name=${sessionCustomer}');
  s = s.replace(/customer=\${\s*customer\s*}/g, 'customer=${sessionCustomer}');

  // C) Nach ENRICH den GENERATE-Call einfügen (nur wenn noch nicht vorhanden)
  if (!/\/projects\/\$\{projectId\}\/generate/.test(s)) {
    const enrichPat = /await\s+fetch\(\s*`\$\{API_BASE\}\/projects\/\$\{projectId\}\/enrich[^;]*;\s*/;
    if (enrichPat.test(s)) {
      const ins = String.raw`
await fetch(\`${'${API_BASE}'}/projects/\${projectId}/generate\`, {
  method: 'POST',
  headers: {'Content-Type':'application/json', ...(apiKey?{'X-API-Key':apiKey}:{})},
  body: JSON.stringify({ modules: [] })
}).then(r=>r.json()).then(j=>{
  if (typeof mark==='function') mark('generate',{status: j.ok?'ok':'fail', meta:j.meta||{}});
}).catch(e=>{ if (typeof mark==='function') mark('generate',{status:'fail', error:String(e)}) });
`;
      s = s.replace(enrichPat, m => m + ins);
    }
  }

  // D) footnotes/attach: richtigen Body senden (Minimal-Slides + leere Quellen)
  {
    const fnPat = /fetch\(\s*`\$\{API_BASE\}\/footnotes\/attach`[\s\S]*?\)\s*;/;
    if (fnPat.test(s)) {
      const rep = String.raw`
fetch(\`${'${API_BASE}'}/footnotes/attach\`, {
  method: 'POST',
  headers: {'Content-Type':'application/json', ...(apiKey?{'X-API-Key':apiKey}:{})},
  body: JSON.stringify({
    slides: [{ id: '1', text: String(topic || 'Slide 1') }],
    sources: []  // optional auffüllen, aber Schema-konform
  })
}).then(r=>r.json()).then(j=>{
  if (typeof mark==='function') mark('footnotes',{status: j.ok?'ok':'fail'});
}).catch(e=>{
  if (typeof mark==='function') mark('footnotes',{status:'fail', error:String(e)});
});
`;
      s = s.replace(fnPat, rep);
    }
  }

  // E) Fallback-Divider mit Session-Kunde parametrieren
  s = s.replace(/`(\$\{API_BASE\}\/pptx\/test_dividers)(`)`/g, '`$1?customer=${sessionCustomer}`');

  write(p, s);
}
