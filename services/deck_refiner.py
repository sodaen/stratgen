# -*- coding: utf-8 -*-
"""
services/deck_refiner.py
=========================
Iterativer Multi-LLM Deck-Refiner für StratGen.

Ablauf:
  1. Generator-LLM erstellt initiales Deck (Ollama/Mistral)
  2. Critic-LLM bewertet jeden Slide (Nemotron / zweites Modell)
  3. Refiner-LLM verbessert schwache Slides basierend auf Kritik
  4. Wiederholen bis Qualitätsschwelle erreicht (default: 8.0/10)
     oder maximale Iterationen erreicht (default: 3)

Unterstützte Konfigurationen:
  A) Ollama only:    Generator=Mistral, Critic=Mistral (anderer Prompt)
  B) Ollama+NIM:     Generator=Mistral, Critic=Nemotron via NIM
  C) Nemotron only:  Generator=Nemotron, Critic=Nemotron
  D) Mixed:          Frei konfigurierbar

Jeder Schritt wird als SSE-Event gestreamt für Live-Fortschritt im Frontend.

Author: StratGen Sprint 9
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Generator, Optional

log = logging.getLogger(__name__)

# ── Konfiguration ─────────────────────────────────────────────────────────────
import os

QUALITY_THRESHOLD = float(os.getenv("REFINER_QUALITY_THRESHOLD", "8.0"))
MAX_ITERATIONS    = int(os.getenv("REFINER_MAX_ITERATIONS", "3"))
MIN_SCORE_TO_KEEP = float(os.getenv("REFINER_MIN_SLIDE_SCORE", "6.0"))


# ── Datenstrukturen ───────────────────────────────────────────────────────────

@dataclass
class SlideContent:
    index: int
    title: str
    bullets: list[str]
    slide_type: str = "content"
    notes: str = ""
    quality_score: float = 0.0
    critique: str = ""
    improved: bool = False
    iteration: int = 0


@dataclass
class RefineSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    briefing: str = ""
    customer_name: str = ""
    deck_size: int = 10
    generator_provider: str = "ollama"
    generator_model: str = "mistral"
    critic_provider: str = "nemotron"
    critic_model: str = "nvidia/nemotron-mini-4b-instruct"
    quality_threshold: float = QUALITY_THRESHOLD
    max_iterations: int = MAX_ITERATIONS
    slides: list[SlideContent] = field(default_factory=list)
    iteration: int = 0
    avg_score: float = 0.0
    status: str = "created"
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    total_llm_calls: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ── LLM-Wrapper ───────────────────────────────────────────────────────────────

def _llm(prompt: str, provider: str, model: str,
         max_tokens: int = 1500, temperature: float = 0.7) -> str:
    """Ruft llm_router.llm_generate mit explizitem Provider/Modell auf."""
    try:
        from services.llm_router import llm_generate
        return llm_generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            provider=provider,
            model=model,
        )
    except Exception as e:
        log.error("LLM call failed (%s/%s): %s", provider, model, e)
        return ""


# ── Prompts ───────────────────────────────────────────────────────────────────

def _build_generation_prompt(briefing: str, customer: str,
                              deck_size: int, slide_idx: int,
                              all_titles: list[str]) -> str:
    context = f"Agenda: {', '.join(all_titles)}" if all_titles else ""
    return f"""Du bist ein erfahrener Strategieberater und erstellst professionelle Präsentations-Slides.

Kunde/Unternehmen: {customer}
Briefing: {briefing}
{context}

Erstelle jetzt genau Slide {slide_idx + 1} von {deck_size}.

