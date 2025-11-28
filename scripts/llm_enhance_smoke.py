import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os, json, requests, random
API = os.environ.get("API","http://127.0.0.1:8001")
KEY = os.environ.get("KEY","dev")

topic = f"LLM Smoke {random.randint(1000,9999)}"
r = requests.post(f"{API}/projects/save", headers={"X-API-Key":KEY}, json={
  "customer_name":"LLMCo",
  "topic": topic,
  "outline":{"title":"Deck","sections":[{"title":"Ziele"},{"title":"Plan"}]}
})
pid = r.json()["project"]["id"]
requests.post(f"{API}/projects/{pid}/generate", headers={"X-API-Key":KEY})
print(json.dumps({"ok": True, "project_id": pid}, ensure_ascii=False))
