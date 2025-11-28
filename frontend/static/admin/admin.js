function getApiKey(){
  try { return document.getElementById('apiKey')?.value?.trim() || 'dev'; }
  catch(e){ return 'dev'; }
}

(function(){
  const state = { q:"", sort:"created_desc", page:1, page_size:20, pages:1 };
  const $q = byId("q"), $sort = byId("sort"), $size = byId("page_size"), $apply = byId("apply");
  const $new = byId("newproj");
  const $rows = byId("rows"), $pp = byId("pp"), $prev = byId("prev"), $next = byId("next"), $apikey = byId("apikey");

  if (window.StratgenAnalytics) StratgenAnalytics.log("page_view", { route: "/admin/" });

  function byId(id){ return document.getElementById(id); }
  function esc(s){ return String(s ?? "").replace(/[&<>"']/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function qs(){
    const p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    p.set("sort", state.sort);
    p.set("page", String(state.page));
    p.set("page_size", String(state.page_size));
    return p.toString();
  }
  async function load(){
    const res = await fetch(`/projects/list?${qs()}`);
    if (!res.ok){ $rows.innerHTML = `<tr><td colspan="6">Error ${res.status}</td></tr>`; return; }
    const data = await res.json();
    state.pages = data.pages || 1; state.page = data.page || 1;
    $pp.textContent = `Seite ${state.page} / ${state.pages}`;
    renderRows(data.items || []);
  }
  function renderRows(items){
    $rows.innerHTML = items.map(it=>{
      const id = it.id || "";
      const title = it.title || "";
      const cust = it.customer_name || "";
      const topic = it.topic || "";
      const created = it.created_at || "";
      const updated = it.updated_at || "";
      return `<tr>
        <td>${esc(title)}</td>
        <td>${esc(cust)}</td>
        <td>${esc(topic)}</td>
        <td>${esc(created)}</td>
        <td>${esc(updated)}</td>
        <td>
          <button data-act="preview" data-id="${esc(id)}">Preview</button>
          <button data-act="export"  data-id="${esc(id)}">Export</button>
          <button data-act="duplicate" data-id="${esc(id)}">Duplicate</button>
          <button data-act="delete"  data-id="${esc(id)}">Delete</button>
        </td>
      </tr>`;
    }).join("");
  }

  $apply.addEventListener("click", ()=>{ state.q=$q.value.trim(); state.sort=$sort.value; state.page_size=parseInt($size.value,10)||20; state.page=1; load();

  // Neu anlegen
  if ($new) $new.addEventListener("click", async ()=>{
    const key = $apikey.value.trim();
    const hdr = key ? { "X-API-Key": key, "Content-Type":"application/json" } : { "Content-Type":"application/json" };
    const title = prompt("Titel für neues Projekt?", "New Project");
    if (title===null) return;
    const body = { customer_name: "Demo", topic: title || "New", outline: { title: title || "New", sections: [] } };
    const res = await fetch("/projects/save", { method: "POST", headers: hdr, body: JSON.stringify(body) });
    if (!res.ok) { alert("Save "+res.status); return; }
    load();
  }); });
  $prev.addEventListener("click", ()=>{ if(state.page>1){ state.page--; load();

  // Neu anlegen
  if ($new) $new.addEventListener("click", async ()=>{
    const key = $apikey.value.trim();
    const hdr = key ? { "X-API-Key": key, "Content-Type":"application/json" } : { "Content-Type":"application/json" };
    const title = prompt("Titel für neues Projekt?", "New Project");
    if (title===null) return;
    const body = { customer_name: "Demo", topic: title || "New", outline: { title: title || "New", sections: [] } };
    const res = await fetch("/projects/save", { method: "POST", headers: hdr, body: JSON.stringify(body) });
    if (!res.ok) { alert("Save "+res.status); return; }
    load();
  }); }});
  $next.addEventListener("click", ()=>{ if(state.page<state.pages){ state.page++; load();

  // Neu anlegen
  if ($new) $new.addEventListener("click", async ()=>{
    const key = $apikey.value.trim();
    const hdr = key ? { "X-API-Key": key, "Content-Type":"application/json" } : { "Content-Type":"application/json" };
    const title = prompt("Titel für neues Projekt?", "New Project");
    if (title===null) return;
    const body = { customer_name: "Demo", topic: title || "New", outline: { title: title || "New", sections: [] } };
    const res = await fetch("/projects/save", { method: "POST", headers: hdr, body: JSON.stringify(body) });
    if (!res.ok) { alert("Save "+res.status); return; }
    load();
  }); }});

  $rows.addEventListener("click", async (e)=>{
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const act = btn.getAttribute("data-act");
    const id  = btn.getAttribute("data-id");
    const key = $apikey.value.trim();
    const hdr = key ? { "X-API-Key": key, "Content-Type":"application/json" } : { "Content-Type":"application/json" };

    try {
      if (act==="preview"){
        const res = await apiFetch(`/projects/${id}/preview`, { method:"POST", headers: hdr, body: JSON.stringify({ style:"brand", width:800, height:450 }) });
        if (!res.ok) throw new Error(`Preview ${res.status}`);
        if (window.StratgenAnalytics) StratgenAnalytics.log("preview_clicked", { src:"admin", id });
        // Bild als Blob öffnen
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank");
      }
      if (act==="export"){
        const res = await apiFetch(`/projects/${id}/export`, { method:"POST", headers: hdr, body: JSON.stringify({ style:"brand", filename:"export.pptx" }) });
        if (!res.ok) throw new Error(`Export ${res.status}`);
        if (window.StratgenAnalytics) StratgenAnalytics.log("export_clicked", { src:"admin", id });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = `project_${id}.pptx`; a.click();
        URL.revokeObjectURL(url);
      }
      if (act==="duplicate"){
        const res = await apiFetch(`/projects/${id}/duplicate`, { method: "POST", headers: hdr, body: JSON.stringify({ title: `${Date.now()} copy` }) });
        if (!res.ok) throw new Error(`Duplicate ${res.status}`);
        if (window.StratgenAnalytics) StratgenAnalytics.log("duplicate_clicked", { src:"admin", id });
        load();
      }
      if (act==="delete"){
        if (!confirm("Projekt wirklich löschen?")) return;
        const res = await apiFetch(`/projects/${id}`, { method:"DELETE", headers: hdr });
        if (!res.ok) throw new Error(`Delete ${res.status}`);
        if (window.StratgenAnalytics) StratgenAnalytics.log("delete_clicked", { src:"admin", id });
        load();

  // Neu anlegen
  if ($new) $new.addEventListener("click", async ()=>{
    const key = $apikey.value.trim();
    const hdr = key ? { "X-API-Key": key, "Content-Type":"application/json" } : { "Content-Type":"application/json" };
    const title = prompt("Titel für neues Projekt?", "New Project");
    if (title===null) return;
    const body = { customer_name: "Demo", topic: title || "New", outline: { title: title || "New", sections: [] } };
    const res = await fetch("/projects/save", { method: "POST", headers: hdr, body: JSON.stringify(body) });
    if (!res.ok) { alert("Save "+res.status); return; }
    load();
  });
      }
    } catch(err){
      alert(err.message || String(err));
      console.error(err);
    }
  });

  // init
  state.sort = $sort.value;
  state.page_size = parseInt($size.value,10) || 20;
  load();

  // Neu anlegen
  if ($new) $new.addEventListener("click", async ()=>{
    const key = $apikey.value.trim();
    const hdr = key ? { "X-API-Key": key, "Content-Type":"application/json" } : { "Content-Type":"application/json" };
    const title = prompt("Titel für neues Projekt?", "New Project");
    if (title===null) return;
    const body = { customer_name: "Demo", topic: title || "New", outline: { title: title || "New", sections: [] } };
    const res = await fetch("/projects/save", { method: "POST", headers: hdr, body: JSON.stringify(body) });
    if (!res.ok) { alert("Save "+res.status); return; }
    load();
  });
})();


  function makeEditableCell(td, project, key){
    td.contentEditable = "true";
    td.dataset.key = key;
    td.addEventListener('keydown', async (ev) => {
      if (ev.key === 'Enter') { ev.preventDefault(); td.blur(); }
    });
    td.addEventListener('blur', async () => {
      const newVal = td.textContent.trim();
      if (newVal === (project[key] || '')) return;
      // PATCH senden
      try {
        const res = await apiFetch(`/projects/${project.id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': getApiKey()
          },
          body: JSON.stringify({ [key]: newVal })
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        // UI aktualisieren (lokal + evtl. Outline-Title)
        project[key] = newVal;
      } catch(e){
        console.error("PATCH failed", e);
        // revert
        td.textContent = project[key] || '';
        alert('Speichern fehlgeschlagen');
      }
    });
  }


  // Hook: Nach dem Zeichnen jeder Zeile aufrufen:
  async function enhanceRowInlineEdit(tr, project){
    // Wir erwarten Zellen in Reihenfolge: Title | Topic | Customer | ... (je nach deiner Tabelle)
    const tds = Array.from(tr.querySelectorAll('td'));
    // Anpassung: passe Indizes an deine Spalten an, falls abweichend:
    const tdTitle = tds[0];       // Titel-Spalte
    const tdTopic = tds[1];       // Topic-Spalte
    const tdCustomer = tds[2];    // Customer-Spalte

    if (tdTitle)   makeEditableCell(tdTitle,   project, 'title');
    if (tdTopic)   makeEditableCell(tdTopic,   project, 'topic');
    if (tdCustomer)makeEditableCell(tdCustomer,project, 'customer_name');
  }

  async function apiFetch(url, opts){
    opts = opts || {};
    opts.headers = Object.assign({
      'Content-Type':'application/json',
      'X-API-Key': getApiKey()
    }, opts.headers||{});
    return fetch(url, opts);
  }
