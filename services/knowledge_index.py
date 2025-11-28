
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
import json, csv, io, re
from rank_bm25 import BM25Okapi
try:
    from rapidfuzz.string_metric import levenshtein
except Exception:
    def levenshtein(a,b): return 0

_INDEX = None
_DOCS: List[Dict[str, Any]] = []
_TOKENS: List[List[str]] = []

DEFAULT_DIRS = ["data/knowledge", "data/raw", "data/exports"]
TEXT_EXT = {".txt",".md",".log",".rst",".csv",".json"}
# (PDF/Office bewusst ausgelassen; kommt später mit Extras)

def _read_text(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext in {".txt",".md",".log",".rst"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if ext == ".csv":
            out = io.StringIO()
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                r = csv.reader(f)
                for row in r:
                    out.write(" ".join(row)+"\n")
            return out.getvalue()
        if ext == ".json":
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            def flatten(x):
                if isinstance(x, dict):
                    return " ".join(f"{k}: {flatten(v)}" for k,v in x.items())
                if isinstance(x, list):
                    return " ".join(flatten(v) for v in x)
                return str(x)
            return flatten(data)
    except Exception:
        return ""
    return ""

def _tokenize(txt: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ÿ0-9_]+", txt.lower())

def ensure_index(dirs: Optional[List[str]]=None, force: bool=False) -> Dict[str, Any]:
    global _INDEX, _DOCS, _TOKENS
    if _INDEX is not None and not force:
        return stats()
    _DOCS, _TOKENS = [], []
    roots = [Path(d) for d in (dirs or DEFAULT_DIRS)]
    for root in roots:
        if not root.exists(): 
            continue
        for path in root.rglob("*"):
            if not path.is_file(): 
                continue
            if path.suffix.lower() not in TEXT_EXT: 
                continue
            text = _read_text(path)
            if not text.strip(): 
                continue
            tokens = _tokenize(text)
            if not tokens: 
                continue
            _DOCS.append({"id": len(_DOCS), "path": str(path), "size": path.stat().st_size, "chars": len(text)})
            _TOKENS.append(tokens)
    _INDEX = BM25Okapi(_TOKENS) if _DOCS else None
    return stats()

def stats() -> Dict[str, Any]:
    return {
        "ok": True,
        "docs": len(_DOCS),
        "indexed": bool(_INDEX),
        "roots": DEFAULT_DIRS
    }

def search(query: str, k: int=5) -> Dict[str, Any]:
    if not query.strip():
        return {"ok": False, "error": "empty query"}
    ensure_index()
    if not _INDEX:
        return {"ok": True, "results": [], "total_docs": 0}
    qtok = _tokenize(query)
    scores = _INDEX.get_scores(qtok)
    # top-k by score
    tops = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:max(1,k)]
    out = []
    for idx, sc in tops:
        doc = _DOCS[idx]
        out.append({
            "path": doc["path"],
            "score": float(sc),
            "size": doc["size"],
            "chars": doc["chars"]
        })
    return {"ok": True, "results": out, "total_docs": len(_DOCS)}
