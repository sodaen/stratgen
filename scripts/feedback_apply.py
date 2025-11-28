# -*- coding: utf-8 -*-
import json, sqlite3, time, sys
from pathlib import Path

DB = Path("data/manifest.db")
FEED = Path(sys.argv[1] if len(sys.argv)>1 else "data/feedback.json")
DB.parent.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(DB); cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS slide_feedback(
  id INTEGER PRIMARY KEY,
  kind TEXT, title TEXT, liked INTEGER,
  ts REAL, customer TEXT, session TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS slide_pref(
  kind TEXT PRIMARY KEY, weight REAL NOT NULL, updated_at REAL
)""")

# defensiv: fehlende Spalten aus 3a/2b ergänzen (no-op wenn vorhanden)
for t,c in (("facts","provider TEXT"),
            ("facts","brand TEXT"),
            ("facts","region TEXT"),
            ("facts","channel TEXT")):
    try: cur.execute(f"ALTER TABLE {t} ADD COLUMN {c}")
    except sqlite3.OperationalError: pass

now = time.time()
items = []
try:
    items = json.loads(FEED.read_text(encoding="utf-8"))
except Exception:
    items = []

ins = 0
for it in items:
    kind  = str(it.get("kind","")).strip() or "-"
    title = str(it.get("title","")).strip() or "-"
    liked = 1 if bool(it.get("liked",False)) else 0
    cur.execute("INSERT INTO slide_feedback(kind,title,liked,ts,customer,session) VALUES(?,?,?,?,?,?)",
                (kind,title,liked,now,None,None))
    ins += 1

# Gewichte pro kind: 1.0 + 0.6 * (likes - dislikes)/max(1,n), clamp [0.5, 1.6]
rows = cur.execute("""
  SELECT kind,
         SUM(CASE WHEN liked=1 THEN 1 ELSE 0 END) AS likes,
         SUM(CASE WHEN liked=0 THEN 1 ELSE 0 END) AS dislikes,
         COUNT(*) AS n
  FROM slide_feedback
  GROUP BY kind
""").fetchall()

def clamp(x,a,b): return a if x<a else b if x>b else x
for kind, likes, dislikes, n in rows:
    score = (likes - dislikes) / float(max(1,n))
    weight = clamp(1.0 + 0.6*score, 0.5, 1.6)
    cur.execute("INSERT INTO slide_pref(kind,weight,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(kind) DO UPDATE SET weight=excluded.weight, updated_at=excluded.updated_at",
                (kind, weight, now))

con.commit(); con.close()
print(json.dumps({"ok": True, "inserted_feedback": ins, "kinds_scored": len(rows)}, ensure_ascii=False))
