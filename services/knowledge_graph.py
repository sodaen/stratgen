from __future__ import annotations
from typing import Dict, Any, List, Tuple
from pathlib import Path
import json, time

GRAPH_PATH = Path("data/graph.json")

def _load() -> Dict[str, Any]:
    if GRAPH_PATH.exists():
        try: return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
        except Exception: return {"nodes":{}, "edges":[]}
    return {"nodes":{}, "edges":[]}

def _save(g: Dict[str, Any]) -> None:
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_PATH.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")

def upsert_nodes(nodes: List[Dict[str, Any]]) -> int:
    g = _load()
    cnt = 0
    for n in nodes:
        nid = str(n.get("id") or n.get("name") or f"n{int(time.time()*1000)}")
        n = {"id": nid, **n}
        g["nodes"][nid] = n
        cnt += 1
    _save(g)
    return cnt

def upsert_edges(edges: List[Tuple[str,str,str]]) -> int:
    g = _load()
    s = set(tuple(e) for e in g.get("edges", []))
    added = 0
    for u,v,label in edges:
        tup = (str(u), str(v), str(label))
        if tup not in s:
            g["edges"].append(list(tup))
            s.add(tup)
            added += 1
    _save(g)
    return added

def search(query: str, limit: int = 20) -> Dict[str, Any]:
    q = (query or "").strip().lower()
    g = _load()
    matches = []
    for nid, n in g.get("nodes", {}).items():
        blob = json.dumps(n, ensure_ascii=False).lower()
        if q in blob:
            matches.append(n)
            if len(matches) >= limit: break
    return {"ok": True, "count": len(matches), "items": matches}

def stats() -> Dict[str, Any]:
    g = _load()
    return {"ok": True, "nodes": len(g.get("nodes", {})), "edges": len(g.get("edges", []))}
