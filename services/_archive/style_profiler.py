
from __future__ import annotations
from typing import Any, Dict
import os, json, time, sqlite3

def profile_from_db(limit: int = 500) -> Dict[str, Any]:
    """Sehr einfache Heuristik: Häufigste Slide-Typen, mittlere Decklänge, Anteil 'agenda'."""
    dbp = os.path.join("data","projects.sqlite")
    if not os.path.exists(dbp):
        return {"ok": False, "detail": "db missing"}
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT id, meta_json FROM decks ORDER BY id DESC LIMIT ?", (limit,))
    deck_ids = []
    lengths = []
    kind_count = {}
    for r in cur.fetchall():
        meta = json.loads(r["meta_json"] or "{}")
        deck_ids.append(r["id"])
        lengths.append(int(meta.get("slide_count") or 0))
    if deck_ids:
        marks = ",".join("?"*len(deck_ids))
        cur2 = con.execute(f"SELECT json FROM deck_slides WHERE deck_id IN ({marks})", tuple(deck_ids))
        for sl in cur2.fetchall():
            try:
                d = json.loads(sl["json"] or "{}")
                k = d.get("kind") or "section"
                kind_count[k] = kind_count.get(k,0)+1
            except Exception:
                pass
    con.close()
    avg_len = (sum(lengths)/len(lengths)) if lengths else 0
    total = sum(kind_count.values()) or 1
    kind_share = {k: v/total for (k,v) in kind_count.items()}
    return {
        "ok": True,
        "avg_len": avg_len,
        "kind_share": kind_share,
        "decks": len(lengths),
    }

def persist_style(name: str = "default") -> Dict[str, Any]:
    prof = profile_from_db()
    if not prof.get("ok"):
        return prof
    import sqlite3
    dbp = os.path.join("data","projects.sqlite")
    con = sqlite3.connect(dbp)
    cur = con.cursor()
    ts = int(time.time())
    cur.execute("INSERT INTO styles(ts,name,profile_json) VALUES (?,?,?)",
                (ts, name, json.dumps(prof, ensure_ascii=False)))
    sid = cur.lastrowid
    con.commit(); con.close()
    return {"ok": True, "style_id": sid, "profile": prof}
