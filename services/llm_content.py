# -*- coding: utf-8 -*-
"""
services/llm_content.py
=======================
Zentraler LLM-Wrapper für Content-Generierung.
Nutzt Ollama/Mistral lokal - kein Cloud-API.

Funktionen:
- generate_bullets(): Bullet-Points für Slides
- generate_summary(): Executive Summary
- generate_persona(): Persona basierend auf Briefing
- generate_critique(): Kritische Analyse eines Decks
- generate_from_template(): Freiform-Generierung mit Template
"""
from __future__ import annotations
import os
import json
import requests
from typing import List, Dict, Any, Optional

# ============================================
# KONFIGURATION
# ============================================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
DEFAULT_TIMEOUT = 120
MAX_RETRIES = 2

# ============================================
# BASIS-FUNKTIONEN
# ============================================

def _ollama_generate(prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    Basis-Call zu Ollama API.
    Returns: Generierter Text oder leerer String bei Fehler.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        }
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                return (data.get("response") or "").strip()
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"[llm_content] Fehler nach {MAX_RETRIES} Versuchen: {e}")
    return ""


def _parse_bullets(text: str, max_items: int = 6) -> List[str]:
    """Extrahiert Bullet-Points aus LLM-Output."""
    lines = text.strip().split("\n")
    bullets = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Entferne Aufzählungszeichen
        for prefix in ["- ", "• ", "* ", "· "]:
            if line.startswith(prefix):
                line = line[len(prefix):]
                break
        # Entferne Nummerierung (1. 2. etc.)
        if len(line) > 2 and line[0].isdigit() and line[1] in [".", ")", ":"]:
            line = line[2:].strip()
        elif len(line) > 3 and line[:2].isdigit() and line[2] in [".", ")", ":"]:
            line = line[3:].strip()
        
        if line and len(line) > 5:  # Mindestlänge
            bullets.append(line)
    
    return bullets[:max_items]


