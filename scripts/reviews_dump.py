import sqlite3
from datetime import datetime, timezone

con = sqlite3.connect("data/projects.sqlite")
cur = con.cursor()
cur.execute("SELECT id, project_id, ts, json FROM reviews ORDER BY id DESC LIMIT 20")
rows = cur.fetchall()
con.close()

print(f"{'id':>6}  {'project_id':<18}  {'ts_utc':<20}  json_snippet")
print("-" * 90)
for r in rows:
    ts_iso = datetime.fromtimestamp(r[2], tz=timezone.utc).isoformat()
    jsnip = (r[3][:80] + "…") if len(r[3]) > 80 else r[3]
    print(f"{r[0]:>6}  {r[1]:<18}  {ts_iso:<20}  {jsnip}")
