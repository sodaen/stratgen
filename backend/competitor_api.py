# -*- coding: utf-8 -*-
"""
StratGen – Competitor Research API
Echtes LLM-Scoring statt Fake-Symbolen.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

log = logging.getLogger("stratgen.competitor")

# _OFFLINE_GUARD_
try:
    from services.offline import is_offline, offline_result
except ImportError:
    def is_offline(): return False
    def offline_result(s): return {"ok": False, "offline": True, "service": s}

router = APIRouter(prefix="/competitors", tags=["competitors"])

COMP_DIR = Path("data/competitors")
COMP_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# LLM HELPER (shared pattern)
# ─────────────────────────────────────────────

def _ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

def _model() -> str:
    return os.getenv("LLM_MODEL", "mistral")

def _llm(prompt: str, max_tokens: int = 2000) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        try:
            r = requests.post(
                f"{_ollama_host()}/api/generate",
                json={"model": _model(), "prompt": prompt, "stream": False,
                      "options": {"num_predict": max_tokens, "temperature": 0.5}},
                timeout=120,
            )
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except Exception as e:
            log.warning("Ollama call failed: %s", e)
            return ""
    if provider == "openai":
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            log.warning("OpenAI call failed: %s", e)
            return ""
    return ""

def _rag_context(query: str, customer: str = "", k: int = 4) -> str:
    """Sucht relevante Dokumente für Wettbewerbsanalyse."""
    try:
        base = os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")
        r = requests.get(
            f"{base}/knowledge/search_semantic",
            params={"q": query, "k": k},
            timeout=20,
        )
        if not r.ok:
            return ""
        hits = r.json().get("_hits") or r.json().get("results") or []
        snippets = []
        for h in hits[:k]:
            txt = h.get("snippet") or h.get("text") or ""
            if txt:
                snippets.append(txt[:500])
        return "\n---\n".join(snippets)
    except Exception:
        return ""

def _parse_json(text: str) -> Optional[Dict]:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    for fence in ["```json", "```"]:
        if fence in text:
            try:
                s = text.index(fence) + len(fence)
                e = text.index("```", s)
                return json.loads(text[s:e].strip())
            except Exception:
                pass
    try:
        s = text.index("{")
        e = text.rindex("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return None


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class MatrixReq(BaseModel):
    customer_name: str
    competitors: List[str]
    criteria: List[str] = Field(
        default_factory=lambda: [
            "Preis/Leistung", "Funktionsumfang", "Benutzerfreundlichkeit",
            "Integrationen", "Support", "Skalierbarkeit"
        ]
    )
    industry: Optional[str] = None
    lang: str = "de"
    use_rag: bool = True


class CompetitorProfileReq(BaseModel):
    competitor_name: str
    customer_name: str
    industry: Optional[str] = None
    lang: str = "de"


# ─────────────────────────────────────────────
# WETTBEWERBS-MATRIX (LLM-basiert)
# ─────────────────────────────────────────────

@router.post("/matrix")
def matrix(req: MatrixReq = Body(...)):
    """
    Erstellt eine Wettbewerbsmatrix mit echtem LLM-Scoring (1–10).
    Optional mit RAG-Kontext aus hochgeladenen Dokumenten.
    """
    # RAG-Kontext
    rag_ctx = ""
    if req.use_rag:
        query = f"Wettbewerb Konkurrenz {req.customer_name} {' '.join(req.competitors[:3])} {req.industry or ''}"
        rag_ctx = _rag_context(query, req.customer_name)

    lang_instr = "Antworte auf Deutsch." if req.lang == "de" else "Answer in English."
    context_block = f"\n\nKontext aus Dokumenten:\n{rag_ctx}" if rag_ctx else ""

    competitors_json = json.dumps(req.competitors)
    criteria_json = json.dumps(req.criteria)

    prompt = f"""Du bist ein Marktanalyst. Bewerte diese Wettbewerber anhand der Kriterien.
