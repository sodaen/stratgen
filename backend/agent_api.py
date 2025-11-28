from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import require_api_key
from backend.strategy_api import StrategyIn, strategy_gen

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    dependencies=[Depends(require_api_key)],
)

MISSIONS_DIR = Path("data/missions");    MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR  = Path("data/content");     CONTENT_DIR.mkdir(parents=True, exist_ok=True)
STRAT_DIR    = Path("data/strategies");  STRAT_DIR.mkdir(parents=True, exist_ok=True)
AGENT_RUN_DIR= Path("data/agent-runs");  AGENT_RUN_DIR.mkdir(parents=True, exist_ok=True)


class AgentRunIn(BaseModel):
    # Missions-Dateiname ("mission-...json")
    mission: str
    # diagnose | enrich | full
    mode: str = "diagnose"
    create_strategy: bool = True
    create_contents: bool = False
    llm_model: Optional[str] = None
    notes: Optional[str] = None


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} not found")
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/run")
def agent_run(body: AgentRunIn):
    ts = int(time.time())
    run_name = f"agent-run-{ts}.json"

    # 1) Mission laden
    mission_path = MISSIONS_DIR / body.mission
    mission = _load_json(mission_path)

    # 2) Sammellisten
    used_strategies: List[str] = list(mission.get("strategies", []))
    created_strategies: List[str] = []
    used_content: List[str] = list(mission.get("contents", []))

    # 3) Neue Strategie ggf. erzeugen
    new_strategy_result: dict[str, Any] | None = None
    if body.create_strategy and body.mode in ("enrich", "full"):
        briefing = mission.get("briefing") or f"Strategie für {mission.get('title')}"
        audience = mission.get("owner") or "Management"

        strat_in = StrategyIn(
            mission_id=None,  # Mission ist string-basiert
            briefing=briefing,
            size="medium",
            audience=audience,
            lang="de",
        )
        gen_resp = strategy_gen(strat_in)                # dict (dein Strategy-Endpoint)
        data = gen_resp.get("data", gen_resp)            # robust gegen unterschiedliche Response-Formen
        new_name = data["name"]                          # <- korrekt eingerückt
        created_strategies.append(new_name)

        # Mission sofort aktualisieren
        mission.setdefault("strategies", []).append(new_name)
        mission["updated_at"] = time.time()
        mission_path.write_text(
            json.dumps(mission, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Für die API-Antwort: lieber konsistent ein dict mit "ok"/"name"
        new_strategy_result = gen_resp if "ok" in gen_resp else {"ok": True, **data}

    # 4) Agent-Run-Report schreiben
    run_doc = {
        "name": run_name,
        "created_at": ts,
        "mission": body.mission,
        "mode": body.mode,
        "notes": body.notes,
        "used_strategies": used_strategies,
        "created_strategies": created_strategies,
        "used_content": used_content,
        "status": "done",
    }
    (AGENT_RUN_DIR / run_name).write_text(
        json.dumps(run_doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"ok": True, "run": run_doc, "new_strategy": new_strategy_result}


@router.get("/runs")
def agent_runs():
    items: List[dict[str, Any]] = []
    for p in sorted(AGENT_RUN_DIR.glob("agent-run-*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        items.append(
            {
                "name": data.get("name"),
                "mission": data.get("mission"),
                "mode": data.get("mode"),
                "created_at": data.get("created_at"),
                "status": data.get("status"),
            }
        )
    items.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
    return {"ok": True, "count": len(items), "items": items}
