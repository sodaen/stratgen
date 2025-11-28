import os, json, sqlite3, time
from datetime import datetime, timezone

DB = os.path.join("data","projects.sqlite")
con = sqlite3.connect(DB)
cur = con.cursor()

def fetch_one(sql):
    cur.execute(sql)
    row = cur.fetchone()
    return row[0] if row else 0

count_decks = fetch_one("SELECT COUNT(1) FROM decks")
count_slides = fetch_one("SELECT COUNT(1) FROM deck_slides")

# Top kinds (nur wenn Spalte existiert)
cur.execute("PRAGMA table_info(deck_slides)")
cols = [r[1] for r in cur.fetchall()]
top_kinds = []
if "kind" in cols:
    cur.execute("""SELECT COALESCE(kind,''), COUNT(1) c
                   FROM deck_slides GROUP BY COALESCE(kind,'')
                   ORDER BY c DESC LIMIT 10""")
    top_kinds = [{"kind": k, "count": c} for k, c in cur.fetchall()]

# Neueste Decks (wenn ts existiert)
latest = []
cur.execute("PRAGMA table_info(decks)")
dcols = [r[1] for r in cur.fetchall()]
if "ts" in dcols:
    cur.execute("SELECT id, ts, source FROM decks ORDER BY ts DESC LIMIT 5")
    for i, ts, src in cur.fetchall():
        latest.append({"id": i, "ts": ts, "ts_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(), "source": src})

con.close()
print(json.dumps({"ok": True, "counts": {"decks": count_decks, "slides": count_slides},
                  "top_kinds": top_kinds, "latest_decks": latest}, ensure_ascii=False, indent=2))