Nutze Branchenwissen und den Kontext. Sei konkret und differenziert.

Unternehmen des Kunden: {req.customer_name}
Wettbewerber: {competitors_json}
Kriterien: {criteria_json}
Branche: {req.industry or 'Allgemein'}{context_block}

{lang_instr}

WICHTIG: Gib NUR gültiges JSON zurück, KEINE Erklärungen davor oder danach.

{{
  "table": [
    {{
      "competitor": "Name des Wettbewerbers",
      "scores": {{
        "Kriterium1": 7,
        "Kriterium2": 5
      }},
      "overall": 6.2,
      "strengths": ["Stärke 1", "Stärke 2"],
      "weaknesses": ["Schwäche 1"],
      "positioning": "1 Satz Positionierung"
    }}
  ],
  "winner_by_criteria": {{
    "Kriterium1": "Wettbewerber X",
    "Kriterium2": "Wettbewerber Y"
  }},
  "our_advantages": ["Vorteil von {req.customer_name} gegenüber Wettbewerbern 1", "Vorteil 2"],
  "our_gaps": ["Lücke 1 die wir schließen sollten", "Lücke 2"],
  "recommendation": "2-3 Sätze strategische Empfehlung für {req.customer_name}",
  "summary": "1 Satz Gesamtfazit"
}}

Scores: 1=sehr schlecht, 10=sehr gut. Seien Sie realistisch und differenziert.
Erstelle EINEN Eintrag pro Wettbewerber aus dieser Liste: {competitors_json}"""

    raw = _llm(prompt, max_tokens=2500)
    parsed = _parse_json(raw)

    if not parsed or not parsed.get("table"):
        log.warning("Competitor matrix LLM failed, building fallback")
        # Strukturierten Fallback bauen
        table = []
        for comp in req.competitors:
            scores = {crit: 5 for crit in req.criteria}
            table.append({
                "competitor": comp,
                "scores": scores,
                "overall": 5.0,
                "strengths": ["LLM nicht verfügbar"],
                "weaknesses": [],
                "positioning": "Analyse nicht möglich – LLM starten",
            })
        parsed = {
            "table": table,
            "winner_by_criteria": {},
            "our_advantages": ["LLM konfigurieren für echte Analyse"],
            "our_gaps": [],
            "recommendation": "Bitte Ollama starten und erneut analysieren.",
            "summary": "LLM nicht verfügbar.",
            "_fallback": True,
        }

    # Slides bauen
    slides = _matrix_to_slides(parsed, req.customer_name, req.criteria)

    result = {
        "ok": True,
        "customer_name": req.customer_name,
        "table": parsed.get("table", []),
        "winner_by_criteria": parsed.get("winner_by_criteria", {}),
        "our_advantages": parsed.get("our_advantages", []),
        "our_gaps": parsed.get("our_gaps", []),
        "recommendation": parsed.get("recommendation", ""),
        "summary": parsed.get("summary", ""),
        "slides": slides,
        "rag_used": bool(rag_ctx),
        "model": _model(),
        "generated_at": time.time(),
        "_fallback": parsed.get("_fallback", False),
    }

    # Persistieren
    name = f"comp-{req.customer_name}-{int(time.time())}.json".replace(" ", "_")
    (COMP_DIR / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["name"] = name

    return result


def _matrix_to_slides(data: Dict, customer_name: str, criteria: List[str]) -> List[Dict]:
    slides = [
        {
            "type": "title",
            "title": f"Wettbewerbsanalyse: {customer_name}",
            "bullets": [],
            "layout": "title-only",
        },
    ]

    # Übersichts-Slide mit Scores
    for comp in data.get("table", []):
        name = comp.get("competitor", "?")
        overall = comp.get("overall", 0)
        strengths = comp.get("strengths", [])[:2]
        weaknesses = comp.get("weaknesses", [])[:1]
        bullet_lines = [f"Gesamtscore: {overall:.1f}/10"]
        bullet_lines.extend([f"✓ {s}" for s in strengths])
        bullet_lines.extend([f"✗ {w}" for w in weaknesses])
        if comp.get("positioning"):
            bullet_lines.append(f"→ {comp['positioning']}")
        slides.append({
            "type": "content",
            "title": f"Analyse: {name}",
            "bullets": bullet_lines,
            "layout": "title-bullets",
        })

    # Vorteile vs. Lücken
    advantages = data.get("our_advantages", [])
    gaps = data.get("our_gaps", [])
    if advantages or gaps:
        slides.append({
            "type": "comparison",
            "title": f"{customer_name}: Stärken & Lücken",
            "bullets": (
                [f"✓ {a}" for a in advantages] +
                [f"→ {g}" for g in gaps]
            ),
            "layout": "two-column",
        })

    # Empfehlung
    if data.get("recommendation"):
        slides.append({
            "type": "cta",
            "title": "Strategische Empfehlung",
            "bullets": [data["recommendation"]],
            "layout": "title-content",
        })

    return slides


# ─────────────────────────────────────────────
# EINZELNER WETTBEWERBER DEEP DIVE
# ─────────────────────────────────────────────

@router.post("/profile")
def competitor_profile(req: CompetitorProfileReq):
    """
    Erstellt ein detailliertes Profil eines einzelnen Wettbewerbers.
    """
    rag_ctx = _rag_context(
        f"{req.competitor_name} Produkt Markt {req.industry or ''}",
        req.customer_name
    )

    lang_instr = "Antworte auf Deutsch." if req.lang == "de" else "Answer in English."
    context_block = f"\n\nKontext:\n{rag_ctx}" if rag_ctx else ""

    prompt = f"""Erstelle ein Wettbewerberprofil für strategische Entscheidungen.

