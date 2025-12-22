from __future__ import annotations
from typing import List
import re

NEGATIVE_TERMS = re.compile(r"(lorem ipsum|blindtext|template|zwischenfolie|agenda|placeholder)", re.I)

SYNONYMS = {
    "Kanäle": ["channels","Touchpoints","Paid Owned Earned"],
    "Zielgruppe": ["Audience","Buyer Persona","ICP","Personas"],
    "Brand": ["Marke","Positionierung","Narrative"],
    "KPIs": ["Metrics","Measurement"],
    "Roadmap": ["Plan","Zeitplan","Timeline"],
    "Budget": ["Media Plan","Mediasplit","Spend"],
}

def rewrite_query(topic: str, subtopic: str, base: str) -> str:
    extra = []
    for k,v in SYNONYMS.items():
        if k.lower() in (topic.lower()+" "+subtopic.lower()):
            extra += v
    if extra:
        base += " · " + " ".join(extra[:6])
    return base

def filter_bad(texts: List[str]) -> List[str]:
    out=[]
    for t in texts:
        if NEGATIVE_TERMS.search(t): 
            continue
        if len(t) < 60: 
            continue
        out.append(t)
    return out
