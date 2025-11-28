import sqlite3, json

con = sqlite3.connect("data/projects.sqlite")
cur = con.cursor()
cur.execute("SELECT id, project_id, ts, json FROM reviews ORDER BY id DESC LIMIT 20")
rows = [{"id": r[0], "project_id": r[1], "ts": r[2], "review": json.loads(r[3])} for r in cur.fetchall()]
con.close()

print(json.dumps({"ok": True, "items": rows}, ensure_ascii=False, indent=2))
