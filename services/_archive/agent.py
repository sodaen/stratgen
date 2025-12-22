from __future__ import annotations
import os, json, time, argparse, random
from typing import Dict, Any, List
from services import db as _db
import requests

API = os.environ.get("API", "http://127.0.0.1:8001")
KEY = os.environ.get("KEY", "dev")

def _h() -> Dict[str, str]:
    return {"X-API-Key": KEY}

def _post(path: str, **kw) -> Dict[str, Any]:
    r = _retryable(lambda: requests.post(f"{API}{path}", headers=_h(), what='POST'), **kw)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"ok": False, "status_code": r.status_code, "text": r.text[:1000]}

def _get(path: str, **kw) -> Dict[str, Any]:
    r = _retryable(lambda: requests.get(f"{API}{path}", headers=_h(), what='GET'), **kw)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"ok": False, "status_code": r.status_code, "text": r.text[:1000]}

def create_project(customer: str, topic: str) -> str:
    payload = {
        "customer_name": customer,
        "topic": topic,
        "outline": {"title":"Deck","sections":[{"title":"Ziele"},{"title":"Plan"}]}
    }
    resp = _post("/projects/save", json=payload)
    pid = resp.get("project", {}).get("id")
    if not pid:
        raise RuntimeError(f"save failed: {resp}")
    return pid

def generate(pid: str) -> Dict[str, Any]:
    return _post(f"/projects/{pid}/generate")

def review(pid: str) -> Dict[str, Any]:
    return _post(f"/projects/{pid}/review")

def autotune(pid: str, passes: int = 2) -> Dict[str, Any]:
    # Optional – falls Endpoint fehlt, sauber auffangen
    try:
        return _post(f"/projects/{pid}/autotune", params={"passes": passes})
    except requests.HTTPError as e:
        return {"ok": False, "error": f"autotune HTTPError: {e}"}

def run_once(use_autotune: bool = True) -> Dict[str, Any]:
    topic = f"Agent Run {random.randint(1000,9999)}"
    pid = create_project("AgentCo", topic)
    g = generate(pid)
    r = review(pid)
    out: Dict[str, Any] = {"ok": True, "project_id": pid, "generate": g, "review": r}
    if use_autotune:
        a = autotune(pid, passes=2)
        out["autotune"] = a
    return out

def run_loop(interval_sec: int = 60, use_autotune: bool = True):
    while True:
        try:
            res = run_once(use_autotune=use_autotune)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        time.sleep(interval_sec)

def main():
    ap = argparse.ArgumentParser(description="Heuristischer StratGen-Agent (lokal)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_once = sub.add_parser("once", help="einen Lauf (save→generate→review[→autotune])")
    ap_once.add_argument("--no-autotune", action="store_true")

    ap_loop = sub.add_parser("loop", help="Endlosschleife")
    ap_loop.add_argument("--interval", type=int, default=60)
    ap_loop.add_argument("--no-autotune", action="store_true")

    args = ap.parse_args()
    if args.cmd == "once":
        res = run_once(use_autotune=not args.no_autotune)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "loop":
        run_loop(interval_sec=args.interval, use_autotune=not args.no_autotune)

if __name__ == "__main__":
    main()


# sichere Hülle (für externe Aufrufer)
def run_once_safe():
    try:
        with _agent_lock():
            return run_once()
    except RuntimeError as e:
        # schon laufend
        return {"ok": False, "detail": str(e)}
    except Exception as e:
        try:
            # Fallback: Lauf ohne run_id kann hier nicht sauber beendet werden
            pass
        finally:
            return {"ok": False, "detail": f"agent error: {type(e).__name__}: {e}"}
