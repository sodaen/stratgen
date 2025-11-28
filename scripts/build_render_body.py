# -*- coding: utf-8 -*-
import json, sys, time
from pathlib import Path

def load_json(p:Path|None, fallback=None):
    if p and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return fallback

def dedupe_rag(title:str)->str:
    # "… (RAG) (RAG)" -> nur einmal
    while " (RAG) (RAG)" in title:
        title = title.replace(" (RAG) (RAG)", " (RAG)")
    return title

def bullets_from_manifest(manifest:dict, limit:int=6)->list[str]:
    bullets=[]
    # Charts mit alt_text bevorzugen
    for ch in manifest.get("charts", []) or []:
        t = (ch.get("alt_text") or "").strip()
        if t: bullets.append(t)
    # Falls leer: aus facts aggregieren (zwei Perioden vergleichen)
    if not bullets:
        facts = manifest.get("facts", [])
        by_metric={}
        for f in facts:
            m=f.get("metric"); v=f.get("value"); p=f.get("period_start")
            if m and p is not None and v is not None:
                by_metric.setdefault(m,[]).append((p,v))
        for m,arr in by_metric.items():
            if len(arr)>=2:
                arr=sorted(arr,key=lambda x:str(x[0]))
                a,b = arr[0][1], arr[-1][1]
                if a==0: continue
                delta = (b-a)/abs(a)*100.0
                bullets.append(f"{m.upper()}: {'↑' if delta>=0 else '↓'} {abs(delta):.1f}% ({a} → {b})")
    return bullets[:limit]

def main(args):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=False, default="")
    ap.add_argument("--plan-file", required=True, help="JSON file containing compose plan array")
    ap.add_argument("--manifest", default="data/manifest.json")
    ns=ap.parse_args(args)

    title = dedupe_rag(ns.title)
    out = ns.out or f"data/exports/deck-{time.strftime('%Y%m%d-%H%M%S')}.pptx"

    plan = load_json(Path(ns.plan_file), [])
    manifest = load_json(Path(ns.manifest), {})

    bullets = bullets_from_manifest(manifest, limit=6)
    if bullets:
        plan = list(plan) + [{
            "kind": "insights",
            "layout_hint": "Title and Content",
            "title": "Data Highlights",
            "bullets": bullets
        }]

    rb = {"title": title, "out_path": out, "plan": plan}
    sys.stdout.write(json.dumps(rb, ensure_ascii=False, separators=(",",":")))
if __name__=="__main__":
    main(sys.argv[1:])
