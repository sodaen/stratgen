#!/usr/bin/env bash
set -u
set -o pipefail
DB="data/manifest.db"
python3 - <<'PY' "$DB"
import sqlite3, sys, os, time
db=sys.argv[1]
os.makedirs(os.path.dirname(db), exist_ok=True)
con=sqlite3.connect(db)
cur=con.cursor()
cur.executescript("""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  customer TEXT,
  path TEXT NOT NULL,
  name TEXT,
  type TEXT,
  size INTEGER,
  hash TEXT,
  tags TEXT,          -- JSON array
  section_hint TEXT,
  topic_hint TEXT,
  source TEXT,
  created_at REAL
);
CREATE TABLE IF NOT EXISTS facts (
  id TEXT PRIMARY KEY,
  asset_id TEXT,
  metric TEXT,
  value REAL,
  unit TEXT,
  period_start TEXT,
  period_end TEXT,
  citation TEXT,
  FOREIGN KEY(asset_id) REFERENCES assets(id)
);
CREATE INDEX IF NOT EXISTS idx_assets_customer ON assets(customer);
CREATE INDEX IF NOT EXISTS idx_assets_tags ON assets(tags);
CREATE INDEX IF NOT EXISTS idx_facts_metric ON facts(metric);
""")
con.commit(); con.close()
print("ok")
PY
