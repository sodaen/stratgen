from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import time

DATA_DIR = Path("data/content")
DB_PATH = Path("data/content.sqlite")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contents (
            name TEXT PRIMARY KEY,
            mission_id INTEGER,
            title TEXT,
            outline_json TEXT,
            assets_json TEXT,
            facts_json TEXT,
            extra_json TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_contents_created_at ON contents(created_at DESC);")
    conn.commit()


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = connect()
    init_db(conn)

    files = sorted(DATA_DIR.glob("content-*.json"))
    now = time.time()
    imported = 0

    for fp in files:
        name = fp.name
        with fp.open("r", encoding="utf-8") as f:
            data = json.load(f)

        mission_id = data.get("mission_id")
        title = data.get("title")
        outline = data.get("outline")
        assets = data.get("assets")
        facts = data.get("facts")
        extra = data.get("extra")

        conn.execute(
            """
            INSERT OR REPLACE INTO contents
            (name, mission_id, title, outline_json, assets_json, facts_json, extra_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM contents WHERE name = ?), ?), ?)
            """,
            (
                name,
                mission_id,
                title,
                json.dumps(outline, ensure_ascii=False) if outline is not None else None,
                json.dumps(assets, ensure_ascii=False) if assets is not None else None,
                json.dumps(facts, ensure_ascii=False) if facts is not None else None,
                json.dumps(extra, ensure_ascii=False) if extra is not None else None,
                name,
                now,
                now,
            ),
        )
        imported += 1

    conn.commit()
    print(f"[content-migrate] fertig, {imported} Dateien übernommen.")


if __name__ == "__main__":
    main()
