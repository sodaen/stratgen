from __future__ import annotations
import sqlite3, os, time, hashlib, urllib.parse as up
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("SOURCES_DB", os.path.join(os.path.dirname(__file__), "..", "data", "sources.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def _conn():
    return sqlite3.connect(DB_PATH)

def _init():
    with _conn() as cx:
        cx.execute("""
        CREATE TABLE IF NOT EXISTS sources(
            id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            type TEXT NOT NULL,
            url TEXT,
            title TEXT,
            file_path TEXT,
            provider TEXT,
            tags TEXT,
            topic TEXT,
            subtopic TEXT,
            note TEXT,
            meta TEXT,
            fingerprint TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """)
        cx.execute("CREATE INDEX IF NOT EXISTS idx_sources_customer ON sources(customer_name)")
        cx.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_fpr ON sources(fingerprint)")
_init()

def _canon_url(url: str) -> str:
    # Lowercase Host, sortierte Query, ohne Fragmente
    p = up.urlsplit(url.strip())
    q = up.parse_qsl(p.query, keep_blank_values=True)
    q.sort(key=lambda kv: kv[0].lower())
    canon = up.urlunsplit((
        p.scheme.lower(),
        p.netloc.lower(),
        p.path or "",
        up.urlencode(q, doseq=True),
        ""  # fragment weg
    ))
    return canon

def _fp(customer: str, item: Dict[str, Any]) -> str:
    base = f"{customer}|{item.get('type')}|"
    if item.get("type") == "url":
        base += _canon_url(item["url"])
    else:
        # Für files könnte hier Pfad/Hash stehen; fürs Erste simpel:
        base += (item.get("file_path") or item.get("url") or "")
    return "src:" + hashlib.sha1(base.encode("utf-8")).hexdigest()

def register(customer_name: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    created = []
    deduped = False
    now = int(time.time())
    with _conn() as cx:
        for it in items:
            if it.get("type") == "url" and it.get("url"):
                url = _canon_url(it["url"])
            else:
                url = it.get("url")
            fp = _fp(customer_name, it)
            # existiert?
            cur = cx.execute("SELECT id FROM sources WHERE fingerprint=?", (fp,))
            row = cur.fetchone()
            if row:
                deduped = True
                continue
            new_id = hashlib.sha1(f"{fp}|{now}".encode()).hexdigest()
            cx.execute("""
                INSERT INTO sources
                (id, customer_name, type, url, title, file_path, provider, tags, topic, subtopic, note, meta, fingerprint, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_id, customer_name, it.get("type","url"), url, it.get("title"),
                it.get("file_path"), it.get("provider"),
                None, it.get("topic"), it.get("subtopic"), it.get("note"),
                None, fp, now
            ))
            created.append({
                "id": new_id,
                "customer_name": customer_name,
                "type": it.get("type","url"),
                "url": url,
                "title": it.get("title"),
                "file_path": it.get("file_path"),
                "provider": it.get("provider"),
                "tags": [],
                "topic": it.get("topic"),
                "subtopic": it.get("subtopic"),
                "note": it.get("note"),
                "meta": None,
                "fingerprint": fp,
                "created_at": now,
            })
    return {"ok": True, "deduped": deduped, "created": created}

def list_sources(customer_name: Optional[str] = None) -> List[Dict[str, Any]]:
    with _conn() as cx:
        if customer_name:
            cur = cx.execute("SELECT * FROM sources WHERE customer_name=? ORDER BY created_at DESC", (customer_name,))
        else:
            cur = cx.execute("SELECT * FROM sources ORDER BY created_at DESC")
        cols = [c[0] for c in cur.description]
        out = []
        for r in cur.fetchall():
            row = dict(zip(cols, r))
            row["tags"] = []
            row["meta"] = None
            out.append(row)
        return out

def get(src_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as cx:
        cur = cx.execute("SELECT * FROM sources WHERE id=?", (src_id,))
        r = cur.fetchone()
        if not r: return None
        cols = [c[0] for c in cur.description]
        row = dict(zip(cols, r))
        row["tags"] = []
        row["meta"] = None
        return row

def remove(src_id: str) -> bool:
    with _conn() as cx:
        cur = cx.execute("DELETE FROM sources WHERE id=?", (src_id,))
        return cur.rowcount > 0