def _parse_json_safe(text: str) -> Optional[Dict[str, Any]]:
    """Versucht JSON aus LLM-Output zu extrahieren."""
    # Suche nach JSON-Block
    text = text.strip()
    
    # Entferne Markdown Code-Blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    
    # Finde JSON-Objekt
    if "{" in text:
        start = text.find("{")
        # Finde passendes Ende
        depth = 0
        for i, c in enumerate(text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        pass
                    break
    return None


# ============================================
# CONTENT-GENERIERUNG
# ============================================

def generate_bullets(
    topic: str,
    context: str = "",
    num_bullets: int = 5,
    style: str = "professional",
    language: str = "de"
) -> List[str]:
    """
    Generiert Bullet-Points für einen Slide.
    
    Args:
        topic: Thema/Titel des Slides
        context: Zusätzlicher Kontext (z.B. aus RAG)
        num_bullets: Anzahl gewünschter Bullets
        style: Stil (professional, casual, technical)
        language: Sprache (de, en)
    
    Returns:
        Liste von Bullet-Point Strings
    """
    lang_hint = "auf Deutsch" if language == "de" else "in English"
    
    prompt = f"""Erstelle genau {num_bullets} prägnante Bullet-Points {lang_hint} für eine Präsentationsfolie.

Thema: {topic}

{f"Kontext/Hintergrund: {context}" if context else ""}

Anforderungen:
- Jeder Punkt ist 1 kurzer, aussagekräftiger Satz
- Professioneller, strategischer Ton
- Konkret und handlungsorientiert
- Keine Füllwörter oder Floskeln

Antworte NUR mit den {num_bullets} Bullet-Points, einer pro Zeile, mit "- " am Anfang."""

    text = _ollama_generate(prompt, max_tokens=400, temperature=0.6)
    bullets = _parse_bullets(text, max_items=num_bullets)
    
    # Fallback wenn zu wenig generiert
    while len(bullets) < num_bullets:
        bullets.append(f"[Punkt {len(bullets)+1} zu {topic}]")
    
    return bullets[:num_bullets]


def generate_summary(
    brief: str,
    key_points: List[str] = None,
    max_sentences: int = 4,
    language: str = "de"
) -> str:
    """
    Generiert eine Executive Summary.
    
    Args:
        brief: Das ursprüngliche Briefing
        key_points: Optionale Schlüsselpunkte zum Einbauen
        max_sentences: Maximale Anzahl Sätze
        language: Sprache
    
    Returns:
        Summary als Fließtext
    """
    lang_hint = "auf Deutsch" if language == "de" else "in English"
    kp_text = "\n".join([f"- {p}" for p in (key_points or [])]) if key_points else ""
    
    prompt = f"""Schreibe eine Executive Summary {lang_hint} für folgendes Strategie-Briefing.

Briefing:
{brief}

{f"Wichtige Punkte zum Einbauen:{chr(10)}{kp_text}" if kp_text else ""}

Anforderungen:
- Maximal {max_sentences} Sätze
- Beginne mit dem Kernziel
- Nenne den strategischen Ansatz
- Schließe mit dem erwarteten Nutzen
- Professioneller, prägnanter Stil

Schreibe NUR die Summary, keine Einleitung oder Erklärung."""

    text = _ollama_generate(prompt, max_tokens=300, temperature=0.5)
    return text.strip() or f"Strategische Initiative: {brief[:100]}..."


def generate_persona(
    product: str,
    market: str = "B2B",
    industry: str = "",
    language: str = "de"
) -> Dict[str, Any]:
    """
    Generiert eine Buyer Persona.
    
    Returns:
        Dict mit: name, role, goals, pains, objections, channels
    """
    prompt = f"""Erstelle eine detaillierte Buyer Persona für:
Produkt/Service: {product}
Markt: {market}
{f"Branche: {industry}" if industry else ""}

Antworte im JSON-Format:
{{
    "name": "Beschreibender Name der Persona",
    "role": "Jobtitel/Position",
    "goals": ["Ziel 1", "Ziel 2", "Ziel 3"],
    "pains": ["Pain Point 1", "Pain Point 2", "Pain Point 3"],
    "objections": ["Einwand 1", "Einwand 2"],
    "channels": ["Kanal 1", "Kanal 2"],
    "budget_authority": "hoch/mittel/niedrig",
    "decision_style": "analytisch/emotional/konsensorientiert"
}}

Antworte NUR mit dem JSON, keine Erklärung."""

    text = _ollama_generate(prompt, max_tokens=500, temperature=0.7)
    parsed = _parse_json_safe(text)
    
    if parsed and "name" in parsed:
        return parsed
    
    # Fallback
    return {
        "name": f"{market} Decision Maker",
        "role": "Entscheider",
        "goals": ["Effizienz steigern", "Kosten senken", "Innovation vorantreiben"],
        "pains": ["Komplexe Prozesse", "Mangelnde Ressourcen", "Zeitdruck"],
        "objections": ["Budget", "Implementierungsaufwand"],
        "channels": ["LinkedIn", "Fachmedien"],
        "budget_authority": "mittel",
        "decision_style": "analytisch"
    }


def generate_critique(
    content: str,
    content_type: str = "strategy",
    language: str = "de"
) -> Dict[str, Any]:
    """
    Generiert eine kritische Analyse von Content.
    
    Returns:
        Dict mit: risks, assumptions, improvements, score
    """
    prompt = f"""Analysiere kritisch folgenden {content_type}-Content:

{content[:2000]}

Antworte im JSON-Format:
{{
    "risks": ["Risiko 1", "Risiko 2", "Risiko 3"],
    "assumptions": ["Annahme 1", "Annahme 2"],
    "improvements": ["Verbesserung 1", "Verbesserung 2", "Verbesserung 3"],
    "missing": ["Fehlendes Element 1", "Fehlendes Element 2"],
    "strengths": ["Stärke 1", "Stärke 2"],
    "score": 7
}}

- risks: Potenzielle Risiken und Schwachstellen
- assumptions: Implizite Annahmen die validiert werden sollten
- improvements: Konkrete Verbesserungsvorschläge
- missing: Was fehlt oder sollte ergänzt werden
- strengths: Was ist gut
- score: Qualitätsbewertung 1-10

Antworte NUR mit dem JSON."""

    text = _ollama_generate(prompt, max_tokens=600, temperature=0.6)
    parsed = _parse_json_safe(text)
    
    if parsed and "risks" in parsed:
        return parsed
    
    # Fallback
    return {
        "risks": ["Keine spezifischen Risiken identifiziert"],
        "assumptions": ["Marktbedingungen bleiben stabil"],
        "improvements": ["Mehr Daten zur Validierung sammeln"],
        "missing": ["Konkrete KPIs", "Zeitplan"],
        "strengths": ["Klare Struktur"],
        "score": 6
    }


def generate_metrics(
    goal: str,
    industry: str = "",
    timeframe: str = "12 Monate",
    language: str = "de"
) -> List[Dict[str, Any]]:
    """
    Generiert relevante KPIs/Metriken für ein Ziel.
    
    Returns:
        Liste von Dicts mit: name, target, baseline, unit
    """
    prompt = f"""Definiere 4-5 messbare KPIs für folgendes Ziel:

Ziel: {goal}
{f"Branche: {industry}" if industry else ""}
Zeitraum: {timeframe}

Antworte als JSON-Array:
[
    {{"name": "KPI Name", "target": "Zielwert", "baseline": "Ausgangswert", "unit": "Einheit"}},
    ...
]

Beispiel:
[
    {{"name": "Lead Conversion Rate", "target": "15%", "baseline": "8%", "unit": "%"}},
    {{"name": "Customer Acquisition Cost", "target": "€80", "baseline": "€120", "unit": "€"}}
]

Antworte NUR mit dem JSON-Array."""

    text = _ollama_generate(prompt, max_tokens=500, temperature=0.6)
    
    # Versuche Array zu parsen
    text = text.strip()
    if text.startswith("["):
        try:
            end = text.rfind("]") + 1
            return json.loads(text[:end])
        except json.JSONDecodeError:
            pass
    
    # Fallback
    return [
        {"name": "Primär-KPI", "target": "TBD", "baseline": "TBD", "unit": "-"},
        {"name": "Sekundär-KPI", "target": "TBD", "baseline": "TBD", "unit": "-"},
    ]


def generate_from_template(
    template: str,
    variables: Dict[str, str],
    max_tokens: int = 500,
    temperature: float = 0.7
) -> str:
    """
    Generiert Content basierend auf einem Template mit Variablen.
    
    Args:
        template: Prompt-Template mit {variable} Platzhaltern
        variables: Dict mit Variablen-Werten
        max_tokens: Max Output-Länge
        temperature: Kreativität (0.0-1.0)
    
    Returns:
        Generierter Text
    """
    # Variablen einsetzen
    prompt = template
    for key, value in variables.items():
        prompt = prompt.replace(f"{{{key}}}", str(value))
    
    return _ollama_generate(prompt, max_tokens=max_tokens, temperature=temperature)


def generate_slide_content(
    slide_type: str,
    title: str,
    brief: str,
    context: str = "",
    num_bullets: int = 5,
    language: str = "de"
) -> Dict[str, Any]:
    """
    Generiert kompletten Content für einen Slide-Typ.
    
    Args:
        slide_type: Typ des Slides (executive_summary, use_case, roi, roadmap, etc.)
        title: Slide-Titel
        brief: Ursprüngliches Briefing
        context: RAG-Kontext
        num_bullets: Anzahl Bullets
        language: Sprache
    
    Returns:
        Dict mit: title, bullets, notes, citations
    """
    type_prompts = {
        "executive_summary": "eine Executive Summary mit Kernziel, Ansatz und erwartetem Nutzen",
        "use_case": "einen konkreten Use Case mit Problem, Lösung und Mehrwert",
        "roi": "eine ROI-Betrachtung mit Kosten, Nutzen und Payback-Zeitraum",
        "roadmap": "eine Roadmap mit Phasen, Meilensteinen und Zeitrahmen",
        "risks": "eine Risikoanalyse mit Risiken, Mitigationsmaßnahmen und Verantwortlichen",
        "next_steps": "konkrete nächste Schritte mit Aktionen, Verantwortlichen und Terminen",
        "personas": "Zielgruppen-Beschreibung mit Bedürfnissen und Ansprache",
        "competitive": "eine Wettbewerbsanalyse mit Differenzierung und Positionierung",
        "kpis": "messbare KPIs mit Zielwerten und Tracking-Methode",
    }
    
    type_hint = type_prompts.get(slide_type, f"Inhalte zum Thema {slide_type}")
    lang_hint = "auf Deutsch" if language == "de" else "in English"
    
    prompt = f"""Erstelle {lang_hint} {type_hint} für eine Strategie-Präsentation.

Slide-Titel: {title}

Briefing:
{brief[:500]}

{f"Zusätzlicher Kontext:{chr(10)}{context[:500]}" if context else ""}

Generiere:
1. Genau {num_bullets} prägnante Bullet-Points (je max 15 Wörter)
2. Speaker Notes (2-3 Sätze für den Präsentator)

Format:
BULLETS:
- Punkt 1
- Punkt 2
...

NOTES:
Speaker Notes hier...

Antworte NUR in diesem Format."""

    text = _ollama_generate(prompt, max_tokens=600, temperature=0.6)
    
    # Parse Output
    bullets = []
    notes = ""
    
    if "BULLETS:" in text and "NOTES:" in text:
        parts = text.split("NOTES:")
        bullet_section = parts[0].replace("BULLETS:", "").strip()
        notes = parts[1].strip() if len(parts) > 1 else ""
        bullets = _parse_bullets(bullet_section, max_items=num_bullets)
    else:
        bullets = _parse_bullets(text, max_items=num_bullets)
    
    # Fallback
    while len(bullets) < num_bullets:
        bullets.append(f"[{title} - Punkt {len(bullets)+1}]")
    
    return {
        "title": title,
        "bullets": bullets[:num_bullets],
        "notes": notes or f"Erläuterungen zu: {title}",
        "citations": []  # Wird später durch RAG befüllt
    }


# ============================================
# HEALTH CHECK
# ============================================

def check_ollama() -> Dict[str, Any]:
    """Prüft ob Ollama erreichbar ist und das Modell geladen."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            model_ready = any(LLM_MODEL in m for m in models)
            return {
                "ok": True,
                "host": OLLAMA_HOST,
                "model": LLM_MODEL,
                "model_loaded": model_ready,
                "available_models": models
            }
    except Exception as e:
        return {"ok": False, "error": str(e), "host": OLLAMA_HOST}
    
    return {"ok": False, "error": "Unknown", "host": OLLAMA_HOST}


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=== LLM Content Service Test ===\n")
    
    # Health Check
    status = check_ollama()
    print(f"Ollama Status: {status}\n")
    
    if status.get("ok"):
        # Test Bullets
        print("--- Test: generate_bullets ---")
        bullets = generate_bullets(
            topic="Digitale Transformation im Mittelstand",
            context="Fokus auf Automatisierung und KI-Integration",
            num_bullets=4
        )
        for b in bullets:
            print(f"  • {b}")
        print()
        
        # Test Persona
        print("--- Test: generate_persona ---")
        persona = generate_persona(
            product="Marketing Automation Software",
            market="B2B",
            industry="Manufacturing"
        )
        print(f"  Persona: {persona.get('name')}")
        print(f"  Role: {persona.get('role')}")
        print(f"  Goals: {persona.get('goals')}")
        print()
