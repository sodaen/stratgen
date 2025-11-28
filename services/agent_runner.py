# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional
import http.client
import json
import os
import time

HOST = os.environ.get("STRATGEN_HOST", "127.0.0.1")
PORT = int(os.environ.get("STRATGEN_PORT", "8011"))


def _req_json(method: str, path: str, body: Dict[str, Any] | None = None) -> Tuple[int, Dict[str, Any]]:
    conn = http.client.HTTPConnection(HOST, PORT, timeout=8)
    try:
        if method.upper() == "GET":
            conn.request("GET", path)
        else:
            payload = json.dumps(body or {})
            conn.request(method.upper(), path, body=payload, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        data_raw = resp.read().decode("utf-8") or "{}"
        try:
            data = json.loads(data_raw)
        except json.JSONDecodeError:
            data = {"raw": data_raw}
        return resp.status, data
    finally:
        conn.close()


def _guess_customer(mission: Dict[str, Any], assets: Optional[Dict[str, Any]]) -> str:
    if assets and assets.get("items"):
        for it in assets["items"]:
            cust = it.get("customer")
            if cust:
                return cust
    title = (mission.get("title") or "").lower()
    if "acme" in title:
        return "Acme GmbH"
    return "Unbekannter Kunde"


def dry_run(mission: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    assets: Optional[Dict[str, Any]] = None
    facts: Optional[Dict[str, Any]] = None
    results: List[Dict[str, Any]] = []

    for t in tasks:
        kind = t.get("kind")
        task_id = t.get("id")

        if kind == "collect_assets":
            status, data = _req_json("GET", "/assets/list")
            if status == 200:
                assets = data
            results.append({"task_id": task_id, "kind": kind, "status": status, "response": data})
            continue

        if kind == "extract_facts":
            status, data = _req_json("GET", "/assets/facts")
            if status == 200:
                facts = data
            results.append({"task_id": task_id, "kind": kind, "status": status, "response": data})
            continue

        if kind == "build_plan":
            payload: Dict[str, Any] = {
                "customer_name": _guess_customer(mission, assets),
                "topic": mission.get("title") or mission.get("goal") or "Strategie",
                "briefing": mission.get("goal") or "",
            }
            if facts and facts.get("items"):
                payload["facts"] = facts["items"][:50]
            status, data = _req_json("POST", "/planner/plan", payload)
            results.append({"task_id": task_id, "kind": kind, "status": status, "response": data})
            continue

        if kind == "compose_slides":
            status, data = _req_json(
                "POST",
                "/content/gen",
                {
                    "mission_id": mission.get("id"),
                    "topic": mission.get("title"),
                    "mode": "stub",
                },
            )
            if status == 404:
                status, data = _req_json("GET", "/content/list")
            results.append({"task_id": task_id, "kind": kind, "status": status, "response": data})
            continue

        if kind == "review_export":
            status, data = _req_json("GET", "/exports/list")
            if status == 404:
                status, data = _req_json("GET", "/export/list")
            results.append({"task_id": task_id, "kind": kind, "status": status, "response": data})
            continue

        results.append(
            {"task_id": task_id, "kind": kind, "status": 400, "response": {"msg": f"unknown task kind: {kind}"}}
        )

    return {
        "ok": True,
        "mission": {"id": mission.get("id"), "title": mission.get("title")},
        "results": results,
        "ran_at": int(time.time()),
    }
