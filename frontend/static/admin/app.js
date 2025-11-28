(function(){
  const API = ""; // same-origin
  const KEY = "dev"; // Demo-API-Key

  const q = document.getElementById("q");
  const sort = document.getElementById("sort");
  const pagesize = document.getElementById("pagesize");
  const reloadBtn = document.getElementById("reload");
  const rows = document.getElementById("rows");
  const prev = document.getElementById("prev");
  const next = document.getElementById("next");
  const pageinfo = document.getElementById("pageinfo");

  let state = { page: 1, pages: 1, page_size: 20, q: "", sort: "created_desc" };

  function fmt(ts){ if(!ts) return ""; try{ const d = new Date(ts*1000||ts); return d.toISOString().slice(0,19).replace('T',' ');}catch(e){return String(ts)} }

  async function load(){
    const params = new URLSearchParams({
      page: String(state.page),
      page_size: String(state.page_size),
      sort: state.sort
    });
    if (state.q) params.set("q", state.q);

    const resp = await fetch(`${API}/projects/list?`+params.toString(), { credentials:"omit" });
    const data = await resp.json();

    state.page = data.page; state.pages = data.pages; state.page_size = data.page_size;
    render(data.items || []);
    pageinfo.textContent = `Seite ${state.page} von ${state.pages} (total ${data.total})`;

    // Analytics
    if (window.StratgenAnalytics) {
      StratgenAnalytics.log("admin_list_loaded", { q: state.q, sort: state.sort, page: state.page, page_size: state.page_size });
    }
  }

  function render(items){
    rows.innerHTML = "";
    for (const it of items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(it.title || "")}</td>
        <td>${escapeHtml(it.customer_name || "")}</td>
        <td>${escapeHtml(it.topic || "")}</td>
        <td>${escapeHtml(fmt(it.created_at))}</td>
        <td>${escapeHtml(fmt(it.updated_at))}</td>
        <td class="actions">
          <button data-act="preview" data-id="${it.id}">Preview</button>
          <button data-act="export"  data-id="${it.id}">Export</button>
        </td>
      `;
      rows.appendChild(tr);
    }
  }

  function escapeHtml(s){ return (s??"").toString().replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])) }

  rows.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("button[data-act]");
    if (!btn) return;
    const id = btn.getAttribute("data-id");
    const act = btn.getAttribute("data-act");

    if (act === "preview") {
      // ruft PNG ab und logged
      const r = await fetch(`${API}/projects/${id}/preview`, {
        method: "POST",
        headers: { "Content-Type":"application/json", "X-API-Key": KEY },
        body: JSON.stringify({ style:"brand", width:800, height:450 })
      });
      if (r.ok) {
        if (window.StratgenAnalytics) StratgenAnalytics.log("admin_preview_clicked", { id });
        alert("Preview OK (siehe Netzwerkkonsole)");
      } else {
        alert("Preview fehlgeschlagen: " + r.status);
      }
    }

    if (act === "export") {
      const r = await fetch(`${API}/projects/${id}/export`, {
        method: "POST",
        headers: { "Content-Type":"application/json", "X-API-Key": KEY },
        body: JSON.stringify({ style:"brand", filename:"export.pptx" })
      });
      if (r.ok) {
        if (window.StratgenAnalytics) StratgenAnalytics.log("admin_export_clicked", { id });
        // Als Blob speichern
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "export.pptx"; a.click();
        URL.revokeObjectURL(url);
      } else {
        alert("Export fehlgeschlagen: " + r.status);
      }
    }
  });

  reloadBtn.addEventListener("click", () => { state.page = 1; state.q = q.value.trim(); state.sort = sort.value; state.page_size = parseInt(pagesize.value,10)||20; load(); });
  prev.addEventListener("click", () => { if (state.page>1){ state.page--; load(); }});
  next.addEventListener("click", () => { if (state.page<state.pages){ state.page++; load(); }});

  // Initial
  load();
})();
