
# services/knowledge.py
from __future__ import annotations
import os, re, json, math, time, sqlite3, hashlib
from typing import List, Dict, Any, Optional, Tuple


def _parse_embed_model(model: str | None):
    m = (model or '').strip()
    if not m:
        return ('hash','hash256')
    if m.startswith('openai'):
        parts = m.split(':',1)
        return ('openai', parts[1] if len(parts)>1 and parts[1] else 'text-embedding-3-small')
    if m.startswith('ollama'):
        parts = m.split(':',1)
        return ('ollama', parts[1] if len(parts)>1 and parts[1] else 'nomic-embed-text')
    # Backcompat: reiner Modellname => Ollama
    return ('ollama', m)

import json
import math
import requests
DB_PATH   = os.path.join("data", "projects.sqlite")
KNOW_ROOT = os.path.join("data", "knowledge")

def _connect():
    os.makedirs("data", exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA synchronous=NORMAL")
    return con

def ensure_tables() -> None:
    con = _connect(); cur = con.cursor()
    # knowledge_docs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_docs(
      id    INTEGER PRIMARY KEY AUTOINCREMENT,
      path  TEXT UNIQUE NOT NULL,
      kind  TEXT NOT NULL DEFAULT 'txt',
      size  INTEGER NOT NULL DEFAULT 0,
      mtime INTEGER NOT NULL DEFAULT 0,
      hash  TEXT NOT NULL DEFAULT '',
      ts INTEGER NOT NULL DEFAULT 0
    )
    """)
    # fehlende Spalten idempotent ergänzen
    cols = {r[1] for r in cur.execute("PRAGMA table_info(knowledge_docs)")}
    if "ts" not in cols:
        cur.execute("ALTER TABLE knowledge_docs ADD COLUMN ts INTEGER NOT NULL DEFAULT 0")
    if "kind" not in cols:
        cur.execute("ALTER TABLE knowledge_docs ADD COLUMN kind TEXT NOT NULL DEFAULT 'txt'")
    if "size" not in cols:
        cur.execute("ALTER TABLE knowledge_docs ADD COLUMN size INTEGER NOT NULL DEFAULT 0")
    if "hash" not in cols:
        cur.execute("ALTER TABLE knowledge_docs ADD COLUMN hash TEXT NOT NULL DEFAULT ''")

    # knowledge_chunks
    cur.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_chunks(
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      doc_id     INTEGER NOT NULL,
      idx        INTEGER NOT NULL,
      content    TEXT NOT NULL,
      created_at INTEGER NOT NULL DEFAULT 0,
      embedding  BLOB,
      FOREIGN KEY(doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE
    )
    """)
    cols2 = {r[1] for r in cur.execute("PRAGMA table_info(knowledge_chunks)")}
    if "content" not in cols2:
        # alt: "text" → in "content" migrieren
        if "text" in cols2:
            cur.execute("ALTER TABLE knowledge_chunks ADD COLUMN content TEXT")
            cur.execute("UPDATE knowledge_chunks SET content=text WHERE content IS NULL")
            # "text" Spalte ggf. belassen (SQLite kann keine DROP COLUMN vor 3.35)
    con.commit(); con.close()

def _file_hash(data: bytes) -> str:
    h = hashlib.sha256(); h.update(data); return h.hexdigest()

def _read_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def _chunk(text: str, max_len: int=1200, overlap: int=120) -> List[str]:
    text = re.sub(r'\r\n?', '\n', text)
    if not text.strip():
        return []
    chunks: List[str] = []
    i = 0
    while i < len(text):
        chunk = text[i:i+max_len]
        chunks.append(chunk)
        if i + max_len >= len(text):
            break
        i += (max_len - overlap)
    return chunks

def _upsert_doc(cur, path:str, kind:str, size:int, mtime:int, hsh:str) -> int:
    ts_now = int(time.time())
    cur.execute("""
    INSERT INTO knowledge_docs(path, kind, size, mtime, hash, ts)
    VALUES(?, ?, ?, ?, ?, ?)
    ON CONFLICT(path) DO UPDATE SET
      kind=excluded.kind,
      size=excluded.size,
      mtime=excluded.mtime,
      hash=excluded.hash,
      ts=CASE WHEN knowledge_docs.ts IS NULL OR knowledge_docs.ts=0 THEN excluded.ts ELSE knowledge_docs.ts END
    """, (path, kind, size, mtime, hsh, ts_now))
    row = cur.execute("SELECT id FROM knowledge_docs WHERE path=?", (path,)).fetchone()
    return int(row["id"])

