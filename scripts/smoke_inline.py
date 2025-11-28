# -*- coding: utf-8 -*-
from __future__ import annotations
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)
headers = {"X-API-Key": "dev"}

# 1) save
payload = {
    "customer_name": "Acme GmbH",
    "topic": "Demo",
    "outline": {
        "title": "Demo",
        "subtitle": "Kurz",
        "sections": [{"title": "One", "bullets": ["A", "B"]}],
    },
}
r = client.post("/projects/save", json=payload, headers=headers)
assert r.status_code == 200, r.text
pid = r.json()["project"]["id"]
print("[smoke] saved:", pid)

# 2) preview
r = client.post(f"/projects/{pid}/preview", json={"style":"brand","width":800,"height":450}, headers=headers)
assert r.status_code == 200, r.text
assert r.headers.get("content-type","").startswith("image/png")
print("[smoke] preview: OK")

# 3) export
r = client.post(f"/projects/{pid}/export", json={"style":"brand","filename":"proj_export.pptx"}, headers=headers)
assert r.status_code == 200, r.text
assert r.headers.get("content-type","").startswith("application/vnd.openxmlformats-officedocument.presentationml.presentation")
print("[smoke] export: OK")

# 4) health
r = client.get("/health")
assert r.status_code == 200, r.text
j = r.json()
assert j.get("status") == "ok"
print("[smoke] health:", j["styles"])
