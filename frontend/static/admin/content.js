const API_BASE = location.origin.replace(/\/$/, "");
const API_KEY = localStorage.getItem("STRATGEN_API_KEY") || "";

// kleiner API-Wrapper
async function api(path, options = {}) {
  const headers = options.headers || {};
  if (API_KEY) {
    headers["x-api-key"] = API_KEY;
  }
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(API_BASE + path, {
    credentials: "include",
    ...options,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return await res.json();
}

const els = {
  list: document.getElementById("items"),
  search: document.getElementById("search"),
  filterStatus: document.getElementById("filter-status"),
  newBtn: document.getElementById("new-content"),
  stats: document.getElementById("stats"),
  currentApi: document.getElementById("current-api"),
  // detail
  name: document.getElementById("name"),
  title: document.getElementById("title"),
  mission_id: document.getElementById("mission_id"),
  status: document.getElementById("status"),
  outline: document.getElementById("outline"),
  facts: document.getElementById("facts"),
  extra: document.getElementById("extra"),
  save: document.getElementById("save-btn"),
  publish: document.getElementById("publish-btn"),
  clone: document.getElementById("clone-btn"),
  del: document.getElementById("delete-btn"),
};

let currentName = null;

async function loadStats() {
  try {
    const data = await api("/content/stats");
    els.stats.innerHTML = "";
    const makeCard = (label, value) => {
      const div = document.createElement("div");
      div.className = "stat-card";
      div.textContent = `${label}: ${value}`;
      return div;
    };
    els.stats.appendChild(makeCard("Total", data.total));
    const by = data.by_status || {};
    for (const k of Object.keys(by)) {
      els.stats.appendChild(makeCard(k, by[k]));
    }
  } catch (err) {
    console.warn("stats failed", err);
  }
}

async function loadList() {
  const q = els.search.value.trim();
  const st = els.filterStatus.value;
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (st) params.set("status", st);
  const data = await api("/content/list" + (params.toString() ? "?" + params.toString() : ""));
  els.list.innerHTML = "";
  data.items.forEach((item) => {
    const div = document.createElement("div");
    div.className = "item" + (item.name === currentName ? " active" : "");
    div.dataset.name = item.name;
    div.innerHTML = `
      <strong>${item.title || "(ohne Titel)"}</strong>
      <small>${item.name}</small>
      <small>Status: ${item.status || "?"}</small>
    `;
    div.addEventListener("click", () => {
      showDetail(item.name);
    });
    els.list.appendChild(div);
  });
}

async function showDetail(name) {
  currentName = name;
  const data = await api("/content/" + name);
  // Liste re-highlighten
  Array.from(els.list.children).forEach((c) => {
    c.classList.toggle("active", c.dataset.name === name);
  });

  els.name.value = data.name;
  els.title.value = data.data.title || "";
  els.mission_id.value = data.data.mission_id != null ? data.data.mission_id : "";
  els.status.value = data.data.status || "";
  els.outline.value = data.data.outline ? JSON.stringify(data.data.outline, null, 2) : "";
  els.facts.value = data.data.facts ? JSON.stringify(data.data.facts, null, 2) : "";
  els.extra.value = data.data.extra ? JSON.stringify(data.data.extra, null, 2) : "";
}

async function saveCurrent() {
  if (!currentName) return;
  let outlineObj = null;
  let factsArr = null;
  let extraObj = null;
  if (els.outline.value.trim()) {
    try { outlineObj = JSON.parse(els.outline.value); } catch (e) { alert("Outline ist kein gültiges JSON"); return; }
  }
  if (els.facts.value.trim()) {
    try { factsArr = JSON.parse(els.facts.value); } catch (e) { alert("Facts ist kein gültiges JSON"); return; }
  }
  if (els.extra.value.trim()) {
    try { extraObj = JSON.parse(els.extra.value); } catch (e) { alert("Extra ist kein gültiges JSON"); return; }
  }
  const body = {
    title: els.title.value || null,
    mission_id: els.mission_id.value ? Number(els.mission_id.value) : null,
    outline: outlineObj,
    facts: factsArr,
    extra: extraObj,
  };
  const resp = await api("/content/" + currentName, {
    method: "PUT",
    body: JSON.stringify(body),
  });
  els.status.value = resp.data.status || "";
  await loadList();
  await loadStats();
}

async function publishCurrent() {
  if (!currentName) return;
  await api("/content/" + currentName + "/publish", { method: "POST" });
  await showDetail(currentName);
  await loadList();
  await loadStats();
}

async function cloneCurrent() {
  if (!currentName) return;
  const resp = await api("/content/" + currentName + "/clone", { method: "POST" });
  await loadList();
  await showDetail(resp.name);
  await loadStats();
}

async function deleteCurrent() {
  if (!currentName) return;
  if (!confirm("Wirklich löschen?")) return;
  await api("/content/" + currentName, { method: "DELETE" });
  currentName = null;
  els.name.value = "";
  els.title.value = "";
  els.mission_id.value = "";
  els.status.value = "";
  els.outline.value = "";
  els.facts.value = "";
  els.extra.value = "";
  await loadList();
  await loadStats();
}

async function newContent() {
  const resp = await api("/content/gen", {
    method: "POST",
    body: JSON.stringify({
      mission_id: 1,
      title: "Neuer Inhalt",
      outline: { sections: ["Intro"] },
      facts: [],
      status: "draft",
    }),
  });
  await loadList();
  await showDetail(resp.name);
  await loadStats();
}

window.addEventListener("DOMContentLoaded", async () => {
  els.currentApi.textContent = API_BASE + "/content";
  els.search.addEventListener("input", () => {
    loadList();
  });
  els.filterStatus.addEventListener("change", () => {
    loadList();
  });
  els.save.addEventListener("click", saveCurrent);
  els.publish.addEventListener("click", publishCurrent);
  els.clone.addEventListener("click", cloneCurrent);
  els.del.addEventListener("click", deleteCurrent);
  els.newBtn.addEventListener("click", newContent);

  await loadStats();
  await loadList();
});
