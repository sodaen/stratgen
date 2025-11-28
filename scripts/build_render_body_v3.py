# -*- coding: utf-8 -*-
import sys, json, sqlite3, time
from pathlib import Path

DB   = Path("data/manifest.db")
MANJ = Path("data/manifest.json")

raw = sys.stdin.read()
comp = json.loads(raw or "{}")
title = comp.get("title") or "Strategy Deck"
plan  = list(comp.get("plan") or [])

# slide_pref laden
prefs = {}
try:
    con = sqlite3.connect(DB); cur = con.cursor()
    for k,w,_ in cur.execute("SELECT kind, weight, updated_at FROM slide_pref"):
        prefs[k] = float(w)
    con.close()
except Exception:
    pass

# Data Highlights aus charts.alt_text (falls vorhanden)
highlights = []
try:
    man = json.loads(MANJ.read_text(encoding="utf-8"))
    for ch in man.get("charts", [])[:5]:
        alt = ch.get("alt_text")
        if alt:
            highlights.append(alt)
except Exception:
    pass

# Falls es bereits einen "Data Highlights" Block gibt, updaten; sonst anhängen
dh_block = None
for blk in plan:
    if blk.get("kind")=="insights" and (blk.get("title") or "").lower().startswith("data"):
        dh_block = blk; break
if dh_block is None:
    dh_block = {"kind":"insights","layout_hint":"Title and Content","title":"Data Highlights","bullets":[]}
    plan.append(dh_block)
dh_block["bullets"] = (highlights or dh_block.get("bullets") or [])[:5]

# Stabil sortieren: höhere Gewichte nach vorn; default 1.0
def w(blk): return float(prefs.get(blk.get("kind","-"), 1.0))
plan_sorted = sorted(plan, key=w, reverse=True)

out = {
  "title": title,
  "out_path": f"data/exports/deck-{time.strftime('%Y%m%d-%H%M%S')}.pptx",
  "plan": plan_sorted
}
print(json.dumps(out, ensure_ascii=False, indent=2))
