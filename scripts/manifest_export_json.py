# -*- coding: utf-8 -*-
import sqlite3, json
from pathlib import Path
DB=Path("data/manifest.db"); OUT=Path("data/manifest.json")
if not DB.exists(): 
    print("[ERR] manifest.db fehlt"); raise SystemExit(1)
con=sqlite3.connect(DB); cur=con.cursor()
def tbl(name):
    try:
        rows=cur.execute(f"SELECT * FROM {name}").fetchall()
        cols=[c[1] for c in cur.execute(f"PRAGMA table_info({name})")]
        return [dict(zip(cols,r)) for r in rows]
    except Exception:
        return []
res = {t: tbl(t) for t in ("assets","facts","charts","chart_insights")}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
con.close()
print(f"[ok] manifest.json aktualisiert: {OUT}")
