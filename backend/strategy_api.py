# -*- coding: utf-8 -*-
"""
StratGen – Strategy API
Echte LLM-Calls für SWOT, Porter's Five Forces und Strategie-Generierung.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("stratgen.strategy")

router = APIRouter(prefix="/strategy", tags=["strategy"])

STRAT_DIR = Path("data/strategies")
STRAT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# LLM HELPER
# ─────────────────────────────────────────────

def _ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

def _model() -> str:
    return os.getenv("LLM_MODEL", "mistral")

def _llm(prompt: str, max_tokens: int = 2000, json_mode: bool = False) -> str:
    """Zentraler LLM-Call gegen Ollama (mit OpenAI-Fallback)."""
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        try:
            payload: Dict[str, Any] = {
                "model": _model(),
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.7},
            }
            r = requests.post(
                f"{_ollama_host()}/api/generate",
                json=payload,
                timeout=120,
            )
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except Exception as e:
            log.warning("Ollama LLM call failed: %s", e)
            return ""

    if provider == "openai":
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            log.warning("OpenAI LLM call failed: %s", e)
            return ""

    return ""


def _rag_context(query: str, k: int = 5) -> str:
    """Holt RAG-Kontext aus der Knowledge Base."""
    try:
        base = os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")
        r = requests.get(
            f"{base}/knowledge/search_semantic",
            params={"q": query, "k": k},
            timeout=20,
        )
        if not r.ok:
            return ""
        hits = (
            r.json().get("_hits")
            or r.json().get("hits")
            or r.json().get("results")
            or []
        )
        snippets = []
        base_path = Path().resolve()
        for h in hits[:k]:
            path_str = h.get("path") or h.get("file") or ""
            if not path_str:
                continue
            p = Path(path_str)
            if not p.is_absolute():
                p = base_path / p
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                snippets.append(text.strip()[:600])
            except Exception:
                snippet = h.get("snippet") or h.get("text") or ""
                if snippet:
                    snippets.append(snippet[:600])
        return "\n\n---\n\n".join(snippets)
    except Exception as e:
        log.warning("RAG context failed: %s", e)
        return ""


def _parse_json_from_llm(text: str) -> Optional[Dict]:
    """Extrahiert JSON sicher aus LLM-Antwort."""
    if not text:
        return None
    # Direkt parsen
    try:
        return json.loads(text)
    except Exception:
        pass
    # JSON-Block aus Markdown
    for fence in ["```json", "```"]:
        if fence in text:
            try:
                start = text.index(fence) + len(fence)
                end = text.index("```", start)
                return json.loads(text[start:end].strip())
            except Exception:
                pass
    # Erste { ... } finden
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return None


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class StrategyIn(BaseModel):
    mission_id: Optional[int] = None
    mission_ref: Optional[str] = None
    briefing: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    size: str = "medium"
    audience: str = "Management"
    tone: Optional[str] = None
    lang: str = "de"
    title: Optional[str] = None
    context: Optional[List[str]] = None  # RAG-Kontext (vom Agent)


class SWOTRequest(BaseModel):
    briefing: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    lang: str = "de"
    use_rag: bool = True


class PorterRequest(BaseModel):
    briefing: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    lang: str = "de"
    use_rag: bool = True


# ─────────────────────────────────────────────
# SWOT ANALYSE
# ─────────────────────────────────────────────

@router.post("/swot")
def generate_swot(body: SWOTRequest):
    """
    Generiert eine vollständige SWOT-Analyse via LLM.
    Nutzt optional RAG-Kontext aus der Knowledge Base.
    """
    rag_ctx = ""
    if body.use_rag:
        query = f"SWOT {body.company_name or ''} {body.industry or ''} {body.briefing[:100]}"
        rag_ctx = _rag_context(query, k=4)

    lang_instruction = "Antworte auf Deutsch." if body.lang == "de" else "Answer in English."
    context_block = f"\n\nKontext aus Wissensdatenbank:\n{rag_ctx}" if rag_ctx else ""

    prompt = f"""Du bist ein erfahrener Strategieberater. Erstelle eine fundierte SWOT-Analyse.

Unternehmen: {body.company_name or 'Nicht angegeben'}
Branche: {body.industry or 'Nicht angegeben'}
Briefing: {body.briefing}{context_block}

