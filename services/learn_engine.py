from __future__ import annotations
from typing import Iterable, Dict, Any, List
from pathlib import Path
import sqlite3, json
from services.strategic_grammar import extract_pptx_features, derive_patterns

DB_PATH = Path("data/projects.sqlite")

def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS learned_patterns (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_path TEXT,
          source_id TEXT UNIQUE,
          deck_title TEXT,
          features_json TEXT,
          patterns_json TEXT,
          created_at INTEGER
        )
        """)
        con.commit()

def learn_from_files(files: Iterable[str|Path]) -> Dict[str, Any]:
    _ensure_db()
    inserted, skipped = 0, 0
    with sqlite3.connect(DB_PATH) as con:
        for f in files:
            p = Path(f)
            if not (p.is_file() and p.suffix.lower()==".pptx"): continue
            feats = extract_pptx_features(p)
            patt = derive_patterns(feats)
            con.execute("""
                INSERT OR IGNORE INTO learned_patterns (source_path, source_id, deck_title, features_json, patterns_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(p), feats["source_id"], (feats["deck"] or {}).get("title"),
                  json.dumps(feats, ensure_ascii=False), json.dumps(patt, ensure_ascii=False), feats["created_at"]))
            if con.total_changes: inserted += 1
            else: skipped += 1
        con.commit()
    return {"ok": True, "inserted": inserted, "skipped": skipped, "total": inserted+skipped}

def scan_and_learn(paths: Iterable[str|Path]) -> Dict[str, Any]:
    collected: List[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_file() and p.suffix.lower()==".pptx": collected.append(p)
        elif p.is_dir(): collected.extend(p.rglob("*.pptx"))
    return learn_from_files(collected)

def stats() -> Dict[str, Any]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM learned_patterns")
        c, mi, ma = cur.fetchone()
    return {"ok": True, "count": c or 0, "oldest": mi, "newest": ma}
