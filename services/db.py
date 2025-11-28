
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, List
import json, sqlite3, time

DB_PATH = Path("data/projects.sqlite")

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con

def _table_info(con, table: str) -> List[sqlite3.Row]:
    return list(con.execute(f"PRAGMA table_info({table})"))

def _has_column(cols, name: str) -> bool:
    return any(c["name"] == name for c in cols)

def _ensure_schema():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects(
            id TEXT PRIMARY KEY,
            customer_name TEXT,
            topic TEXT,
            outline_json TEXT,
            -- optional columns, werden ggf. via ALTER TABLE ergänzt:
            meta_json TEXT,
            style TEXT,
            facts_json TEXT,
            logo TEXT,
            created_at INTEGER,
            updated_at INTEGER
        );
    """)
    con.commit()

    cols = _table_info(con, "projects")

    # fehlende Spalten nachziehen (idempotent)
    alters = []
    if not _has_column(cols, "meta_json"):
        alters.append("ALTER TABLE projects ADD COLUMN meta_json TEXT")
    if not _has_column(cols, "style"):
        alters.append("ALTER TABLE projects ADD COLUMN style TEXT")
    if not _has_column(cols, "facts_json"):
        alters.append("ALTER TABLE projects ADD COLUMN facts_json TEXT")
    if not _has_column(cols, "logo"):
        alters.append("ALTER TABLE projects ADD COLUMN logo TEXT")
    if not _has_column(cols, "created_at"):
        alters.append("ALTER TABLE projects ADD COLUMN created_at INTEGER")
    if not _has_column(cols, "updated_at"):
        alters.append("ALTER TABLE projects ADD COLUMN updated_at INTEGER")

    for stmt in alters:
        cur.execute(stmt)
    if alters:
        con.commit()
    con.close()

# beim Import sicherstellen
_ensure_schema()

def save_project(id: Optional[str] = None,
                 customer_name: str = "Client",
                 topic: str = "Initiative",
                 outline: Dict[str, Any] | None = None,
                 note: Optional[str] = None,
                 style: Optional[str] = None,
                 facts: Optional[Dict[str, Any]] = None,
                 logo: Optional[str] = None) -> Dict[str, Any]:
    """
    Speichert/upsert ein Projekt. Alle JSON-Felder werden als *_json persistiert.
    """
    outline = outline or {}
    facts = facts or {}
    meta = {}
    if note is not None:
        meta["note"] = note

    ts = int(time.time())
    pid = id or f"proj-{ts}"

    con = _connect()
    cur = con.cursor()

    # Upsert via INSERT OR REPLACE (einfach & robust)
    cur.execute("""
        INSERT OR REPLACE INTO projects
            (id, customer_name, topic, outline_json, meta_json, style, facts_json, logo, created_at, updated_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM projects WHERE id=?), ?), ?)
    """, (
        pid, customer_name, topic,
        json.dumps(outline, ensure_ascii=False),
        json.dumps(meta, ensure_ascii=False),
        style,
        json.dumps(facts, ensure_ascii=False),
        logo,
        pid, ts, ts
    ))
    con.commit()

    # Rückgabe
    row = con.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    con.close()
    return _row_to_project(row)

def update_project(project_id: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
    """Patch: nur gegebene Felder überschreiben."""
    con = _connect()
    row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        con.close()
        return None

    proj = _row_to_project(row)
    # Merge der bekannten Felder
    for k in ("customer_name","topic","style","logo"):
        if k in data: proj[k] = data[k]
    if "outline" in data and isinstance(data["outline"], dict):
        proj["outline"] = data["outline"]
    if "facts" in data and isinstance(data["facts"], dict):
        proj["facts"] = data["facts"]
    if "meta" in data and isinstance(data["meta"], dict):
        m = dict(proj.get("meta") or {})
        m.update(data["meta"])
        proj["meta"] = m

    ts = int(time.time())
    con.execute("""
        UPDATE projects
           SET customer_name=?,
               topic=?,
               outline_json=?,
               meta_json=?,
               style=?,
               facts_json=?,
               logo=?,
               updated_at=?
         WHERE id=?
    """, (
        proj.get("customer_name"),
        proj.get("topic"),
        json.dumps(proj.get("outline") or {}, ensure_ascii=False),
        json.dumps(proj.get("meta") or {}, ensure_ascii=False),
        proj.get("style"),
        json.dumps(proj.get("facts") or {}, ensure_ascii=False),
        proj.get("logo"),
        ts,
        project_id
    ))
    con.commit()
    row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    con.close()
    return _row_to_project(row)

def get_project(project_id: str) -> Dict[str, Any] | None:
    con = _connect()
    row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    con.close()
    return _row_to_project(row) if row else None

def list_projects() -> list[dict]:
    con = _connect()
    rows = con.execute("SELECT * FROM projects ORDER BY updated_at DESC NULLS LAST, created_at DESC").fetchall()
    con.close()
    return [_row_to_project(r) for r in rows]

def _row_to_project(row: sqlite3.Row | None) -> Dict[str, Any] | None:
    if not row:
        return None
    def _js(s):
        try:
            return json.loads(s) if s else {}
        except Exception:
            return {}
    return {
        "id": row["id"],
        "customer_name": row["customer_name"],
        "topic": row["topic"],
        "outline": _js(row["outline_json"]),
        "meta": _js(row["meta_json"]),
        "style": row["style"],
        "facts": _js(row["facts_json"]),
        "logo": row["logo"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def ensure_deck_style_tables():
    """
    Ensure PPTX-related tables exist and migrate old schema to new columns.
    New schema:
      decks(id, ts, source, meta_json)
      deck_slides(id, deck_id, slide_no, kind, title, bullets_json, notes_json)
      style_profiles(id, created_at, name, profile_json)
    """
    import sqlite3, os
    os.makedirs("data", exist_ok=True)
    dbp = os.path.join("data","projects.sqlite")
    con = sqlite3.connect(dbp)
    cur = con.cursor()

    # decks
    cur.execute("""CREATE TABLE IF NOT EXISTS decks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        source TEXT,
        meta_json TEXT
    );""")

    # deck_slides (start with minimal; then add missing cols)
    cur.execute("""CREATE TABLE IF NOT EXISTS deck_slides(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER NOT NULL,
        -- historical columns (may exist)
        idx INTEGER,
        json TEXT,
        -- target columns (may be added)
        slide_no INTEGER,
        kind TEXT,
        title TEXT,
        bullets_json TEXT,
        notes_json TEXT,
        FOREIGN KEY(deck_id) REFERENCES decks(id)
    );""")

    # Add target columns if they don't exist yet
    cur.execute("PRAGMA table_info(deck_slides)")
    cols = {r[1] for r in cur.fetchall()}
    for col, ddl in [
        ("slide_no", "ALTER TABLE deck_slides ADD COLUMN slide_no INTEGER"),
        ("kind", "ALTER TABLE deck_slides ADD COLUMN kind TEXT"),
        ("title", "ALTER TABLE deck_slides ADD COLUMN title TEXT"),
        ("bullets_json", "ALTER TABLE deck_slides ADD COLUMN bullets_json TEXT"),
        ("notes_json", "ALTER TABLE deck_slides ADD COLUMN notes_json TEXT"),
    ]:
        if col not in cols:
            try:
                cur.execute(ddl)
            except Exception:
                pass

    # style_profiles (used by learn_styles)
    cur.execute("""CREATE TABLE IF NOT EXISTS style_profiles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at INTEGER NOT NULL,
        name TEXT,
        profile_json TEXT
    );""")

    con.commit()
    con.close()


def ensure_agent_tables():
    import os, sqlite3
    os.makedirs("data", exist_ok=True)
    con = sqlite3.connect("data/projects.sqlite", timeout=30, isolation_level=None)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS agent_runs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_start INTEGER NOT NULL,
        ts_end INTEGER,
        status TEXT NOT NULL,
        details_json TEXT
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status)")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS agent_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        ts INTEGER NOT NULL,
        level TEXT,
        message TEXT,
        data_json TEXT,
        FOREIGN KEY(run_id) REFERENCES agent_runs(id)
    )""")
    con.close()

