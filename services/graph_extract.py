from __future__ import annotations
from typing import Dict, Any, Iterable, List, Tuple
import re, json

WORD = re.compile(r"\b[A-ZÄÖÜ][A-Za-z0-9ÄÖÜäöüß&\-]{2,}\b")
STOP = {"AND","THE","DAS","DER","DIE","UND","EIN","EINE","FÜR","MIT","VON","TO","IN","ON","AT","OR","VS","V/S"}

def extract_nodes_and_edges(features: Dict[str, Any]) -> tuple[list[dict], list[tuple[str,str,str]]]:
    """Nimmt extract_pptx_features()-Ergebnis und erzeugt einfache Knoten/Kanten."""
    nodes: set[str] = set()
    edges: set[tuple[str,str,str]] = set()

    # Kandidat: Deck-Titel als Hauptknoten
    deck_title = (features.get("deck") or {}).get("title")
    if deck_title:
        nodes.add(deck_title)

    def add_text(t: str):
        for m in WORD.findall(t or ""):
            w = m.strip().strip("-")
            if w.upper() in STOP: 
                continue
            if len(w) < 3: 
                continue
            nodes.add(w)

    for s in features.get("slides", []):
        if s.get("title"): add_text(s["title"])
        for b in s.get("bullets", []):
            add_text(b.get("text",""))
        for body in s.get("body", []):
            add_text(body)

        # primitive Pattern: "X vs Y" oder "X gegen Y" => competes
        blob = " ".join([s.get("title") or ""] + [b.get("text","") for b in s.get("bullets",[])])
        m = re.search(r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\-]{2,})\s+(?:vs\.?|gegen)\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\-]{2,})\b", blob, flags=re.I)
        if m:
            a,b = m.group(1), m.group(2)
            edges.add((a,b,"competes"))

    node_list = [{"id":n, "type":"entity"} for n in sorted(nodes)]
    edge_list = sorted(edges)
    return node_list, edge_list
