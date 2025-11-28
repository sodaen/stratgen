#!/usr/bin/env bash
set -u
set -o pipefail
echo "==> init schema"
scripts/manifest_init.sh >/dev/null
echo "==> scan"
python3 scripts/manifest_scan.py
echo "==> peek (assets 5):"
python3 - <<'PY'
import json
with open("data/manifest.json","r",encoding="utf-8") as f:
    j=json.load(f)
print(len(j.get("assets",[])))
for a in j.get("assets",[])[:5]:
    print(a["name"], a.get("section_hint"), a.get("tags"))
PY
echo "==> facts metrics sample:"
python3 - <<'PY'
import sqlite3
con=sqlite3.connect("data/manifest.db")
for row in con.execute("SELECT metric, COUNT(*) FROM facts GROUP BY metric ORDER BY COUNT(*) DESC LIMIT 5"):
    print(row)
con.close()
PY