Wettbewerber: {req.competitor_name}
Unser Unternehmen: {req.customer_name}
Branche: {req.industry or 'Allgemein'}{context_block}

{lang_instr}

Gib NUR JSON zurück:
{{
  "name": "{req.competitor_name}",
  "market_position": "Leader|Challenger|Niche|Follower",
  "estimated_market_share": "~X%",
  "key_products": ["Produkt 1", "Produkt 2"],
  "target_segments": ["Segment 1", "Segment 2"],
  "pricing_strategy": "Premium|Mid-Market|Low-Cost|Freemium",
  "key_differentiators": ["USP 1", "USP 2", "USP 3"],
  "known_weaknesses": ["Schwäche 1", "Schwäche 2"],
  "recent_moves": ["Aktion 1", "Aktion 2"],
  "threat_level": "hoch|mittel|niedrig",
  "threat_reasoning": "Warum diese Bedrohungsstufe",
  "counter_strategy": "Konkrete Empfehlung wie man diesem Wettbewerber begegnet"
}}"""

    raw = _llm(prompt, max_tokens=1500)
    parsed = _parse_json(raw)

    if not parsed:
        parsed = {
            "name": req.competitor_name,
            "market_position": "unbekannt",
            "threat_level": "unbekannt",
            "counter_strategy": "LLM nicht verfügbar",
            "_fallback": True,
        }

    return {"ok": True, "profile": parsed, "rag_used": bool(rag_ctx), "model": _model()}


# ─────────────────────────────────────────────
# LISTE GESPEICHERTER ANALYSEN
# ─────────────────────────────────────────────

@router.get("/")
def list_analyses():
    analyses = []
    for f in sorted(COMP_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            analyses.append({
                "name": f.name,
                "customer_name": data.get("customer_name", "?"),
                "competitors": [t.get("competitor") for t in data.get("table", [])],
                "generated_at": data.get("generated_at", 0),
                "rag_used": data.get("rag_used", False),
            })
        except Exception:
            continue
    return {"ok": True, "analyses": analyses, "count": len(analyses)}
