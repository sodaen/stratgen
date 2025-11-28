#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

BASE = os.environ.get("BASE", "http://127.0.0.1:8011")
USE_KNOW = os.environ.get("USE_KNOWLEDGE_SLIDES","0") == "1"

def _get(p): 
    return p if p is not None else {}

def _bul(x):
    if x is None: return []
    if isinstance(x, str): return [x.strip()] if x.strip() else []
    if isinstance(x, (list, tuple)): return [str(i).strip() for i in x if str(i).strip()]
    return []

def _http_json(url, data=None, timeout=10):
    try:
        if data is not None:
            data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def _synthesize_slide_plan(pj: dict):
    brief = _get(pj.get("brief"))
    outline = _get(pj.get("outline"))
    topic = pj.get("topic") or pj.get("title") or "Strategy Deck"
    customer = pj.get("customer_name") or ""

    sections = []

    # 1) Title/Agenda
    bullets_ag = []
    for sec in _bul([s.get("title") for s in outline.get("sections") or []]):
        bullets_ag.append(f"{sec}")
    sections.append({"title":"Agenda", "bullets": bullets_ag or ["Ziele", "Taktiken", "KPIs & Mix", "Risiken & Nächste Schritte"]})

    # 2) Ziele / Constraints
    goals = _bul(brief.get("goals"))
    constraints = _bul(brief.get("constraints"))
    if goals or constraints:
        left = goals or ["—"]
        right = constraints or ["—"]
        sections.append({"title":"Ziele & Rahmen", "cols":{"left":left, "right":right}})

    # 3) Outline-Sektionen als Bullets
    for sec in outline.get("sections") or []:
        t = sec.get("title") or "Abschnitt"
        bs = _bul(sec.get("bullets"))
        sections.append({"title": t, "bullets": bs})

    # 4) Knowledge-Slide (optional)
    if USE_KNOW:
        q = f"{topic} {customer}".strip()
        ans = _http_json(f"{BASE}/knowledge/answer", {"q": q, "customer": customer, "limit": 6}, timeout=12)
        hits = _get(ans).get("hits") or []
        kb = [h.get("text") or h.get("snippet") or "" for h in hits if (h.get("text") or h.get("snippet"))]
        if kb:
            sections.append({"title":"Wissen aus Knowledge", "bullets": kb[:8]})

    # 5) Personas/Messaging/Metrics/Media-Mix/Critique falls vorhanden
    if pj.get("personas"):
        sections.append({"title":"Zielgruppen (Personas)", "bullets":[f"{p.get('name')}: Ziele={', '.join(_bul(p.get('goals')))}; Pains={', '.join(_bul(p.get('pains')))}" for p in pj["personas"]][:8]})
    if pj.get("messaging"):
        sections.append({"title":"Messaging-Matrix", "bullets":[f"{m.get('persona')}: " + '; '.join(_bul(m.get('messages'))) for m in pj["messaging"]][:8]})
    if pj.get("metrics_plan"):
        sections.append({"title":"KPIs & Messung", "bullets":[f"{i.get('kpi')} → {i.get('target')} ({i.get('measurement')}, {i.get('cadence')})" for i in pj["metrics_plan"]][:8]})
    if pj.get("media_mix"):
        mm = pj["media_mix"]
        sections.append({"title":"Media-Mix", "bullets":[f"{k}: €{v}" for k,v in list(mm.items())[:10]]})
    if pj.get("critique"):
        cr = pj["critique"]
        for key in ("risks","assumptions","counterarguments"):
            vals = _bul(cr.get(key))
            if vals:
                sections.append({"title": key.capitalize(), "bullets": vals[:10]})

    # 6) Schluss / Next steps
    sections.append({"title":"Nächste Schritte", "bullets":["Validierung mit Sales","A/B-Test-Plan anlegen","Tracking-Plan prüfen","Content-Backlog priorisieren"]})

    return sections

def main():
    if len(sys.argv) < 2:
        print("usage: ensure_slide_plan.py <project_id>"); sys.exit(2)
    pid = sys.argv[1]
    pj_path = Path("data/projects")/pid/"project.json"
    if not pj_path.exists():
        print(f"not found: {pj_path}"); sys.exit(1)
    pj = json.loads(pj_path.read_text(encoding="utf-8"))

    meta = _get(pj.get("meta"))
    plan = (meta.get("slide_plan") or [])
    if not plan:
        plan = _synthesize_slide_plan(pj)
        meta["slide_plan"] = plan
        pj["meta"] = meta
        pj_path.write_text(json.dumps(pj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[ok] slide_plan geschrieben: {pj_path}")
    else:
        print("[ok] slide_plan bereits vorhanden (keine Änderung)")

if __name__ == "__main__":
    main()
