import time, os, json, requests, pathlib
API=os.environ.get("API","http://127.0.0.1:8001")
KN=pathlib.Path("data/knowledge")
def snapshot():
    items=[]
    for p in KN.rglob("*"):
        if p.is_file(): items.append((str(p), p.stat().st_mtime_ns))
    items.sort()
    return items

def scan():
    try:
        r=requests.post(f"{API}/knowledge/scan", timeout=30)
        print("[watch] scan:", r.status_code)
    except Exception as e:
        print("[watch] error:", e)

prev = snapshot()
print("[watch] baseline with", len(prev), "files")
while True:
    time.sleep(10)
    cur = snapshot()
    if cur != prev:
        print("[watch] change detected; triggering scan…")
        scan()
        prev = cur
