from __future__ import annotations
from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional

# Speicherort für Outlines
DATA_DIR = Path("data/outlines")
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------- Hilfen ----------
def _slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-_]+", "", s)
    return s or "untitled"


def _file_path(customer_name: str, project_title: str) -> Path:
    return DATA_DIR / f"{_slug(customer_name)}__{_slug(project_title)}.json"


def _normalize_agenda_item(a: Any) -> Dict[str, Any]:
    """Akzeptiert Dict oder Pydantic-Objekt und normiert auf {topic:str, subtopics:list[str]}"""
    if isinstance(a, dict):
        topic = a.get("topic", "")
        subs = a.get("subtopics", []) or []
    else:
        topic = getattr(a, "topic", "")
        subs = getattr(a, "subtopics", []) or []
    # Falls subtopics als Nicht-Liste kommt, konvertieren
    if not isinstance(subs, list):
        subs = [str(subs)]
    subs = [str(x) for x in subs]
    return {"topic": str(topic), "subtopics": subs}


# ---------- Persistenz ----------
def save_outline(customer_name: str, project_title: str, agenda: List[Dict[str, Any]]) -> None:
    """Speichert eine Outline-Datei im JSON-Format."""
    items = [_normalize_agenda_item(a) for a in (agenda or [])]
    fp = _file_path(customer_name, project_title)
    fp.parent.mkdir(parents=True, exist_ok=True)
    with fp.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "customer_name": customer_name,
                "project_title": project_title,
                "agenda": items,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def load_outline(customer_name: str, project_title: str) -> List[Dict[str, Any]]:
    """Lädt eine Outline. Gibt eine Liste von {topic, subtopics} zurück oder []."""
    fp = _file_path(customer_name, project_title)
    if not fp.exists():
        return []
    try:
        with fp.open("r", encoding="utf-8") as f:
            data = json.load(f)
        agenda = data.get("agenda", [])
        return [_normalize_agenda_item(a) for a in agenda]
    except Exception:
        # Falls Datei korrupt ist: leer zurückgeben
        return []


# ---------- Zählen & Auffüllen ----------
def count_slides(items: List[Any]) -> int:
    """
    Zählt Folien konservativ: 1 pro Topic + 1 je Subtopic.
    (Passt gut für „min_slides“-Budgetierung.)
    """
    total = 0
    for a in items or []:
        na = _normalize_agenda_item(a)
        total += 1  # Topic
        total += len(na["subtopics"])  # Subtopics
    return total


def pad_to_min_slides(items: List[Any], target: int) -> int:
    """
    Füllt die Agenda „in place“ auf, bis mindestens 'target' Folien erreicht sind.
    Strategie: Subtopics unter dem letzten Topic hinzufügen.
    Gibt die Anzahl der hinzugefügten Folien zurück.
    """
    # In-place Normalisierung
    for i in range(len(items)):
        items[i] = _normalize_agenda_item(items[i])

    # Falls leer: Dummy-Topic anlegen
    if not items:
        items.append({"topic": "Weitere Details", "subtopics": []})

    added = 0
    while count_slides(items) < target:
        items[-1]["subtopics"].append(f"Zusatzpunkt {added+1}")
        added += 1
    return added


# ---------- Agenda-Vorschlag ----------
def suggest_agenda(brief: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Versucht zuerst, via LLM eine Agenda zu holen; bei Fehlern fällt sie
    auf eine solide Default-Agenda zurück.
    """
    # Versuch mit vorhandenem LLM-Client (optional)
    try:
        from services.llm import LLMClient  # type: ignore
        llm = LLMClient()
        sys = (
            "Du erstellst eine Agenda für eine Strategie-Präsentation. "
            "Antworte NUR als JSON mit dem Feld 'agenda' = Liste von Objekten: "
            "[{\"topic\": str, \"subtopics\": [str,...]}, ...]. "
            "Keine Fließtexte, keine Erklärungen, nur JSON."
        )
        user = json.dumps(
            {
                "customer_name": brief.get("customer_name"),
                "project_title": brief.get("project_title"),
                "scope": brief.get("scope"),
                "market": brief.get("market"),
                "region": brief.get("region"),
                "channels": brief.get("channels"),
                "min_slides": brief.get("min_slides", 25),
            },
            ensure_ascii=False,
        )
        data = llm.chat_json(system=sys, user=user, temperature=0.2)
        # Erwartet { "agenda": [...] }
        if isinstance(data, dict) and isinstance(data.get("agenda"), list):
            return [_normalize_agenda_item(a) for a in data["agenda"]]
    except Exception:
        # LLM nicht verfügbar oder Antwort nicht JSON → Fallback unten
        pass

    # Robuster Fallback ohne LLM
    scope = brief.get("scope") or "Marketingstrategie & Social Media"
    market = brief.get("market") or "Allgemein"
    region = brief.get("region") or "DACH"

    fallback = [
        {"topic": "Executive Summary", "subtopics": ["Kernaussagen"]},
        {"topic": "Zielgruppe", "subtopics": ["Personas", "Needs & Barrieren"]},
        {"topic": "Marktanalyse", "subtopics": [f"Trends im {market}", f"Wettbewerb ({region})"]},
        {"topic": "Marketingstrategie", "subtopics": ["Positionierung", "Wertversprechen"]},
        {"topic": "Social Media Strategie", "subtopics": ["Kanäle & Content", "Paid/Organic-Rollen"]},
        {"topic": "Kanalintegration", "subtopics": ["Always-on & Kampagne", "Budgetrahmen"]},
        {"topic": "Umsetzung & Abläufe", "subtopics": ["Roadmap", "Rollen & Prozesse"]},
        {"topic": "Performance-Monitoring & Evaluation", "subtopics": ["KPIs", "Messplan"]},
    ]
    return fallback