Antworte NUR als JSON, keine Erklärungen:
{{
  "title": "Slide-Titel (prägnant, max 8 Wörter)",
  "slide_type": "title|agenda|content|swot|kpi|comparison|cta",
  "bullets": [
    "Bullet 1 – konkret und wertvoll",
    "Bullet 2 – faktenbasiert",
    "Bullet 3 – handlungsorientiert"
  ],
  "notes": "Kurze Sprechnotiz für den Präsentator"
}}"""


def _build_critique_prompt(slide: SlideContent, briefing: str,
                           customer: str, model: str = "") -> str:
    """Baut den Critique-Prompt - optimiert für DeepSeek-R1 Reasoning wenn erkannt."""
    bullets_text = "\n".join(f"  - {b}" for b in slide.bullets)
    is_deepseek = "deepseek" in model.lower() or "r1" in model.lower()

    # DeepSeek-R1 profitiert von expliziter Reasoning-Anweisung
    reasoning_hint = (
        "Denke Schritt für Schritt: Analysiere zuerst jeden Bullet-Point einzeln, "
        "dann bewerte das Gesamtbild.\n\n"
        if is_deepseek else ""
    )

    return f"""Du bist ein erfahrener, kritischer Strategieberater der Präsentationen für Top-Management bewertet.
{reasoning_hint}
Kontext: {briefing[:300]}
Kunde: {customer}

SLIDE {slide.index + 1}: {slide.title}
{bullets_text}

Bewerte streng nach diesen Kriterien (jeweils 1-10):
1. Relevanz für das Briefing (trifft es den Kern?)
2. Klarheit und Verständlichkeit (sofort erfassbar?)
3. Professionalität der Sprache (C-Level geeignet?)
4. Faktische Tiefe / Mehrwert (konkret oder Platitüden?)
5. Präsentierbarkeit (fesselnd oder langweilig?)

Antworte NUR als JSON ohne Erklärungen außerhalb:
{{
  "score": 7.5,
  "scores": {{
    "relevance": 8,
    "clarity": 7,
    "professionalism": 8,
    "depth": 6,
    "presentability": 7
  }},
  "critique": "Konkreter Kritiktext: Was fehlt, was ist schwach, was ist unklar?",
  "improvement_suggestions": [
    "Spezifischer Verbesserungsvorschlag 1",
    "Spezifischer Verbesserungsvorschlag 2"
  ]
}}"""


def _build_improvement_prompt(slide: SlideContent, briefing: str,
                               customer: str, critique: str,
                               suggestions: list[str]) -> str:
    bullets_text = "\n".join(f"  - {b}" for b in slide.bullets)
    sugg_text = "\n".join(f"- {s}" for s in suggestions[:3])
    return f"""Verbessere diesen Präsentations-Slide basierend auf der Kritik.

Kontext: {briefing[:300]}
Kunde: {customer}

AKTUELLER SLIDE {slide.index + 1}: {slide.title}
{bullets_text}

KRITIK: {critique}

VERBESSERUNGSVORSCHLÄGE:
{sugg_text}

Erstelle eine verbesserte Version. Antworte NUR als JSON:
{{
  "title": "Verbesserter Titel",
  "slide_type": "{slide.slide_type}",
  "bullets": [
    "Verbesserter Bullet 1",
    "Verbesserter Bullet 2",
    "Verbesserter Bullet 3",
    "Neuer Bullet basierend auf Feedback"
  ],
  "notes": "Aktualisierte Sprechnotiz"
}}"""


def _build_agenda_prompt(briefing: str, customer: str, deck_size: int) -> str:
    return f"""Erstelle eine Agenda für eine professionelle Strategiepräsentation.

Kunde: {customer}
Briefing: {briefing[:500]}
Anzahl Slides: {deck_size}

Antworte NUR als JSON-Array mit {deck_size} Titeln:
["Titel 1", "Titel 2", "Titel 3", ...]

