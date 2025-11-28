from __future__ import annotations
import sqlite3, json, statistics
from datetime import datetime, timezone

con = sqlite3.connect("data/projects.sqlite")
cur = con.cursor()
cur.execute("SELECT id, project_id, ts, json FROM reviews ORDER BY id DESC LIMIT 500")
rows = cur.fetchall()
con.close()

items=[]
for id_, pid, ts, js in rows:
    try:
        j = json.loads(js)
    except Exception:
        j = {}
    items.append({
        "id": id_,
        "project_id": pid,
        "ts": ts,
        "ts_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        "score": j.get("score"),
        "issues": j.get("issues", []),
        "suggestions": j.get("suggestions", []),
    })

scores = [x["score"] for x in items if isinstance(x.get("score"), (int,float))]
summary = {
    "ok": True,
    "count": len(items),
    "scores": {
        "n": len(scores),
        "mean": round(statistics.mean(scores),2) if scores else None,
        "median": round(statistics.median(scores),2) if scores else None,
        "p25": round(statistics.quantiles(scores, n=4)[0],2) if len(scores)>=4 else None,
        "p75": round(statistics.quantiles(scores, n=4)[-1],2) if len(scores)>=4 else None,
        "min": min(scores) if scores else None,
        "max": max(scores) if scores else None,
    },
    "latest": items[:10],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