{lang_instruction}

Gib NUR gültiges JSON zurück (kein Markdown, kein Text davor/danach):
{{
  "title": "SWOT-Analyse: <Unternehmensname>",
  "strengths": [
    {{"point": "Stärke 1", "detail": "Erläuterung mit konkretem Bezug zum Briefing"}},
    {{"point": "Stärke 2", "detail": "..."}},
    {{"point": "Stärke 3", "detail": "..."}},
    {{"point": "Stärke 4", "detail": "..."}}
  ],
  "weaknesses": [
    {{"point": "Schwäche 1", "detail": "..."}},
    {{"point": "Schwäche 2", "detail": "..."}},
    {{"point": "Schwäche 3", "detail": "..."}}
  ],
  "opportunities": [
    {{"point": "Chance 1", "detail": "..."}},
    {{"point": "Chance 2", "detail": "..."}},
    {{"point": "Chance 3", "detail": "..."}}
  ],
  "threats": [
    {{"point": "Risiko 1", "detail": "..."}},
    {{"point": "Risiko 2", "detail": "..."}},
    {{"point": "Risiko 3", "detail": "..."}}
  ],
  "strategic_recommendations": [
    "Empfehlung 1 basierend auf SO-Kombination",
    "Empfehlung 2 basierend auf WT-Abwehr",
    "Empfehlung 3 für Quick Wins"
  ],
  "summary": "2-3 Sätze Gesamtfazit"
}}"""

    raw = _llm(prompt, max_tokens=2000)
    parsed = _parse_json_from_llm(raw)

    if not parsed:
        log.warning("SWOT LLM parse failed, using fallback structure")
        parsed = {
            "title": f"SWOT-Analyse: {body.company_name or 'Unternehmen'}",
            "strengths": [{"point": "LLM nicht verfügbar", "detail": "Bitte Ollama starten: ollama run mistral"}],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "strategic_recommendations": ["Ollama/LLM konfigurieren und erneut generieren"],
            "summary": "LLM nicht erreichbar – bitte Backend-Konfiguration prüfen.",
            "_fallback": True,
        }

    # Slides für PPTX-Export vorbereiten
    slides = _swot_to_slides(parsed, body.lang)

    result = {
        "ok": True,
        "type": "swot",
        "swot": parsed,
        "slides": slides,
        "rag_used": bool(rag_ctx),
        "model": _model(),
        "generated_at": time.time(),
    }

    # Persistieren
    name = f"swot-{body.company_name or 'unknown'}-{int(time.time())}.json".replace(" ", "_")
    (STRAT_DIR / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["name"] = name

    return result


def _swot_to_slides(swot: Dict, lang: str = "de") -> List[Dict]:
    """Konvertiert SWOT-Daten in Slide-Format."""
    label = {"de": {"s": "Stärken", "w": "Schwächen", "o": "Chancen", "t": "Risiken"},
             "en": {"s": "Strengths", "w": "Weaknesses", "o": "Opportunities", "t": "Threats"}}
    lbl = label.get(lang, label["de"])

    slides = [
        {
            "type": "title",
            "title": swot.get("title", "SWOT-Analyse"),
            "bullets": [],
            "layout": "title-only",
        },
        {
            "type": "content",
            "title": lbl["s"],
            "bullets": [f"{s['point']}: {s['detail']}" for s in swot.get("strengths", [])],
            "layout": "title-bullets",
            "color_theme": "green",
        },
        {
            "type": "content",
            "title": lbl["w"],
            "bullets": [f"{s['point']}: {s['detail']}" for s in swot.get("weaknesses", [])],
            "layout": "title-bullets",
            "color_theme": "red",
        },
        {
            "type": "content",
            "title": lbl["o"],
            "bullets": [f"{s['point']}: {s['detail']}" for s in swot.get("opportunities", [])],
            "layout": "title-bullets",
            "color_theme": "blue",
        },
        {
            "type": "content",
            "title": lbl["t"],
            "bullets": [f"{s['point']}: {s['detail']}" for s in swot.get("threats", [])],
            "layout": "title-bullets",
            "color_theme": "orange",
        },
        {
            "type": "bullets",
            "title": "Strategische Empfehlungen" if lang == "de" else "Strategic Recommendations",
            "bullets": swot.get("strategic_recommendations", []),
            "layout": "title-bullets",
        },
    ]
    return slides


# ─────────────────────────────────────────────
# PORTER'S FIVE FORCES
# ─────────────────────────────────────────────

@router.post("/porter")
def generate_porter(body: PorterRequest):
    """
    Analysiert die fünf Wettbewerbskräfte nach Porter via LLM.
    """
    rag_ctx = ""
    if body.use_rag:
        query = f"Wettbewerb Markt {body.company_name or ''} {body.industry or ''} Porter"
        rag_ctx = _rag_context(query, k=4)

    lang_instruction = "Antworte auf Deutsch." if body.lang == "de" else "Answer in English."
    context_block = f"\n\nKontext aus Wissensdatenbank:\n{rag_ctx}" if rag_ctx else ""

    prompt = f"""Du bist ein erfahrener Strategieberater. Analysiere die Wettbewerbssituation nach Porter's Five Forces.