def scan_dir(root: Optional[str]=None) -> Dict[str, Any]:
    """
    Scannt TXT im knowledge-Ordner, aktualisiert knowledge_docs und (re)schreibt chunks.
    PDFs bitte vorab in TXT wandeln (bereits diskutiert). Idempotent.
    """
    ensure_tables()
    root = root or KNOW_ROOT
    os.makedirs(root, exist_ok=True)

    con = _connect(); cur = con.cursor()
    inserted = updated = skipped = total = 0

    for dirpath, _, files in os.walk(root):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in (".txt",):
                continue
            fpath = os.path.join(dirpath, fn)
            total += 1
            try:
                b = open(fpath, "rb").read()
                h = _file_hash(b)
                st = os.stat(fpath)
                kind = "txt"; size = st.st_size; mtime = int(st.st_mtime)

                # existierendes?
                row = cur.execute("SELECT id, hash FROM knowledge_docs WHERE path=?", (fpath,)).fetchone()
                if row and row["hash"] == h:
                    skipped += 1
                    continue

                doc_id = _upsert_doc(cur, fpath, kind, size, mtime, h)

                # alte Chunks löschen und neu schreiben (einfach & robust)
                cur.execute("DELETE FROM knowledge_chunks WHERE doc_id=?", (doc_id,))
                text = _read_txt(fpath)
                chs = _chunk(text)
                now = int(time.time())
                for idx, c in enumerate(chs):
                    cur.execute("""
                    INSERT INTO knowledge_chunks(doc_id, idx, content, created_at, embedding)
                    VALUES(?, ?, ?, ?, NULL)
                    """, (doc_id, idx, c, now))
                if row:
                    updated += 1
                else:
                    inserted += 1

                con.commit()
            except Exception as e:
                # Wir crashen nicht, sondern zählen als skipped
                skipped += 1

    con.close()
    return {"ok": True, "inserted": inserted, "updated": updated, "skipped": skipped, "total": total}

# -------- Heuristische Embeddings (Hashing-Trick) --------

def _tokenize(text:str) -> List[str]:
    return re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", (text or "").lower())