def agent_run_begin(details: dict|None=None) -> int:
    import time, json, sqlite3
    con = sqlite3.connect("data/projects.sqlite", timeout=30, isolation_level=None)
    cur = con.cursor()
    cur.execute("INSERT INTO agent_runs(ts_start, status, details_json) VALUES(?,?,?)",
                (int(time.time()), "running", json.dumps(details or {}, ensure_ascii=False)))
    rid = cur.lastrowid
    con.close()
    return rid

def agent_run_end(run_id: int, status: str, details: dict|None=None):
    import time, json, sqlite3
    con = sqlite3.connect("data/projects.sqlite", timeout=30, isolation_level=None)
    cur = con.cursor()
    cur.execute("UPDATE agent_runs SET ts_end=?, status=?, details_json=? WHERE id=?",
                (int(time.time()), status, json.dumps(details or {}, ensure_ascii=False), run_id))
    con.close()

def agent_event(run_id: int, level: str, message: str, data: dict|None=None):
    import time, json, sqlite3
    con = sqlite3.connect("data/projects.sqlite", timeout=30, isolation_level=None)
    cur = con.cursor()
    cur.execute("INSERT INTO agent_events(run_id, ts, level, message, data_json) VALUES(?,?,?,?,?)",
                (run_id, int(time.time()), level, message, json.dumps(data or {}, ensure_ascii=False)))
    con.close()
