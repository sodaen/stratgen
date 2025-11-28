# -*- coding: utf-8 -*-
import sqlite3, time, json

con=sqlite3.connect("data/manifest.db"); cur=con.cursor()
# hole stats
stats={k:(r,l,dw,dl) for k,r,l,dl,dw in cur.execute("SELECT kind,renders,likes,dislikes,downloads FROM slide_stats")}
# Feedback-Tabelle (falls aus 3b vorhanden) ergänzend nutzen
fb = {k:(lk,dk) for k,lk,dk in cur.execute("""
  SELECT kind, SUM(CASE WHEN liked=1 THEN 1 ELSE 0 END), SUM(CASE WHEN liked=0 THEN 1 ELSE 0 END)
  FROM slide_feedback GROUP BY kind
""")} if list(cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='slide_feedback'")) else {}

updated=[]
for kind,(renders,likes,dislikes,downloads) in stats.items():
  lk = likes + (fb.get(kind,(0,0))[0] if fb else 0)
  dl = dislikes + (fb.get(kind,(0,0))[1] if fb else 0)
  tot = max(1, lk+dl)
  like_ratio = lk / tot
  # simple Formel: Basis 1.0, +0.4*Likes, -0.2*Dislikes; Klammern 0.7..1.8
  w = 1.0 + 0.4*like_ratio - 0.2*(dl/tot)
  if w < 0.7: w=0.7
  if w > 1.8: w=1.8
  cur.execute("INSERT INTO slide_pref(kind,weight,updated_at) VALUES(?,?,?) ON CONFLICT(kind) DO UPDATE SET weight=?, updated_at=?",
              (kind,w,time.time(),w,time.time()))
  updated.append((kind,round(w,3)))
con.commit(); con.close()
print(json.dumps({"ok":True,"updated":updated}, ensure_ascii=False))
