from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


CRITIC_DIR = Path("data/critic")
CRITIC_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_report(report: dict) -> Path:
    ts = int(time.time())
    name = f"critic-{ts}.json"
    out = CRITIC_DIR / name
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _critique_strategy(data: dict) -> dict:
    score = 100
    issues: List[str] = []
    suggestions: List[str] = []

    title = data.get("title")
    if not title:
        score -= 20
        issues.append("Strategie hat keinen Titel.")
        suggestions.append("Setze einen klaren, kundengerichteten Titel, z.B. 'KI-Rollout 2026 – Change & Enablement'.")

    slides = data.get("slides") or []
    if len(slides) < 5:
        score -= 10
        issues.append(f"Zu wenige Slides: {len(slides)} gefunden.")
        suggestions.append("Füge Agenda-/Intro-/Recap-Slides hinzu oder splitte große Inhalte auf mehrere Folien.")

    goals = data.get("goals") or []
    if not goals:
        score -= 5
        issues.append("Keine Ziele (goals) definiert.")
        suggestions.append("Lege 3–5 Ziele fest, z.B. 'Awareness', 'Enablement', 'Pilotvorhaben', 'Change-Kommunikation'.")

    core_messages = data.get("core_messages") or []
    if not core_messages:
        score -= 5
        issues.append("Keine Kernbotschaften (core_messages) definiert.")
        suggestions.append("Formuliere 3 Kernbotschaften, die in Slides wiederkehren sollen.")

    status = data.get("status")
    if status not in ("approved", "generated"):
        issues.append(f"Status ist '{status}', nicht 'approved' oder 'generated'.")
        suggestions.append("Prüfe die Strategie manuell und setze sie danach auf 'approved'.")

    # mini-metadata
    return {
        "ok": True,
        "kind": "strategy",
        "score": max(score, 0),
        "issues": issues,
        "suggestions": suggestions,
    }


def _critique_content(data: dict) -> dict:
    score = 100
    issues: List[str] = []
    suggestions: List[str] = []

    title = data.get("title")
    if not title:
        score -= 15
        issues.append("Content hat keinen Titel.")
        suggestions.append("Setze einen Titel, der Kanal + Thema enthält, z.B. 'LinkedIn: KI in der Industrie'.")

    outline = data.get("outline") or {}
    sections = outline.get("sections") if isinstance(outline, dict) else []
    if not sections:
        score -= 10
        issues.append("Kein Outline bzw. keine sections vorhanden.")
        suggestions.append("Lege ein Outline an: ['Hook', 'Body', 'CTA'].")

    facts = data.get("facts") or []
    if not facts:
        score -= 5
        issues.append("Keine Facts/Assets angegeben (CTR, Channel, Persona, etc.).")
        suggestions.append("Mindestens 1–2 relevante Facts hinzufügen, z.B. Zielkanal, CTA, KPI.")

    ctype = data.get("content_type")
    if not ctype:
        issues.append("Kein content_type gesetzt.")
        suggestions.append("Setze content_type (z.B. 'linkedin_post', 'newsletter', 'case_study').")

    return {
        "ok": True,
        "kind": "content",
        "score": max(score, 0),
        "issues": issues,
        "suggestions": suggestions,
    }


def run(target_type: str, name: str) -> dict:
    """
    target_type: strategy | content
    name: z.B. strategy-1762111001.json oder content-1762109407.json
    """
    if target_type == "strategy":
        path = Path("data/strategies") / name
        data = _load_json(path)
        if data is None:
            return {"ok": False, "error": f"strategy json not found: {path}"}
        report = _critique_strategy(data)
        report["target_type"] = "strategy"
        report["target_name"] = name
        out = _save_report(report)
        report["report_path"] = str(out)
        return report

    if target_type == "content":
        path = Path("data/content") / name
        data = _load_json(path)
        if data is None:
            return {"ok": False, "error": f"content json not found: {path}"}
        report = _critique_content(data)
        report["target_type"] = "content"
        report["target_name"] = name
        out = _save_report(report)
        report["report_path"] = str(out)
        return report

    return {"ok": False, "error": f"unsupported target_type: {target_type}"}


def list_reports() -> list[dict]:
    items: list[dict] = []
    for p in sorted(CRITIC_DIR.glob("critic-*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_path"] = str(p)
            items.append(data)
        except Exception:
            continue
    return items
