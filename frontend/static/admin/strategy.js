const API_BASE = location.origin.replace(/\/$/, "");
const API_KEY = localStorage.getItem("STRATGEN_API_KEY") || "";

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (API_KEY) {
    headers["x-api-key"] = API_KEY;
  }
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }
  const res = await fetch(API_BASE + path, {
    ...options,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error("API error " + res.status + ": " + text);
  }
  return res.json();
}

const listEl = document.getElementById("strategy-list");
const detailEl = document.getElementById("strategy-detail");
const searchEl = document.getElementById("search");
const filterStatusEl = document.getElementById("filter-status");
const refreshBtn = document.getElementById("btn-refresh");

let currentName = null;
let currentData = null;

async function loadList() {
  const resp = await api("/strategy/list");
  let items = resp.items || [];
  const q = searchEl.value.trim().toLowerCase();
  const fs = filterStatusEl.value;
  if (q) {
    items = items.filter((it) => (it.title || "").toLowerCase().includes(q));
  }
  if (fs) {
    items = items.filter((it) => it.status === fs);
  }
  renderList(items);
}

function renderList(items) {
  listEl.innerHTML = "";
  items.forEach((it) => {
    const div = document.createElement("div");
    div.className = "item" + (it.name === currentName ? " active" : "");
    div.innerHTML = `
      <div><strong>${it.title || it.name}</strong></div>
      <div class="muted">${it.status || "–"} · ${it.mission_id ?? ""}</div>
    `;
    div.addEventListener("click", () => {
      loadDetail(it.name);
    });
    listEl.appendChild(div);
  });
}

async function loadDetail(name) {
  const resp = await api(`/strategy/${name}`);
  currentName = name;
  currentData = resp.data;
  renderDetail(resp.data);
  // liste neu, damit active sichtbar
  await loadList();
}

function renderDetail(data) {
  detailEl.innerHTML = "";
  const wrap = document.createElement("div");
  wrap.innerHTML = `
    <div class="row">
      <div>
        <label>Titel</label>
        <input id="f-title" value="${data.title || ""}" />
      </div>
      <div>
        <label>Status</label>
        <select id="f-status">
          <option value="">–</option>
          <option value="generated">generated</option>
          <option value="approved">approved</option>
          <option value="delivered">delivered</option>
        </select>
      </div>
    </div>
    <div class="row">
      <div>
        <label>Audience</label>
        <input id="f-audience" value="${data.audience || ""}" />
      </div>
      <div>
        <label>Sprache</label>
        <input id="f-lang" value="${data.lang || ""}" />
      </div>
    </div>
    <div class="row">
      <div>
        <label>Size</label>
        <input id="f-size" value="${data.size || ""}" />
      </div>
      <div>
        <label>Mission ID</label>
        <input value="${data.mission_id || ""}" disabled />
      </div>
    </div>
    <div>
      <label>Briefing</label>
      <textarea id="f-briefing">${data.briefing || ""}</textarea>
    </div>
    <div>
      <label>Verknüpfte Contents (JSON Array)</label>
      <textarea id="f-used-contents">${JSON.stringify(data.used_contents || [], null, 2)}</textarea>
    </div>
    <div class="actions">
      <button id="btn-save">Speichern</button>
      <a class="secondary" href="${API_BASE}/strategy/${data.name}.pptx" target="_blank">
        <button class="secondary" type="button">PPTX laden</button>
      </a>
    </div>
    <p class="muted">Name: ${data.name}</p>
  `;
  detailEl.appendChild(wrap);

  // status setzen
  const fStatus = document.getElementById("f-status");
  if (data.status) {
    fStatus.value = data.status;
  }

  document.getElementById("btn-save").addEventListener("click", async () => {
    let used = [];
    const rawUsed = document.getElementById("f-used-contents").value.trim();
    if (rawUsed) {
      try {
        used = JSON.parse(rawUsed);
      } catch (e) {
        alert("used_contents ist kein gültiges JSON");
        return;
      }
    }
    const payload = {
      title: document.getElementById("f-title").value,
      audience: document.getElementById("f-audience").value,
      lang: document.getElementById("f-lang").value,
      size: document.getElementById("f-size").value,
      status: document.getElementById("f-status").value,
      used_contents: used,
    };
    try {
      await api(`/strategy/${currentName}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      await loadDetail(currentName);
    } catch (err) {
      alert(err.message);
    }
  });
}

searchEl.addEventListener("input", () => loadList());
filterStatusEl.addEventListener("change", () => loadList());
refreshBtn.addEventListener("click", () => loadList());

loadList();
