# -*- coding: utf-8 -*-
import json, time, sqlite3
from pathlib import Path

DB="data/manifest.db"
ev = []
now=time.time()

# Render-Plan: zähle jeden Block als 'render'
plan=[]
for pth in ["assets_tmp/render_body_v4.json","assets_tmp/render_body_v3.json","assets_tmp/comp_wave3c.json"]:
  try:
    obj=json.loads(Path(pth).read_text(encoding="utf-8"))
    if isinstance(obj,dict): plan=obj.get("plan") or plan
  except Exception: pass
for blk in (plan or []):
  k=blk.get("kind") or "-"
  ev.append((now,k,"render",1))

# Feedback-Datei (optional): likes/dislikes
try:
  fb=json.loads(Path("data/feedback.json").read_text(encoding="utf-8"))
  for it in fb:
    k=it.get("kind") or "-"
    ttl=it.get("title") or ""
    if it.get("liked") is True:  ev.append((now,k,"like",1))
    if it.get("liked") is False: ev.append((now,k,"dislike",1))
except Exception:
  pass

con=sqlite3.connect(DB); cur=con.cursor()

# schreibe events + aggregiere in slide_stats
for ts,kind,event,ok in ev:
  cur.execute("INSERT INTO telemetry_events(ts,kind,source,event,ok,extra) VALUES(?,?,?,?,?,?)",
              (ts,kind,"local",event,ok,None))
  if event=="render":
    cur.execute("INSERT INTO slide_stats(kind,renders) VALUES(?,1) ON CONFLICT(kind) DO UPDATE SET renders=renders+1", (kind,))
  elif event=="like":
    cur.execute("INSERT INTO slide_stats(kind,likes) VALUES(?,1) ON CONFLICT(kind) DO UPDATE SET likes=likes+1", (kind,))
  elif event=="dislike":
    cur.execute("INSERT INTO slide_stats(kind,dislikes) VALUES(?,1) ON CONFLICT(kind) DO UPDATE SET dislikes=dislikes+1", (kind,))
con.commit()

# kleine Zusammenfassung
rows=list(cur.execute("SELECT kind,renders,likes,dislikes,downloads FROM slide_stats ORDER BY kind"))
con.close()
print(json.dumps({"ok":True,"events":len(ev),"stats":rows}, ensure_ascii=False))