Unternehmen: {body.company_name or 'Nicht angegeben'}
Branche: {body.industry or 'Nicht angegeben'}
Briefing: {body.briefing}{context_block}

{lang_instruction}

Gib NUR gültiges JSON zurück:
{{
  "title": "Porter's Five Forces: <Branche/Unternehmen>",
  "forces": {{
    "rivalry": {{
      "name": "Wettbewerbsintensität",
      "intensity": "hoch|mittel|niedrig",
      "score": 7,
      "factors": ["Faktor 1", "Faktor 2", "Faktor 3"],
      "assessment": "Bewertung in 2 Sätzen"
    }},
    "new_entrants": {{
      "name": "Bedrohung durch neue Anbieter",
      "intensity": "hoch|mittel|niedrig",
      "score": 5,
      "factors": ["Faktor 1", "Faktor 2"],
      "assessment": "Bewertung"
    }},
    "substitutes": {{
      "name": "Bedrohung durch Substitute",
      "intensity": "hoch|mittel|niedrig",
      "score": 4,
      "factors": ["Faktor 1", "Faktor 2"],
      "assessment": "Bewertung"
    }},
    "buyer_power": {{
      "name": "Verhandlungsmacht der Kunden",
      "intensity": "hoch|mittel|niedrig",
      "score": 6,
      "factors": ["Faktor 1", "Faktor 2"],
      "assessment": "Bewertung"
    }},
    "supplier_power": {{
      "name": "Verhandlungsmacht der Lieferanten",
      "intensity": "hoch|mittel|niedrig",
      "score": 3,
      "factors": ["Faktor 1", "Faktor 2"],
      "assessment": "Bewertung"
    }}
  }},
  "overall_attractiveness": "hoch|mittel|niedrig",
  "strategic_implications": [
    "Implikation 1",
    "Implikation 2",
    "Implikation 3"
  ],
  "summary": "2-3 Sätze Gesamtfazit zur Branchenattraktivität"
}}"""

    raw = _llm(prompt, max_tokens=2000)
    parsed = _parse_json_from_llm(raw)

    if not parsed:
        log.warning("Porter LLM parse failed, using fallback")
        parsed = {
            "title": f"Porter's Five Forces: {body.industry or 'Branche'}",
            "forces": {
                "rivalry": {"name": "Wettbewerbsintensität", "intensity": "unbekannt", "score": 0,
                            "factors": ["LLM nicht verfügbar"], "assessment": "Bitte Ollama starten"},
                "new_entrants": {"name": "Neue Anbieter", "intensity": "unbekannt", "score": 0,
                                  "factors": [], "assessment": ""},
                "substitutes": {"name": "Substitute", "intensity": "unbekannt", "score": 0,
                                 "factors": [], "assessment": ""},
                "buyer_power": {"name": "Kundenmacht", "intensity": "unbekannt", "score": 0,
                                 "factors": [], "assessment": ""},
                "supplier_power": {"name": "Lieferantenmacht", "intensity": "unbekannt", "score": 0,
                                    "factors": [], "assessment": ""},
            },
            "overall_attractiveness": "unbekannt",
            "strategic_implications": ["LLM konfigurieren und erneut generieren"],
            "summary": "LLM nicht erreichbar.",
            "_fallback": True,
        }

    slides = _porter_to_slides(parsed)

    result = {
        "ok": True,
        "type": "porter",
        "porter": parsed,
        "slides": slides,
        "rag_used": bool(rag_ctx),
        "model": _model(),
        "generated_at": time.time(),
    }

    name = f"porter-{body.company_name or 'unknown'}-{int(time.time())}.json".replace(" ", "_")
    (STRAT_DIR / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["name"] = name

    return result


def _porter_to_slides(porter: Dict) -> List[Dict]:
    forces = porter.get("forces", {})
    force_list = []
    for key, force in forces.items():
        intensity = force.get("intensity", "")
        score = force.get("score", 0)
        factors = force.get("factors", [])
        force_list.append(
            f"{force.get('name', key)} ({intensity}, {score}/10): " + "; ".join(factors[:2])
        )

    slides = [
        {
            "type": "title",
            "title": porter.get("title", "Porter's Five Forces"),
            "bullets": [],
            "layout": "title-only",
        },
        {
            "type": "content",
            "title": "Five Forces Übersicht",
            "bullets": force_list,
            "layout": "title-bullets",
        },
    ]

    # Eine Slide pro Force
    for key, force in forces.items():
        slides.append({
            "type": "content",
            "title": force.get("name", key),
            "bullets": [
                f"Intensität: {force.get('intensity', '')} ({force.get('score', 0)}/10)",
                *force.get("factors", []),
                f"Bewertung: {force.get('assessment', '')}",
            ],
            "layout": "title-bullets",
        })

    slides.append({
        "type": "bullets",
        "title": "Strategische Implikationen",
        "bullets": porter.get("strategic_implications", []),
        "notes": porter.get("summary", ""),
        "layout": "title-bullets",
    })

    return slides


# ─────────────────────────────────────────────
# HAUPT-STRATEGIE GENERIERUNG
# ─────────────────────────────────────────────

@router.post("/gen")
def strategy_gen(body: StrategyIn):
    """
    Generiert eine vollständige Strategie-Präsentation via LLM.
    Nutzt RAG-Kontext wenn vorhanden.
    """
    # RAG-Kontext aufbauen
    rag_ctx = ""
    if body.context:
        rag_ctx = "\n\n".join(body.context[:5])
    else:
        query = f"{body.company_name or ''} {body.briefing[:150]}"
        rag_ctx = _rag_context(query, k=5)

    lang_instruction = "Antworte auf Deutsch." if body.lang == "de" else "Answer in English."
    context_block = f"\n\nRelevanter Kontext:\n{rag_ctx}" if rag_ctx else ""

    n_slides = {"small": 8, "medium": 14, "large": 22}.get(body.size, 14)

    prompt = f"""Du bist ein erfahrener Strategieberater und Präsentationsexperte.
