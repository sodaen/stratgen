import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import os, json, requests
API = os.environ.get("API","http://127.0.0.1:8001")
KEY = os.environ.get("KEY","dev")
PASSES = int(os.environ.get("PASSES","3"))

resp = requests.post(f"{API}/projects/save", headers={"X-API-Key":KEY}, json={
  "customer_name":"AutoTuneCo",
  "topic":"AutoTune",
  "outline":{"title":"Deck","sections":[{"title":"Ziele"},{"title":"Plan"}]}
})
pid = resp.json()["project"]["id"]
requests.post(f"{API}/projects/{pid}/generate", headers={"X-API-Key":KEY})
r = requests.post(f"{API}/projects/{pid}/autotune", headers={"X-API-Key":KEY}, params={"passes": PASSES})
try:
    out = r.json()
except Exception:
    out = {"ok": False, "status_code": r.status_code, "text": (r.text[:1000] if r.text else None)}
print(json.dumps(out, ensure_ascii=False, indent=2))