def _hash_embedding(text: str, dim:int=256) -> List[float]:
    """Heuristisches Fallback-Embedding: Wort-Hashing in fixen Vektorraum."""
    vec = [0.0]*dim
    for t in _tokenize(text):
        h = int(hashlib.sha1(t.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    # L2-Norm
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v/norm for v in vec]


def embed_all(model: str | None = None):
    """
    Embeddet alle Chunks ohne Embedding in knowledge_chunks.
    Provider via `model` oder $EMBED_MODEL:
      - "hash" (Default, schnell, 32-dim)
      - "ollama:MODEL"
      - "openai:MODEL"
    """
    ensure_tables()
    import json
    con = _connect()
    con.execute("PRAGMA journal_mode=WAL")
    cur = con.cursor()

    provider, mname = _parse_embed_model(model)
    rows = cur.execute("SELECT id, content FROM knowledge_chunks WHERE embedding IS NULL ORDER BY id ASC").fetchall()
    if not rows:
        con.close()
        return {"ok": True, "provider": provider, "embedded": 0}

    def write_vec(cid, vec):
        cur.execute("UPDATE knowledge_chunks SET embedding=? WHERE id=?", (json.dumps(vec), cid))

    total = 0

    if provider == "hash":
        for cid, txt in rows:
            vec = _hash_embed([txt])[0]
            write_vec(cid, vec)
            total += 1
        con.commit()
        try:
            _set_setting("embed_model", "hash")
            _set_setting("embed_dim", len(vec))
        except Exception:
            pass
        con.close()
        return {"ok": True, "provider": "hash", "embedded": total}

    # Netz-Provider (Batching)
    BATCH = 64
    buf_ids, buf_txt = [], []
    first_dim = None

    def flush():
        nonlocal total, buf_ids, buf_txt, first_dim
        if not buf_ids:
            return
        if provider.startswith("ollama"):
            vecs = _ollama_embed(buf_txt, mname)
        elif provider.startswith("openai"):
            vecs = _openai_embed(buf_txt, mname)
        else:
            raise RuntimeError(f"unknown provider: {provider}")
        if first_dim is None and vecs:
            first_dim = len(vecs[0])
            try:
                _set_setting("embed_model", f"{provider}:{mname}" if mname else provider)
                _set_setting("embed_dim", first_dim)
            except Exception:
                pass
        for cid, v in zip(buf_ids, vecs):
            write_vec(cid, v)
            total += 1
        buf_ids.clear(); buf_txt.clear()
        con.commit()

    for cid, txt in rows:
        buf_ids.append(cid); buf_txt.append(txt or "")
        if len(buf_ids) >= BATCH:
            flush()
    flush()
    con.close()
    return {"ok": True, "provider": provider, "model": mname, "embedded": total}
def search(q: str, limit: int = 5, semantic: int = 0) -> dict:
    """
    Semantische Suche:
    - Wenn Embeddings vorhanden: Query-Embedding zur gespeicherten Dim/Modell passend erzeugen
    - Cosine Score; Mismatch-Dimensionen -> Query ggf. auf Hash256 umbiegen
    - Fallback: LIKE
    """
    import json
    ensure_tables()
    con = _connect(); cur = con.cursor()
    limit = max(1, min(int(limit or 5), 50))
    if not q:
        return {"ok": True, "results": []}

    results = []

    if semantic:
        cnt = cur.execute(
            "SELECT COUNT(1) FROM knowledge_chunks WHERE embedding IS NOT NULL AND embedding!=''"
        ).fetchone()[0]
        if cnt > 0:
            model = _get_setting(cur, "embed_model", "hash256")
            try:
                dim = int(_get_setting(cur, "embed_dim", "256") or "256")
            except Exception:
                dim = 256

            # Query-Vektor
            if model != "hash256" and dim > 256:
                try:
                    qv = _ollama_embed([q], model=model)[0]
                except Exception:
                    qv = _hash_embedding(q, dim=256)
            else:
                qv = _hash_embedding(q, dim=256)

            rows = cur.execute("""
                SELECT d.path, c.content, c.embedding
                FROM knowledge_chunks c
                JOIN knowledge_docs d ON d.id=c.doc_id
                WHERE c.embedding IS NOT NULL AND c.embedding!=''
                LIMIT 2000
            """).fetchall()

            scored = []
            for r in rows:
                emb = _as_vec(r["embedding"])
                if not emb:
                    continue
                if len(emb) != len(qv):
                    if len(emb) == 256:
                        qv_local = _hash_embedding(q, dim=256)
                    else:
                        # Unpassende Dimension -> überspringen
                        continue
                else:
                    qv_local = qv
                na = _l2(qv_local) or 1.0
                nb = _l2(emb) or 1.0
                score = sum(a*b for a,b in zip(qv_local, emb)) / (na*nb)
                scored.append((float(score), r["path"], r["content"]))

            scored.sort(key=lambda x: x[0], reverse=True)
            for sc, path, content in scored[:limit]:
                snippet = _clean_snippet(content)
                results.append({"path": path, "score": round(sc, 4), "snippet": snippet[:280].strip()})
            con.close()
            return {"ok": True, "results": results}

    # Fallback: einfache LIKE-Suche
    like = f"%{q.lower()}%"
    rows = cur.execute("""
        SELECT d.path, c.content
        FROM knowledge_chunks c
        JOIN knowledge_docs d ON d.id=c.doc_id
        WHERE lower(c.content) LIKE ?
        LIMIT ?
    """, (like, limit)).fetchall()
    for r in rows:
        snippet = _clean_snippet(content)
        results.append({"path": r["path"], "snippet": snippet[:280].strip()})
    con.close()
    return {"ok": True, "results": results}
# --- /FIXED_EMBED_AND_SEARCH ---


# --- FIXED_DIM_MATCH (appended) ---
def _pad_or_truncate(vec, target_dim):
    """Passt die Länge von vec auf target_dim an (Padding mit 0.0 oder Trunkierung)."""
    if not isinstance(vec, list):
        return []
    if len(vec) == target_dim:
        return vec
    if len(vec) > target_dim:
        return vec[:target_dim]
    return vec + [0.0]*(target_dim - len(vec))

def search(q: str, limit: int = 5, semantic: int = 0) -> dict:
    import json, math
    ensure_tables()
    con = _connect(); cur = con.cursor()
    limit = max(1, min(int(limit or 5), 50))
    if not q:
        return {"ok": True, "results": []}

    results = []

    if semantic:
        cnt = cur.execute(
            "SELECT COUNT(1) FROM knowledge_chunks WHERE embedding IS NOT NULL AND embedding!=''"
        ).fetchone()[0]
        if cnt > 0:
            model = _get_setting(cur, "embed_model", "hash256")
            try:
                dim = int(_get_setting(cur, "embed_dim", "256") or "256")
            except Exception:
                dim = 256

            # Query einbetten
            qv = []
            if model != "hash256" and dim > 256:
                try:
                    qv = _ollama_embed([q], model=model)[0]
                except Exception:
                    qv = _hash_embedding(q, dim=256)
            else:
                qv = _hash_embedding(q, dim=256)

            rows = cur.execute("""
                SELECT d.path, c.content, c.embedding
                FROM knowledge_chunks c
                JOIN knowledge_docs d ON d.id=c.doc_id
                WHERE c.embedding IS NOT NULL AND c.embedding!=''
                LIMIT 5000
            """).fetchall()

            scored = []
            for r in rows:
                emb = _as_vec(r["embedding"])
                if not emb:
                    continue
                # Dimensionen kompatibel machen (anstatt zu skippen!)
                qv_local = qv
                if len(emb) != len(qv_local):
                    qv_local = _pad_or_truncate(qv_local, len(emb))

                na = _l2(qv_local) or 1.0
                nb = _l2(emb) or 1.0
                score = sum(a*b for a,b in zip(qv_local, emb)) / (na*nb)
                scored.append((float(score), r["path"], r["content"] or ""))

            scored.sort(key=lambda x: x[0], reverse=True)
            for sc, path, content in scored[:limit]:
                snippet = _clean_snippet(content)
                results.append({"path": path, "score": round(sc, 4), "snippet": snippet[:280].strip()})
            con.close()
            return {"ok": True, "results": results}

    # Fallback: LIKE
    like = f"%{q.lower()}%"
    rows = cur.execute("""
        SELECT d.path, c.content
        FROM knowledge_chunks c
        JOIN knowledge_docs d ON d.id=c.doc_id
        WHERE lower(c.content) LIKE ?
        LIMIT ?
    """, (like, limit)).fetchall()
    for r in rows:
        snippet = _clean_snippet(content)
        results.append({"path": r["path"], "snippet": snippet[:280].strip()})
    con.close()
    return {"ok": True, "results": results}
# --- /FIXED_DIM_MATCH ---


def _clean_snippet(s: str, maxlen: int = 280) -> str:
    if not s:
        return ""
    # robuste Zeilenumbrüche/Whitespace-Normalisierung
    s = s.replace("\r", " ").replace("\n", " ")
    s = " ".join(s.split())
    return s[:maxlen]


def _json_to_vec(x):
    import json
    if x is None: return []
    if isinstance(x, (bytes, bytearray)):
        try: x = x.decode("utf-8","ignore")
        except: x = str(bytes(x))
    x = (x or "").strip()
    if not x: return []
    if x.startswith("["):
        try: return [float(v) for v in json.loads(x)]
        except: return []
    # CSV-Fallback
    try: return [float(t.strip()) for t in x.strip("[]").split(",") if t.strip()]
    except: return []


# --- SEARCH_V2 ---
def search_v2(q: str, limit: int = 5, semantic: int = 0) -> dict:
    # 1) Grundsicherung: Tabellen existieren
    ensure_tables()
    # 2) Chunks + Embeddings holen
    rows = _q("""\
SELECT c.id, d.path, c.content, c.embedding\
FROM knowledge_chunks c\
JOIN knowledge_docs d ON d.id=c.doc_id\
WHERE c.embedding IS NOT NULL AND c.embedding!=""\
""")
    if not rows:
        # Fallback: rein lexikalisch
        if not q:
            return {"ok": True, "results": []}
        hits = _q("""\
SELECT c.id, d.path, c.content\
FROM knowledge_chunks c\
JOIN knowledge_docs d ON d.id=c.doc_id\
WHERE c.content LIKE ?\
LIMIT ?\
""", (f"%{q}%", limit))
        results = []
        for _id, path, chunk in hits:
            results.append({
                "id": _id,
                "path": path or "",
                "score": 0.0,
                "snippet": _clean_snippet(chunk or "")
            })
        return {"ok": True, "results": results}

    # 3) Ziel-Dimension aus erstem Embedding ableiten
    first_vec = _json_to_vec(rows[0][3])
    target_dim = len(first_vec)

    # 4) Query-Embedding (nur wenn semantic=1, sonst lexikalisch)
    results = []
    if semantic:
        # Modell merken/lesen (optional – wenn ihr settings nutzt)
        try:
            import sqlite3
            con = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
            cur = con.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
            row = cur.execute("SELECT value FROM settings WHERE key='embed_model'").fetchone()
            model = row[0] if row and row[0] else os.environ.get("EMBED_MODEL","nomic-embed-text")
            con.close()
        except Exception:
            import os
            model = os.environ.get("EMBED_MODEL","nomic-embed-text")

        qvec = _ollama_embed([q], model=model)[0] if q else []
        qvec = _pad_or_truncate(qvec, target_dim)

        # 5) Cosine für alle Chunks
        for _id, path, chunk, emb in rows:
            v = _pad_or_truncate(_json_to_vec(emb), target_dim)
            score = _cosine(qvec, v)
            results.append((
                score,
                {
                    "id": _id,
                    "path": path or "",
                    "score": round(float(score), 6),
                    "snippet": _clean_snippet(chunk or "")
                }
            ))
        # 6) Sortieren & top-k schneiden (kein harter Threshold!)
        results.sort(key=lambda x: x[0], reverse=True)
        results = [r for _, r in results[:max(1, int(limit))]]

        # Falls alle Scores quasi 0 sind → lexikalischer Fallback
        if not results or all(abs(r["score"]) < 1e-9 for r in results):
            hits = _q("""\
SELECT c.id, d.path, c.content\
FROM knowledge_chunks c\
JOIN knowledge_docs d ON d.id=c.doc_id\
WHERE c.content LIKE ?\
LIMIT ?\
""", (f"%{q}%", limit))
            results = []
            for _id, path, chunk in hits:
                results.append({
                    "id": _id,
                    "path": path or "",
                    "score": 0.0,
                    "snippet": _clean_snippet(chunk or "")
                })
        return {"ok": True, "results": results}

    # --- rein lexikalisch ---
    hits = _q("""\
SELECT c.id, d.path, c.content\
FROM knowledge_chunks c\
JOIN knowledge_docs d ON d.id=c.doc_id\
WHERE c.content LIKE ?\
LIMIT ?\
""", (f"%{q}%", limit))
    for _id, path, chunk in hits:
        results.append({
            "id": _id,
            "path": path or "",
            "score": 0.0,
            "snippet": _clean_snippet(chunk or "")
        })
    return {"ok": True, "results": results}

# Alias aktivieren
search = search_v2


def _q(sql: str, params: tuple = ()):
    """Einmaliger Query-Helper: öffnet kurz eine DB-Verbindung, führt aus, liefert rows."""
    con = _connect(); cur = con.cursor()
    rows = cur.execute(sql, params).fetchall()
    con.close()
    return rows


# --- HOTFIX_SEARCH_FINAL ---
def _json_to_vec(x):
    import json
    if x is None: return []
    if isinstance(x, (bytes, bytearray)):
        try: x = x.decode("utf-8","ignore")
        except Exception: x = str(bytes(x))
    x = (x or "").strip()
    if not x: return []
    if x.startswith("["):
        try:
            v = json.loads(x)
            if isinstance(v, list):
                return [float(t) for t in v]
        except Exception:
            return []
    # CSV-Notnagel
    try: return [float(t.strip()) for t in x.strip("[]").split(",") if t.strip()]
    except Exception: return []

def _pad_or_truncate(vec, target_dim):
    if not isinstance(vec, list): return []
    if target_dim <= 0: return []
    if len(vec) == target_dim: return vec
    if len(vec) > target_dim:  return vec[:target_dim]
    return vec + [0.0]*(target_dim - len(vec))

def _clean_snippet(s: str, maxlen: int = 280) -> str:
    if not s: return ""
    s = s.replace("\r", " ").replace("\n", " ")
    s = " ".join(s.split())
    return s[:maxlen]

def _embed_query(text, cur):
    # Modell aus settings; fallback auf nomic-embed-text → sonst Hash256
    model = None
    try:
        cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        row = cur.execute("SELECT value FROM settings WHERE key='embed_model'").fetchone()
        model = (row[0] if row and row[0] else None)
    except Exception:
        model = None
    if not model:
        model = "nomic-embed-text"
    # Versuch: Ollama /api/embed
    try:
        vecs = _ollama_embed([text], model=model)
        if vecs and isinstance(vecs[0], list):
            return [float(x) for x in vecs[0]]
    except Exception:
        pass
    # Fallback: Hash 256
    return _hash_embedding(text, dim=256)

def search(q: str, limit: int = 5, semantic: int = 0) -> dict:
    ensure_tables()
    con = _connect(); cur = con.cursor()
    try:
        limit = max(1, min(int(limit or 5), 50))
    except Exception:
        limit = 5
    if not q:
        con.close(); return { "ok": True, "results": [] }

    # SEMANTIK
    if semantic:
        rows = cur.execute(
            "SELECT d.path, c.content, c.embedding "
            "FROM knowledge_chunks c "
            "JOIN knowledge_docs d ON d.id=c.doc_id "
            "WHERE c.embedding IS NOT NULL AND c.embedding!='' "
            "LIMIT 5000"
        ).fetchall()
        if rows:
            # Ziel-Dim am ersten Embedding ableiten
            target_dim = len(_json_to_vec(rows[0]["embedding"]))
            qv = _pad_or_truncate(_embed_query(q, cur), target_dim)
            # Score
            scored = []
            for r in rows:
                ev = _pad_or_truncate(_json_to_vec(r["embedding"]), target_dim)
                sc = _cosine(qv, ev)
                scored.append((float(sc), r["path"], r["content"] or ""))
            scored.sort(key=lambda t: t[0], reverse=True)
            out = [{"path": (p or "unknown"), "score": round(sc, 4), "snippet": _clean_snippet(ct)} for sc, p, ct in scored[:limit]]
            con.close()
            return { "ok": True, "results": out }

    # LEXIKALISCHER FALLBACK (funktioniert immer)
    like = f"%{q.lower()}%"
    rows = cur.execute(
        "SELECT d.path, c.content "
        "FROM knowledge_chunks c "
        "JOIN knowledge_docs d ON d.id=c.doc_id "
        "WHERE lower(c.content) LIKE ? "
        "LIMIT ?",
        (like, limit)
    ).fetchall()
    out = [{"path": (r["path"] if r["path"] else "unknown"), "snippet": _clean_snippet(r["content"] or "")} for r in rows]
    con.close()
    return { "ok": True, "results": out }

# /HOTFIX_SEARCH_FINAL


# === FIX: stabile Suche (COALESCE(content,text), Ollama optional, LIKE Fallback) ===
def search(q: str, limit: int = 5, semantic: int = 0) -> dict:
    import sqlite3, json, os, math
    # optional: requests wird nur bei semantic gebraucht
    try:
        import requests  # noqa: F401
    except Exception:
        requests = None  # type: ignore

    ensure_tables()
    try:
        limit = max(1, min(int(limit or 5), 50))
    except Exception:
        limit = 5
    if not q:
        return {"ok": True, "results": []}

    con = _connect()
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    txt_expr = "COALESCE(c.content, c.text)"

    # --- SEMANTIK: nur wenn gewünscht ---
    if semantic:
        # Modellname holen (Settings/ENV → Default nomic-embed-text)
        try:
            model = _get_setting(cur, "embed_model", os.environ.get("EMBED_MODEL", "nomic-embed-text"))
        except Exception:
            model = os.environ.get("EMBED_MODEL", "nomic-embed-text")

        qv = []
        # Query-Embedding via Ollama (/api/embed)
        try:
            if requests is not None:
                r = requests.post(
                    "http://127.0.0.1:11434/api/embed",
                    json={"model": model, "input": [q]},
                    timeout=30,
                )
                r.raise_for_status()
                data = r.json()
                qv = (data.get("embeddings") or [[]])[0]
        except Exception:
            qv = []

        # Kandidaten (eingebettete Chunks)
        rows = cur.execute(
            "SELECT d.path AS path, " + txt_expr + " AS txt, c.embedding AS embedding "
            "FROM knowledge_chunks c "
            "JOIN knowledge_docs d ON d.id = c.doc_id "
            "WHERE c.embedding IS NOT NULL AND c.embedding!='' "
            "LIMIT 5000"
        ).fetchall()

        def _to_vec(x):
            if x is None:
                return []
            if isinstance(x, (bytes, bytearray)):
                try:
                    x = x.decode("utf-8", "ignore")
                except Exception:
                    x = ""
            x = (x or "").strip()
            try:
                v = json.loads(x)
            except Exception:
                v = []
            return v if isinstance(v, list) else []

        def _cos(a, b):
            if not a or not b:
                return 0.0
            L = min(len(a), len(b))
            s = na = nb = 0.0
            for i in range(L):
                ai = float(a[i]); bi = float(b[i])
                s += ai * bi; na += ai * ai; nb += bi * bi
            na = math.sqrt(na) or 1.0
            nb = math.sqrt(nb) or 1.0
            return s / (na * nb)

        scored = []
        if qv:
            for r in rows:
                v = _to_vec(r["embedding"])
                if not v:
                    continue
                score = _cos(qv, v)
                scored.append((score, r["path"] or "", r["txt"] or ""))

            scored.sort(key=lambda t: t[0], reverse=True)
            out = [{"path": p, "score": float(f"{sc:.4f}"), "snippet": _clean_snippet(t)}
                   for sc, p, t in scored[:limit]]
            # Nur zurückgeben, wenn nicht komplett leer
            if out:
                con.close()
                return {"ok": True, "results": out}

    # --- Fallback: einfache LIKE-Suche (funktioniert immer, wenn Wort im Korpus) ---
    like = "%" + q.lower() + "%"
    rows = cur.execute(
        "SELECT d.path AS path, " + txt_expr + " AS txt "
        "FROM knowledge_chunks c "
        "JOIN knowledge_docs d ON d.id = c.doc_id "
        "WHERE lower(" + txt_expr + ") LIKE ? "
        "LIMIT ?",
        (like, limit),
    ).fetchall()

    out = [{"path": (r["path"] or ""), "score": 0.0, "snippet": _clean_snippet(r["txt"] or "")}
           for r in rows]
    con.close()
    return {"ok": True, "results": out}
# === /FIX ===



def _open_conn(db_path: str = "data/projects.sqlite"):
    import sqlite3
    con = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    return con

def _as_vec_any(x):
    import json
    if x is None: return []
    if isinstance(x, (bytes, bytearray)):
        try: x = x.decode("utf-8","ignore")
        except: x = str(bytes(x))
    xs = (x or "").strip()
    if not xs: return []
    if xs[:1] == '[':
        try: return [float(v) for v in json.loads(xs)]
        except: pass
    try:
        return [float(p.strip()) for p in xs.strip("[]").split(",") if p.strip()]
    except:
        return []

def _cosine(a, b):
    import math
    if not a or not b: return 0.0
    s=0.0; na=0.0; nb=0.0
    for i in range(min(len(a), len(b))):
        ai=a[i]; bi=b[i]
        s += ai*bi; na += ai*ai; nb += bi*bi
    if na<=0 or nb<=0: return 0.0
    return s / (math.sqrt(na)*math.sqrt(nb))

def _clean_snippet(s: str, maxlen: int = 280) -> str:
    if not s: return ""
    s = s.replace("\r", " ").replace("\n", " ")
    s = " ".join(s.split())
    return s[:maxlen]


def _openai_embed(texts: list[str], model: str, api_key: str | None = None) -> list[list[float]]:
    import os, requests
    api_key = api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY fehlt')
    url = 'https://api.openai.com/v1/embeddings'
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {'model': model, 'input': texts}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return [item['embedding'] for item in data.get('data', [])]
