from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
import os, re, time

router = APIRouter(tags=["knowledge"])

DERIVED_DIR = os.path.join("data", "knowledge", "derived")

class SearchReq(BaseModel):
    q: str
    k: int = 6
    dedup: bool = True
    with_snippets: bool = True
    rerank: bool = True
    snippet_bytes: int = 280
    debug: bool = False

def _read_text_snippet(path: str, query: str, max_bytes: int = 280) -> Optional[str]:
    try:
        p = path if os.path.isabs(path) else os.path.abspath(path)
        if not os.path.exists(p):
            alt = os.path.abspath(os.path.join(DERIVED_DIR, os.path.basename(path)))
            if os.path.exists(alt):
                p = alt
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return None
    text = re.sub(r"\s+", " ", text)
    low = text.lower()
    tokens = [t for t in re.split(r"\W+", query.lower()) if t]
    hits = [low.find(t) for t in tokens if t]
    pos = min([i for i in hits if i >= 0], default=0)
    start = max(0, pos - max_bytes // 3)
    end = min(len(text), start + max_bytes)
    snippet = text[start:end].strip()
    return snippet or None

def _token_overlap(snippet: str, tokens: List[str]) -> int:
    if not snippet:
        return 0
    s = snippet.lower()
    return sum(s.count(t) for t in tokens if t)

def search_semantic_v2_local(
    q: str,
    k: int = 6,
    dedup: bool = True,
    with_snippets: bool = True,
    rerank: bool = True,
    snippet_bytes: int = 280,
    debug: bool = False,
) -> Dict:
    t0 = time.time()
    try:
        from backend.knowledge_api import knowledge_search_semantic  # returns {"results":[{"path","score"},...]}
        base = knowledge_search_semantic(q=q, k=max(k, 6))
        raw = base.get("results", []) if isinstance(base, dict) else []
    except Exception:
        raw = []

    tokens = [t for t in re.split(r"\W+", q.lower()) if t]
    items: List[Dict] = []
    best_by_title: Dict[str, Dict] = {}

    for r in raw:
        path = r.get("path")
        score = float(r.get("score", 0.0))
        title = os.path.splitext(os.path.basename(path or ""))[0] or "document"
        rec: Dict = {"path": path, "score": score, "title": title}

        if with_snippets and path:
            rec["snippet"] = _read_text_snippet(path, q, snippet_bytes)

        if dedup:
            prev = best_by_title.get(title)
            if prev is None or score > prev.get("score", 0.0):
                best_by_title[title] = rec
        else:
            items.append(rec)

    if dedup:
        items = list(best_by_title.values())

    if rerank:
        for it in items:
            ov = _token_overlap(it.get("snippet", "") or "", tokens)
            it["_ov"] = ov
            it["_rs"] = it["score"] + 0.05 * ov
        items.sort(key=lambda x: (x["_ov"], x["_rs"]), reverse=True)
        for it in items:
            it.pop("_ov", None); it.pop("_rs", None)

    out: Dict = {"ok": True, "results": items[:k], "total": len(items)}
    if debug:
        out["debug"] = {
            "query_tokens": tokens,
            "raw_count": len(raw),
            "dedup": dedup,
            "rerank": rerank,
            "with_snippets": with_snippets,
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
    return out

@router.post("/knowledge/search_semantic_v2", operation_id="knowledge_search_semantic_v2")
def search_semantic_v2(req: SearchReq):
    return search_semantic_v2_local(
        q=req.q,
        k=req.k,
        dedup=req.dedup,
        with_snippets=req.with_snippets,
        rerank=req.rerank,
        snippet_bytes=req.snippet_bytes,
        debug=req.debug,
    )
