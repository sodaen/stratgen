#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, json, os, requests
from pathlib import Path

TOPICS = [
    "GTM für B2B SaaS in DACH",
    "Social-Media-Plan für FMCG-Launch",
    "Positionierung für KI-Produkt im Mittelstand",
    "Content-Strategie für B2C Fitness-App",
    "Employer Branding Kampagne Tech",
    "Leadgen-Kampagne für Consulting",
    "Markteintritt in Frankreich (B2B)",
    "Messaging für Cybersecurity-Lösung",
    "Produkt-Relaunch Premium-Kaffee",
    "Event-Marketing-Plan (Branche: MedTech)",
]

API = os.environ.get("API", "http://127.0.0.1:8001")

def score_topic(topic: str, use_knowledge: bool) -> int:
    """
    Sehr einfache Heuristik:
    - Basis: 8
    - Wenn use_knowledge=1 und /knowledge/search (semantic=1)  >=1 Treffer liefert: +1
    - Score wird auf 10 gedeckelt
    """
    base = 8
    if use_knowledge:
        try:
            r = requests.get(
                f"{API}/knowledge/search",
                params={"q": topic, "limit": 1, "semantic": 1},
                timeout=8,
            )
            if r.ok and r.json().get("results"):
                base += 1
        except Exception:
            pass
    return min(base, 10)

def write_json(rows, out_path: str):
    if not out_path:
        return
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--use_knowledge", type=int, default=0, help="1 = mit RAG-Heuristik")
    ap.add_argument("--out", type=str, default="", help="Pfad für JSON-Output")
    args = ap.parse_args()

    rows = [{"topic": t, "score": score_topic(t, bool(args.use_knowledge))} for t in TOPICS]
    write_json(rows, args.out)
    # zusätzlich auf STDOUT, damit man sofort was sieht
    print(json.dumps({"ok": True, "n": len(rows), "rows": rows}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
