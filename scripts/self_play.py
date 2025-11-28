#!/usr/bin/env python
from __future__ import annotations
import os, json, time, random, string, requests

API = os.environ.get("API", "http://127.0.0.1:8001")
KEY = os.environ.get("KEY", "dev")

def _rand(n=6):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

def create_and_play(topic="Auto-Gen Strategy"):
    # 1) Save
    payload = {
        "customer_name": f"SelfPlayCo-{_rand()}",
        "topic": topic,
        "outline": {"title": "Deck", "sections":[
            {"title":"Ziele","bullets":["Awareness","Leads"]},
            {"title":"Plan","bullets":["T1 Kampagne","T2 Launch"]}
        ]}
    }
    r = requests.post(f"{API}/projects/save", headers={"X-API-Key": KEY}, json=payload, timeout=30)
    r.raise_for_status()
    pid = r.json()["project"]["id"]

    # 2) Generate (mit Modulen)
    requests.post(f"{API}/projects/{pid}/generate", headers={"X-API-Key": KEY},
                  json={"modules":["kpis","roadmap","executive summary"]}, timeout=60)

    # 3) Review
    rr = requests.post(f"{API}/projects/{pid}/review", headers={"X-API-Key": KEY}, timeout=30)
    rr.raise_for_status()
    review = rr.json()["review"]

    # 4) (optional) Export
    requests.post(f"{API}/projects/{pid}/export2", headers={"X-API-Key": KEY}, params={"template":"brand"}, timeout=120)

    return {"project_id": pid, "review": review}

def main(rounds=3):
    out = []
    for i in range(rounds):
        res = create_and_play(topic=f"Auto-Strategy Round {i+1}")
        out.append(res)
        time.sleep(1)
    print(json.dumps({"ok": True, "runs": out}, ensure_ascii=False))

if __name__ == "__main__":
    main(int(os.environ.get("ROUNDS","3")))
