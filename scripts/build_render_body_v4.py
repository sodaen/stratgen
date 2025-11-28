# -*- coding: utf-8 -*-
import sys, json, time, sqlite3
from pathlib import Path

DB = Path("data/manifest.db")
def load_json(p):
  try: return json.loads(Path(p).read_text(encoding="utf-8"))
  except Exception: return {}

comp = load_json("assets_tmp/comp_wave3c.json")
style = load_json("assets_tmp/style_choice.json")
rag   = load_json("assets_tmp/rag_bullets.json")
man   = load_json("data/manifest.json")

title = comp.get("title") or "Strategy Deck"
plan  = list(comp.get("plan") or [])

# Data Highlights aus charts.alt_text
high = []
for ch in (man.get("charts") or [])[:5]:
  alt = ch.get("alt_text")
  if alt: high.append(alt)
if not high: high = rag.get("bullets") or []

# Data Highlights Block anlegen/ersetzen
dh = None
for blk in plan:
  if blk.get("kind")=="insights" and (blk.get("title") or "").lower().startswith("data"):
    dh = blk; break
if dh is None:
  dh = {"kind":"insights","layout_hint":"Title and Content","title":"Data Highlights","bullets":[]}
  plan.append(dh)
dh["bullets"] = high[:5]

# Zusätzlicher RAG-Bullets-Block (separat)
plan.append({
  "kind":"insights","layout_hint":"Title and Content",
  "title":"RAG Highlights","bullets": (rag.get("bullets") or [])[:5]
})

# Präferenz-Sortierung aus 3b (slide_pref)
prefs = {}
try:
  con = sqlite3.connect(DB); cur = con.cursor()
  for k,w,_ in cur.execute("SELECT kind,weight,updated_at FROM slide_pref"):
    prefs[k]=float(w)
  con.close()
except Exception:
  pass

def w(blk): return float(prefs.get(blk.get("kind","-"), 1.0))
plan_sorted = sorted(plan, key=w, reverse=True)

out = {
  "title": title,
  "out_path": f"data/exports/deck-{time.strftime('%Y%m%d-%H%M%S')}.pptx",
  "plan": plan_sorted,
  "styles": style.get("profile") or {},
  "brand": style.get("brand"),
  "industry": style.get("industry")
}
Path("assets_tmp/render_body_v4.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"ok": True, "style_id": (style.get('profile') or {}).get('id','default_minimal'),
                  "blocks": len(plan_sorted)}, ensure_ascii=False))