Die Titel sollen eine logische Erzählstruktur bilden:
Einstieg → Analyse → Strategie → Maßnahmen → Fazit"""


# ── JSON-Parser ───────────────────────────────────────────────────────────────

def _parse_json(text: str, fallback: dict) -> dict:
    """Extrahiert JSON aus LLM-Antwort robust. Unterstützt verschachtelte Objekte."""
    if not text:
        return fallback

    # <think>...</think> Tags von DeepSeek-R1 entfernen
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    # Markdown-Code-Blöcke entfernen (```json ... ``` oder ``` ... ```)
    text = re.sub(r'```(?:json)?\s*', '', text).replace('```', '').strip()

    # Ganzen Text direkt versuchen
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Äußerstes JSON-Objekt finden (mit verschachtelten Klammern)
    start = text.find('{')
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        break

    return fallback


def _parse_json_array(text: str) -> list[str]:
    """Extrahiert JSON-Array aus LLM-Antwort. Entfernt DeepSeek-R1 Think-Tags."""
    if not text:
        return []
    # Think-Tags entfernen
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    # Markdown-Code-Blöcke entfernen
    text = re.sub(r'```(?:json)?\s*', '', text).replace('```', '').strip()
    # Äußerstes Array finden
    start = text.find('[')
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    try:
                        result = json.loads(text[start:i+1])
                        if isinstance(result, list):
                            return [str(x) for x in result]
                    except json.JSONDecodeError:
                        break
    return []


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def refine_deck(session: RefineSession) -> Generator[dict, None, None]:
    """
    Hauptgenerator für den iterativen Deck-Refinement-Prozess.
    Yield: SSE-Events als dicts.

    Events:
      started       → Session gestartet
      agenda        → Agenda generiert
      slide_gen     → Slide generiert
      slide_critique → Slide bewertet
      slide_improve → Slide verbessert
      iteration_done → Iteration abgeschlossen
      done          → Fertig
      error         → Fehler
    """
    session.status = "running"
    yield {"type": "started", "session_id": session.session_id,
           "briefing": session.briefing[:100] + "...",
           "generator": f"{session.generator_provider}/{session.generator_model}",
           "critic": f"{session.critic_provider}/{session.critic_model}",
           "max_iterations": session.max_iterations,
           "quality_threshold": session.quality_threshold}

    # ── Schritt 1: Agenda generieren ──────────────────────────────────────────
    yield {"type": "agenda_start", "message": "Generiere Deck-Struktur…"}

    # Agenda: Qwen2.5 wenn als structure_model gesetzt, sonst generator
    agenda_provider = getattr(session, "structure_provider", session.generator_provider)
    agenda_model = getattr(session, "structure_model", session.generator_model)
    agenda_raw = _llm(
        _build_agenda_prompt(session.briefing, session.customer_name, session.deck_size),
        agenda_provider, agenda_model,
        max_tokens=500, temperature=0.4,
    )
    session.total_llm_calls += 1

    agenda_titles = _parse_json_array(agenda_raw)
    if len(agenda_titles) < session.deck_size:
        # Fallback
        agenda_titles = [f"Slide {i+1}" for i in range(session.deck_size)]

    yield {"type": "agenda", "titles": agenda_titles[:session.deck_size]}

    # ── Schritt 2: Initiale Slides generieren ─────────────────────────────────
    slides: list[SlideContent] = []
    for i in range(session.deck_size):
        title_hint = agenda_titles[i] if i < len(agenda_titles) else f"Slide {i+1}"
        prompt = _build_generation_prompt(
            session.briefing, session.customer_name,
            session.deck_size, i, agenda_titles[:i]
        )
        raw = _llm(prompt, session.generator_provider, session.generator_model,
                   max_tokens=600, temperature=0.7)
        session.total_llm_calls += 1

        data = _parse_json(raw, {
            "title": title_hint,
            "slide_type": "content",
            "bullets": ["Inhalt wird generiert…"],
            "notes": "",
        })

        slide = SlideContent(
            index=i,
            title=data.get("title", title_hint),
            bullets=data.get("bullets", [])[:6],
            slide_type=data.get("slide_type", "content"),
            notes=data.get("notes", ""),
            iteration=0,
        )
        slides.append(slide)

        yield {
            "type": "slide_gen",
            "index": i,
            "title": slide.title,
            "bullets": slide.bullets,
            "slide_type": slide.slide_type,
        }

    session.slides = slides

    # ── Schritt 3: Iterativer Critic/Refine-Loop ──────────────────────────────
    for iteration in range(session.max_iterations):
        session.iteration = iteration + 1
        yield {
            "type": "iteration_start",
            "iteration": session.iteration,
            "message": f"Iteration {session.iteration}/{session.max_iterations} – Bewerte Slides…"
        }

        scores = []
        for slide in session.slides:
            # Kritik
            critique_raw = _llm(
                _build_critique_prompt(
                    slide, session.briefing, session.customer_name,
                    model=session.critic_model
                ),
                session.critic_provider, session.critic_model,
                max_tokens=500, temperature=0.3,
            )
            session.total_llm_calls += 1

            critique_data = _parse_json(critique_raw, {
                "score": 7.0,
                "critique": "Keine spezifische Kritik.",
                "improvement_suggestions": [],
            })

            score = float(critique_data.get("score", 7.0))
            score = max(1.0, min(10.0, score))  # Clamp
            slide.quality_score = score
            slide.critique = critique_data.get("critique", "")
            suggestions = critique_data.get("improvement_suggestions", [])
            scores.append(score)

            yield {
                "type": "slide_critique",
                "index": slide.index,
                "title": slide.title,
                "score": score,
                "critique": slide.critique[:200],
                "iteration": session.iteration,
            }

            # Verbessern wenn Score unter Schwelle
            if score < MIN_SCORE_TO_KEEP:
                improve_raw = _llm(
                    _build_improvement_prompt(
                        slide, session.briefing, session.customer_name,
                        slide.critique, suggestions
                    ),
                    session.generator_provider, session.generator_model,
                    max_tokens=600, temperature=0.6,
                )
                session.total_llm_calls += 1

                improved = _parse_json(improve_raw, {
                    "title": slide.title,
                    "slide_type": slide.slide_type,
                    "bullets": slide.bullets,
                    "notes": slide.notes,
                })

                old_title = slide.title
                slide.title   = improved.get("title", slide.title)
                slide.bullets = improved.get("bullets", slide.bullets)[:6]
                slide.notes   = improved.get("notes", slide.notes)
                slide.improved = True
                slide.iteration = session.iteration

                yield {
                    "type": "slide_improve",
                    "index": slide.index,
                    "old_title": old_title,
                    "new_title": slide.title,
                    "new_bullets": slide.bullets,
                    "old_score": score,
                    "iteration": session.iteration,
                }

        avg = round(sum(scores) / len(scores), 2) if scores else 0.0
        session.avg_score = avg
        weak = sum(1 for s in scores if s < MIN_SCORE_TO_KEEP)

        yield {
            "type": "iteration_done",
            "iteration": session.iteration,
            "avg_score": avg,
            "weak_slides": weak,
            "threshold": session.quality_threshold,
            "total_llm_calls": session.total_llm_calls,
        }

        # Abbruch wenn Qualitätsschwelle erreicht
        if avg >= session.quality_threshold:
            yield {
                "type": "quality_reached",
                "avg_score": avg,
                "threshold": session.quality_threshold,
                "message": f"Qualitätsschwelle {session.quality_threshold} erreicht nach {session.iteration} Iteration(en)."
            }
            break

    # ── Fertig ────────────────────────────────────────────────────────────────
    session.status = "done"
    session.finished_at = time.time()
    duration = round(session.finished_at - session.started_at, 1)

    yield {
        "type": "done",
        "session_id": session.session_id,
        "avg_score": session.avg_score,
        "iterations": session.iteration,
        "total_slides": len(session.slides),
        "improved_slides": sum(1 for s in session.slides if s.improved),
        "total_llm_calls": session.total_llm_calls,
        "duration_s": duration,
        "slides": [
            {
                "index": s.index,
                "title": s.title,
                "bullets": s.bullets,
                "slide_type": s.slide_type,
                "notes": s.notes,
                "quality_score": s.quality_score,
                "improved": s.improved,
            }
            for s in session.slides
        ],
    }