Erstelle eine strukturierte Strategie-Präsentation.

Kunde/Unternehmen: {body.company_name or 'Nicht angegeben'}
Branche: {body.industry or 'Nicht angegeben'}
Briefing: {body.briefing}
Zielgruppe: {body.audience}
Umfang: {n_slides} Slides
Ton: {body.tone or 'professionell'}{context_block}

{lang_instruction}

Gib NUR gültiges JSON zurück:
{{
  "title": "Präsentationstitel",
  "subtitle": "Unterzeile",
  "executive_summary": "3-4 Sätze Zusammenfassung",
  "strategic_goals": ["Ziel 1", "Ziel 2", "Ziel 3"],
  "core_messages": ["Kernbotschaft 1", "Kernbotschaft 2", "Kernbotschaft 3"],
  "slides": [
    {{
      "type": "title",
      "title": "Titel-Slide Titel",
      "bullets": [],
      "notes": "Speaker Notes"
    }},
    {{
      "type": "agenda",
      "title": "Agenda",
      "bullets": ["Punkt 1", "Punkt 2", "Punkt 3", "Punkt 4"],
      "notes": ""
    }},
    {{
      "type": "content",
      "title": "Ausgangslage",
      "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"],
      "notes": "Speaker Notes"
    }}
  ]
}}

