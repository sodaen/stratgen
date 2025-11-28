from __future__ import annotations


from pathlib import Path
from typing import List, Optional, Union

from fastapi import APIRouter, Query, HTTPException, Body
import unicodedata
from typing import Dict
from typing import Any
import time
import json
import math
import os
from pydantic import BaseModel

# interne Services
from services import knowledge
try:
    # dein FS-Index (war in deinem Repo schon da)
    from services.knowledge_fs import (
        ensure_index,
        ix_search,
        ix_stats,
        DEFAULT_KNOWLEDGE_DIRS,
    )
except Exception:
    # Fallback, falls es das Modul mal nicht geben sollte
    DEFAULT_KNOWLEDGE_DIRS = ["data/knowledge", "data/knowledge/derived"]
    def ensure_index(dirs: list[str], force: bool = False):
        return {"ok": True, "dirs": dirs, "forced": force}
    def ix_search(q: str, k: int = 5):
        return {"ok": True, "results": []}
    def ix_stats():
        return {"ok": True, "stats": {}}

router = APIRouter(tags=["knowledge"])


def _sanitize_model_name(name: str) -> str:
    # akzeptiert "sbert:sentence-transformers/all-MiniLM-L6-v2" oder reinen Modellnamen
    return name.split(":", 1)[-1]

def _cos_sim(a, b):
    # wenn normalisiert encode(normalize_embeddings=True), ist cosine == dot
    return float(sum(x * y for x, y in zip(a, b)))

# --- Canonical SBERT embeddings + semantic search (stable) ---
from pathlib import Path as _Path
import json as _json
import time as _time
from fastapi import Query, HTTPException

_EMB_DIR = _Path("data/knowledge/embeddings")
_DERIVED_DIR = _Path("data/knowledge/derived")
_EMB_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/knowledge/embed_local")
def knowledge_embed_local(model: str = Query("sbert:sentence-transformers/all-MiniLM-L6-v2")):
    """
    Baut lokale SBERT-Embeddings aller TXT-Dateien in data/knowledge/derived und schreibt:
      - data/knowledge/embeddings/vectors.jsonl
      - data/knowledge/embeddings/index.json
      - data/knowledge/embeddings/<model>.jsonl (Bequemlichkeitskopie)
    """
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SBERT not available: {e}")

    model_id = model.split(":", 1)[-1]
    docs = []
    if _DERIVED_DIR.exists():
        for pth in sorted(_DERIVED_DIR.glob("*.txt")):
            try:
                txt = pth.read_text(encoding="utf-8", errors="ignore").strip()
            except Exception:
                txt = ""
            if txt:
                docs.append({"path": str(pth), "text": txt})

    if not docs:
        return {"ok": True, "indexed": 0, "note": "no non-empty txt"}

    encoder = SentenceTransformer(model_id)
    mat = encoder.encode([d["text"] for d in docs],
                         convert_to_numpy=True, normalize_embeddings=True)

    vec_path = _EMB_DIR / "vectors.jsonl"
    idx_path = _EMB_DIR / "index.json"

    with vec_path.open("w", encoding="utf-8") as vf:
        for d, vec in zip(docs, mat):
            rec = {"path": d["path"], "dim": int(vec.shape[0]), "vector": vec.tolist()}
            vf.write(_json.dumps(rec, ensure_ascii=False) + "\n")

    with idx_path.open("w", encoding="utf-8") as jf:
        _json.dump({"model": model_id, "ts": _time.time(), "count": len(docs)},
                   jf, ensure_ascii=False, indent=2)

    # Modell-spezifische Kopie (optional)
    (_EMB_DIR / (model_id.replace("/", "_") + ".jsonl")).write_text(
        vec_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    return {"ok": True, "indexed": len(docs),
            "vectors_jsonl": str(vec_path), "index_json": str(idx_path)}

@router.get("/knowledge/search_semantic")
def knowledge_search_semantic(q: str = Query(...), k: int = Query(5, ge=1, le=50)):
    """
    Lineare semantische Suche über vectors.jsonl (Cosine == Dot dank normalize_embeddings=True).
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SBERT not available: {e}")

    idx_path = _EMB_DIR / "index.json"
    vec_path = _EMB_DIR / "vectors.jsonl"
    if not idx_path.exists() or not vec_path.exists():
        raise HTTPException(status_code=404, detail="No embeddings found. Run /knowledge/embed_local first.")

    meta = _json.loads(idx_path.read_text(encoding="utf-8"))
    model_id = meta.get("model", "sentence-transformers/all-MiniLM-L6-v2")

    enc = SentenceTransformer(model_id)
    qvec = enc.encode([q], convert_to_numpy=True, normalize_embeddings=True)[0]

    results = []
    with vec_path.open("r", encoding="utf-8") as vf:
        for line in vf:
            rec = _json.loads(line)
            vec = np.asarray(rec["vector"], dtype="float32")
            score = float((qvec * vec).sum())  # cosine == dot (normalized)
            results.append({"path": rec["path"], "score": round(score, 6)})

    results.sort(key=lambda r: r["score"], reverse=True)
    return {"ok": True, "results": results[:max(1, k)], "total": len(results)}

@router.post("/knowledge/scan")
def knowledge_scan(
    root: Optional[str] = Query(None, description="Optionales Root-Verzeichnis (überschreibt Defaults)"),
    force: bool = Query(False, description="Index/Scan forcieren")
) -> Dict[str, Any]:
    """
    Schneller Knowledge-Scan/Index-Build. Nutzt services.knowledge/services.knowledge_fs wenn vorhanden;
    fällt sonst auf einen einfachen Datei-Scan (TXT/MD/CSV/JSON) zurück.
    """
    try:
        # bevorzugt: neuer Dienst
        try:
            from services.knowledge import scan as _svc_scan  # type: ignore
            return _svc_scan(root=root, force=force) or {"ok": True}
        except Exception:
            pass
        # fallback: einfacher BM25-Index über Files
        from services.knowledge_index import ensure_index, DEFAULT_DIRS  # type: ignore
        dirs = [root] if root else DEFAULT_DIRS
        stats = ensure_index(dirs=dirs, force=force)
        # Form an die alten Tests anlehnen (inserted/updated/skipped/total)
        docs = int(stats.get("docs", 0))
        return {"ok": True, "inserted": 0, "updated": 0, "skipped": docs, "total": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"scan failed: {e}")


class _SemanticQuery(BaseModel):
    q: str
    k: int = 6

@router.post("/knowledge/search_semantic")
def knowledge_search_semantic_post(payload: _SemanticQuery):
    """
    POST-Alias für JSON-Body:
      { "q": "...", "k": 6 }
    Leitet auf die bestehende GET-Implementierung um.
    """
    return knowledge_search_semantic(q=payload.q, k=payload.k)


class _SearchReq(BaseModel):
    q: str
    k: int = 6
    dedup: bool = True

@router.post("/knowledge/search_semantic_v2")
def knowledge_search_semantic_v2(payload: _SearchReq):
    # Reuse v1
    base = knowledge_search_semantic(q=payload.q, k=payload.k)
    results = base.get("results", []) if isinstance(base, dict) else []
    if payload.dedup:
        seen = set()
        deduped = []
        for r in results:
            b = os.path.basename(r.get("path",""))
            if b in seen:
                continue
            seen.add(b)
            deduped.append(r)
        results = deduped
    return {"ok": True, "results": results, "total": len(results)}
