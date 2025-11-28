# -*- coding: utf-8 -*-
import sqlite3, time, os, json
db="data/manifest.db"
os.makedirs("data", exist_ok=True)
con=sqlite3.connect(db); cur=con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS telemetry_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  kind TEXT,
  source TEXT,
  event TEXT,   -- render, download, like, dislike
  ok INTEGER,   -- 1/0
  extra TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS slide_stats (
  kind TEXT PRIMARY KEY,
  renders INTEGER DEFAULT 0,
  downloads INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  dislikes INTEGER DEFAULT 0
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS slide_pref (
  kind TEXT PRIMARY KEY,
  weight REAL DEFAULT 1.0,
  updated_at REAL
)""")
con.commit(); con.close()
print(json.dumps({"ok":True,"note":"telemetry schema ready"}))