Erstelle genau {n_slides} Slides. Nutze diese Typen: title, agenda, content, bullets, chart, quote, cta.
Jeder Slide muss title + bullets (als Liste) haben. Letzte Slide ist immer type=cta (Nächste Schritte)."""

    raw = _llm(prompt, max_tokens=3000)
    parsed = _parse_json_from_llm(raw)

    if not parsed or not parsed.get("slides"):
        log.warning("Strategy gen LLM parse failed")
        parsed = {
            "title": body.title or "Strategie-Präsentation",
            "subtitle": body.briefing[:80],
            "executive_summary": "LLM nicht verfügbar – bitte Ollama konfigurieren.",
            "strategic_goals": ["LLM starten: ollama run mistral"],
            "core_messages": ["Backend konfigurieren"],
            "slides": [
                {"type": "title", "title": body.title or "Strategie-Präsentation",
                 "bullets": [], "notes": ""},
                {"type": "content", "title": "LLM nicht verfügbar",
                 "bullets": ["Ollama starten: ollama run mistral",
                             "LLM_PROVIDER und LLM_MODEL in .env prüfen"],
                 "notes": ""},
            ],
            "_fallback": True,
        }

    data = {
        "name": f"strategy-{int(time.time())}.json",
        "mission_id": body.mission_id,
        "mission_ref": body.mission_ref,
        "briefing": body.briefing,
        "company_name": body.company_name,
        "industry": body.industry,
        "size": body.size,
        "audience": body.audience,
        "tone": body.tone,
        "lang": body.lang,
        "created_at": time.time(),
        "updated_at": time.time(),
        "title": parsed.get("title") or body.title or "Strategie",
        "subtitle": parsed.get("subtitle", ""),
        "executive_summary": parsed.get("executive_summary", ""),
        "goals": parsed.get("strategic_goals", []),
        "core_messages": parsed.get("core_messages", []),
        "slides": parsed.get("slides", []),
        "status": "generated",
        "rag_used": bool(rag_ctx),
        "model": _model(),
        "context_used": body.context or [],
    }

    (STRAT_DIR / data["name"]).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"ok": True, "data": data}


# ─────────────────────────────────────────────
# REVISE + GET (unverändert aus Original)
# ─────────────────────────────────────────────

class StrategyReviseIn(BaseModel):
    name: str
    use_critic: bool = False
    critic_name: Optional[str] = None
    add_agenda: bool = True
    add_cta: bool = True


@router.post("/revise")
def strategy_revise(body: StrategyReviseIn):
    p = STRAT_DIR / body.name
    if not p.exists():
        raise HTTPException(status_code=404, detail="strategy not found")
    data = json.loads(p.read_text(encoding="utf-8"))

    added = []
    if body.add_agenda and not any(s.get("type") == "agenda" for s in data.get("slides", [])):
        data["slides"].insert(1, {
            "type": "agenda",
            "title": "Agenda",
            "bullets": ["Ausgangslage", "Ziele", "Analyse", "Maßnahmen", "Roadmap"],
            "notes": "",
        })
        added.append("agenda")

    if body.add_cta:
        data["slides"].append({
            "type": "cta",
            "title": "Nächste Schritte",
            "bullets": ["Verantwortliche & Zeitplan", "KPIs definieren", "Risiken managen"],
            "notes": "",
        })
        added.append("cta")

    data["updated_at"] = time.time()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "data": data, "added": added}


@router.get("/{name}")
def strategy_get(name: str):
    p = STRAT_DIR / name
    if not p.exists():
        raise HTTPException(status_code=404, detail="strategy not found")
    data = json.loads(p.read_text(encoding="utf-8"))
    return {"ok": True, "data": data}


@router.get("/")
def strategy_list():
    """Listet alle gespeicherten Strategien."""
    strategies = []
    for f in sorted(STRAT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            strategies.append({
                "name": f.name,
                "title": data.get("title", f.name),
                "type": data.get("type", "strategy"),
                "created_at": data.get("created_at", 0),
                "model": data.get("model", "unknown"),
                "rag_used": data.get("rag_used", False),
            })
        except Exception:
            continue
    return {"ok": True, "strategies": strategies, "count": len(strategies)}
