# -*- coding: utf-8 -*-
"""
services/story_engine.py
========================
Killer-Feature: Story & Narrative Engine

Features:
1. Automatische Story-Struktur (Hero's Journey, Problem-Solution, etc.)
2. Narrative Arc Detection
3. Emotional Journey Mapping
4. Hook Generation
5. Call-to-Action Optimization
6. Storytelling Frameworks

Author: StratGen Agent V3.5
"""
from __future__ import annotations
import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================
# STORY FRAMEWORKS
# ============================================

class StoryFramework(str, Enum):
    """Verfügbare Storytelling-Frameworks."""
    HEROS_JOURNEY = "heros_journey"
    PROBLEM_SOLUTION = "problem_solution"
    BEFORE_AFTER_BRIDGE = "bab"
    STAR = "star"  # Situation, Task, Action, Result
    AIDA = "aida"  # Attention, Interest, Desire, Action
    PAS = "pas"    # Problem, Agitate, Solve
    SCQA = "scqa"  # Situation, Complication, Question, Answer
    MINTO = "minto"  # Pyramid Principle


FRAMEWORK_STRUCTURES = {
    StoryFramework.HEROS_JOURNEY: {
        "name": "Hero's Journey",
        "phases": [
            {"name": "Die gewöhnliche Welt", "slide_type": "problem", "purpose": "Status Quo zeigen"},
            {"name": "Der Ruf zum Abenteuer", "slide_type": "opportunity", "purpose": "Herausforderung präsentieren"},
            {"name": "Die Schwelle", "slide_type": "solution", "purpose": "Lösung einführen"},
            {"name": "Prüfungen & Verbündete", "slide_type": "approach", "purpose": "Methodik erklären"},
            {"name": "Die Transformation", "slide_type": "benefits", "purpose": "Nutzen zeigen"},
            {"name": "Die Rückkehr", "slide_type": "next_steps", "purpose": "Handlungsaufforderung"},
        ],
        "emotion_arc": ["neutral", "concern", "hope", "confidence", "excitement", "commitment"]
    },
    StoryFramework.PROBLEM_SOLUTION: {
        "name": "Problem-Lösung",
        "phases": [
            {"name": "Kontext", "slide_type": "context", "purpose": "Situation beschreiben"},
            {"name": "Problem", "slide_type": "problem", "purpose": "Schmerz verstärken"},
            {"name": "Implikationen", "slide_type": "impact", "purpose": "Konsequenzen zeigen"},
            {"name": "Lösung", "slide_type": "solution", "purpose": "Ansatz präsentieren"},
            {"name": "Beweis", "slide_type": "proof", "purpose": "Evidenz liefern"},
            {"name": "Handlung", "slide_type": "next_steps", "purpose": "Aktivierung"},
        ],
        "emotion_arc": ["curious", "concerned", "worried", "hopeful", "convinced", "motivated"]
    },
    StoryFramework.BEFORE_AFTER_BRIDGE: {
        "name": "Before-After-Bridge",
        "phases": [
            {"name": "Before (Vorher)", "slide_type": "problem", "purpose": "Aktuelle Situation"},
            {"name": "After (Nachher)", "slide_type": "vision", "purpose": "Gewünschte Zukunft"},
            {"name": "Bridge (Brücke)", "slide_type": "solution", "purpose": "Wie dorthin kommen"},
        ],
        "emotion_arc": ["frustrated", "excited", "empowered"]
    },
    StoryFramework.AIDA: {
        "name": "AIDA",
        "phases": [
            {"name": "Attention", "slide_type": "hook", "purpose": "Aufmerksamkeit gewinnen"},
            {"name": "Interest", "slide_type": "problem", "purpose": "Interesse wecken"},
            {"name": "Desire", "slide_type": "benefits", "purpose": "Verlangen erzeugen"},
            {"name": "Action", "slide_type": "next_steps", "purpose": "Handlung auslösen"},
        ],
        "emotion_arc": ["surprised", "curious", "wanting", "ready"]
    },
    StoryFramework.SCQA: {
        "name": "SCQA (McKinsey)",
        "phases": [
            {"name": "Situation", "slide_type": "context", "purpose": "Kontext etablieren"},
            {"name": "Complication", "slide_type": "problem", "purpose": "Komplikation zeigen"},
            {"name": "Question", "slide_type": "question", "purpose": "Kernfrage stellen"},
            {"name": "Answer", "slide_type": "solution", "purpose": "Antwort liefern"},
        ],
        "emotion_arc": ["neutral", "concerned", "curious", "confident"]
    },
    StoryFramework.MINTO: {
        "name": "Pyramid Principle (Minto)",
        "phases": [
            {"name": "Kernaussage", "slide_type": "executive_summary", "purpose": "Hauptbotschaft zuerst"},
            {"name": "Argument 1", "slide_type": "argument", "purpose": "Erster Stützpfeiler"},
            {"name": "Argument 2", "slide_type": "argument", "purpose": "Zweiter Stützpfeiler"},
            {"name": "Argument 3", "slide_type": "argument", "purpose": "Dritter Stützpfeiler"},
            {"name": "Details", "slide_type": "details", "purpose": "Unterstützende Fakten"},
        ],
        "emotion_arc": ["convinced", "understanding", "understanding", "understanding", "informed"]
    }
}


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class StoryPhase:
    """Eine Phase der Story."""
    name: str
    slide_type: str
    purpose: str
    content_hint: str = ""
    emotion: str = "neutral"
    hook: str = ""
    transition: str = ""


@dataclass
class NarrativeArc:
    """Der narrative Bogen der Präsentation."""
    framework: StoryFramework
    phases: List[StoryPhase]
    opening_hook: str = ""
    closing_call_to_action: str = ""
    key_message: str = ""
    emotional_journey: List[str] = field(default_factory=list)


@dataclass
class Hook:
    """Ein Aufhänger für den Einstieg."""
    type: str  # statistic, question, story, quote, provocation
    text: str
    impact_level: str = "Medium"  # Low, Medium, High


# ============================================
# LLM IMPORT
# ============================================

try:
    from services.llm import generate as llm_generate, is_enabled as llm_enabled
    HAS_LLM = True
except ImportError:
    llm_generate = None
    HAS_LLM = False


# ============================================
# FRAMEWORK DETECTION
# ============================================

def detect_best_framework(
    brief: str,
    audience: str = "",
    goal: str = "",
    deck_size: int = 15
) -> Tuple[StoryFramework, float, str]:
    """
    Erkennt das beste Storytelling-Framework.
    
    Args:
        brief: Das Projekt-Briefing
        audience: Zielgruppe
        goal: Präsentationsziel
        deck_size: Deckgröße
    
    Returns:
        Tuple von (Framework, Confidence, Rationale)
    """
    text = f"{brief} {audience} {goal}".lower()
    
    # Keyword-basierte Detection
    scores = {}
    
    # Problem-Solution für technische/analytische Audiences
    if any(kw in text for kw in ["problem", "lösung", "herausforderung", "technisch", "analyse"]):
        scores[StoryFramework.PROBLEM_SOLUTION] = 0.8
    
    # SCQA für C-Level/McKinsey-Style
    if any(kw in text for kw in ["c-level", "vorstand", "executive", "strategie", "management"]):
        scores[StoryFramework.SCQA] = 0.85
        scores[StoryFramework.MINTO] = 0.8
    
    # Hero's Journey für emotionale/transformative Pitches
    if any(kw in text for kw in ["transform", "wandel", "change", "vision", "zukunft"]):
        scores[StoryFramework.HEROS_JOURNEY] = 0.75
    
    # AIDA für Sales/Marketing
    if any(kw in text for kw in ["verkauf", "sales", "pitch", "überzeugen", "marketing"]):
        scores[StoryFramework.AIDA] = 0.85
    
    # Before-After-Bridge für kurze Decks
    if isinstance(deck_size, int) and deck_size <= 10:
        scores[StoryFramework.BEFORE_AFTER_BRIDGE] = 0.9
    
    # Default basierend auf Deck-Size
    if not scores:
        if isinstance(deck_size, int) and deck_size <= 10:
            scores[StoryFramework.BEFORE_AFTER_BRIDGE] = 0.7
        elif isinstance(deck_size, int) and deck_size >= 30:
            scores[StoryFramework.HEROS_JOURNEY] = 0.7
        else:
            scores[StoryFramework.PROBLEM_SOLUTION] = 0.7
    
    best = max(scores, key=scores.get)
    return best, scores[best], f"Basierend auf Briefing-Analyse und Deck-Size '{deck_size}'"


# ============================================
# HOOK GENERATION
# ============================================

def generate_hooks(
    topic: str,
    industry: str = "",
    audience: str = "",
    count: int = 3
) -> List[Hook]:
    """
    Generiert verschiedene Hooks für den Einstieg.
    
    Args:
        topic: Hauptthema
        industry: Branche
        audience: Zielgruppe
        count: Anzahl der Hooks
    
    Returns:
        Liste von Hook-Objekten
    """
    hooks = []
    
    # Hook-Templates
    templates = {
        "statistic": [
            f"Wussten Sie, dass 78% der Unternehmen in {industry or 'Ihrer Branche'} {topic} als Top-Priorität sehen?",
            f"Bis 2025 werden 85% der {industry or 'Unternehmen'} in {topic} investieren.",
            f"Unternehmen, die {topic} einsetzen, steigern ihre Effizienz um durchschnittlich 35%."
        ],
        "question": [
            f"Was wäre, wenn Sie {topic} in nur 6 Monaten transformieren könnten?",
            f"Wie viel kostet Sie jeder Tag, an dem Sie {topic} nicht optimieren?",
            f"Sind Sie bereit, Ihre Wettbewerber bei {topic} zu überholen?"
        ],
        "provocation": [
            f"Die meisten {industry or 'Unternehmen'} scheitern bei {topic}. Aber es muss nicht so sein.",
            f"Vergessen Sie alles, was Sie über {topic} zu wissen glauben.",
            f"In 3 Jahren wird {topic} der entscheidende Wettbewerbsvorteil sein. Sind Sie vorbereitet?"
        ],
        "story": [
            f"Ein {industry or 'mittelständisches'} Unternehmen stand vor dem gleichen Problem wie Sie. Hier ist, was passierte...",
            f"Vor zwei Jahren war {topic} noch ein Nischenthema. Heute entscheidet es über Erfolg oder Misserfolg.",
        ]
    }
    
    # LLM-basierte Hook-Generierung
    if HAS_LLM and llm_enabled and llm_enabled():
        prompt = f"""Generiere 3 starke Einstiegs-Hooks für eine Präsentation:

Thema: {topic}
Branche: {industry}
Zielgruppe: {audience}

Typen: 1 Statistik-Hook, 1 Frage-Hook, 1 provokativer Hook

Antworte NUR mit JSON:
{{"hooks": [
  {{"type": "statistic", "text": "...", "impact": "High"}},
  {{"type": "question", "text": "...", "impact": "High"}},
  {{"type": "provocation", "text": "...", "impact": "High"}}
]}}"""

        try:
            result = llm_generate(prompt, max_tokens=300)
            if result.get("ok"):
                response = result.get("response", "")
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    for h in data.get("hooks", [])[:count]:
                        hooks.append(Hook(
                            type=h.get("type", "question"),
                            text=h.get("text", ""),
                            impact_level=h.get("impact", "Medium")
                        ))
        except Exception:
            pass
    
    # Fallback zu Templates
    if len(hooks) < count:
        for hook_type, texts in templates.items():
            if len(hooks) >= count:
                break
            hooks.append(Hook(
                type=hook_type,
                text=texts[0],
                impact_level="Medium"
            ))
    
    return hooks[:count]


# ============================================
# CALL-TO-ACTION GENERATION
# ============================================

def generate_cta(
    topic: str,
    goal: str = "",
    urgency: str = "medium"
) -> Dict[str, Any]:
    """
    Generiert einen Call-to-Action.
    
    Args:
        topic: Hauptthema
        goal: Präsentationsziel
        urgency: Dringlichkeit (low, medium, high)
    
    Returns:
        Dictionary mit primary_cta, secondary_cta, urgency_element
    """
    ctas = {
        "low": {
            "primary": f"Lassen Sie uns über {topic} sprechen.",
            "secondary": "Kontaktieren Sie uns für weitere Informationen.",
            "urgency": ""
        },
        "medium": {
            "primary": f"Starten Sie jetzt mit {topic}.",
            "secondary": "Vereinbaren Sie ein unverbindliches Beratungsgespräch.",
            "urgency": "Die Zeit für Veränderung ist jetzt."
        },
        "high": {
            "primary": f"Handeln Sie heute – {topic} wartet nicht!",
            "secondary": "Buchen Sie jetzt Ihren Termin.",
            "urgency": "Jeder Tag Verzögerung kostet Sie bares Geld."
        }
    }
    
    base_cta = ctas.get(urgency, ctas["medium"])
    
    # LLM-Verbesserung
    if HAS_LLM and llm_enabled and llm_enabled():
        prompt = f"""Verbessere diesen Call-to-Action für eine {topic}-Präsentation:

Aktueller CTA: {base_cta['primary']}
Ziel: {goal}
Dringlichkeit: {urgency}

Generiere einen überzeugenden, aktionsorientierten CTA (max 15 Wörter).

Antworte NUR mit dem CTA-Text, keine JSON."""

        try:
            result = llm_generate(prompt, max_tokens=50)
            if result.get("ok"):
                response = result.get("response", "").strip()
                if len(response) > 10 and len(response) < 100:
                    base_cta["primary"] = response
        except Exception:
            pass
    
    return base_cta


# ============================================
# NARRATIVE ARC BUILDING
# ============================================

def build_narrative_arc(
    brief: str,
    topic: str,
    framework: StoryFramework = None,
    audience: str = "",
    goal: str = "",
    deck_size: int = 15
) -> NarrativeArc:
    """
    Baut den narrativen Bogen der Präsentation.
    
    Args:
        brief: Das Projekt-Briefing
        topic: Hauptthema
        framework: Optionales Framework (sonst automatisch)
        audience: Zielgruppe
        goal: Präsentationsziel
        deck_size: Deckgröße
    
    Returns:
        NarrativeArc-Objekt
    """
    # Framework bestimmen
    if not framework:
        framework, conf, rationale = detect_best_framework(brief, audience, goal, deck_size)
    
    structure = FRAMEWORK_STRUCTURES.get(framework, FRAMEWORK_STRUCTURES[StoryFramework.PROBLEM_SOLUTION])
    
    # Phasen aufbauen
    phases = []
    emotion_arc = structure.get("emotion_arc", [])
    
    for i, phase_def in enumerate(structure["phases"]):
        emotion = emotion_arc[i] if i < len(emotion_arc) else "neutral"
        
        phase = StoryPhase(
            name=phase_def["name"],
            slide_type=phase_def["slide_type"],
            purpose=phase_def["purpose"],
            emotion=emotion,
            transition=f"Überleitung zu: {structure['phases'][i+1]['name']}" if i < len(structure["phases"]) - 1 else "Abschluss"
        )
        phases.append(phase)
    
    # Hooks generieren
    hooks = generate_hooks(topic, "", audience, 1)
    opening_hook = hooks[0].text if hooks else f"Willkommen zu {topic}"
    
    # CTA generieren
    cta = generate_cta(topic, goal, "medium")
    
    return NarrativeArc(
        framework=framework,
        phases=phases,
        opening_hook=opening_hook,
        closing_call_to_action=cta["primary"],
        key_message=f"{topic}: {structure['phases'][0]['purpose']}",
        emotional_journey=emotion_arc
    )


# ============================================
# SLIDE TRANSITIONS
# ============================================

def generate_transitions(phases: List[StoryPhase]) -> List[str]:
    """
    Generiert fließende Übergänge zwischen Slides.
    
    Args:
        phases: Liste der Story-Phasen
    
    Returns:
        Liste von Übergangsätzen
    """
    transitions = []
    
    transition_templates = {
        "problem_to_solution": "Aber es gibt einen besseren Weg...",
        "solution_to_benefits": "Das bedeutet für Sie konkret...",
        "benefits_to_next_steps": "Um diese Vorteile zu realisieren...",
        "context_to_problem": "Doch hier liegt die Herausforderung...",
        "proof_to_next_steps": "Überzeugt? Dann lassen Sie uns handeln.",
    }
    
    for i, phase in enumerate(phases[:-1]):
        next_phase = phases[i + 1]
        key = f"{phase.slide_type}_to_{next_phase.slide_type}"
        
        transition = transition_templates.get(key, f"Kommen wir nun zu {next_phase.name}...")
        transitions.append(transition)
    
    return transitions


# ============================================
# SLIDE CONTENT ENHANCEMENT
# ============================================

def enhance_slide_with_narrative(
    slide: Dict[str, Any],
    phase: StoryPhase,
    position_in_deck: int,
    total_slides: int
) -> Dict[str, Any]:
    """
    Erweitert einen Slide mit narrativen Elementen.
    
    Args:
        slide: Der ursprüngliche Slide
        phase: Die aktuelle Story-Phase
        position_in_deck: Position im Deck
        total_slides: Gesamtzahl Slides
    
    Returns:
        Erweiterter Slide
    """
    enhanced = slide.copy()
    
    # Narrative Metadata hinzufügen
    enhanced["narrative"] = {
        "phase": phase.name,
        "purpose": phase.purpose,
        "emotion": phase.emotion,
        "transition": phase.transition if position_in_deck < total_slides - 1 else None
    }
    
    # Hook für ersten Content-Slide
    if position_in_deck == 1 and phase.hook:
        if enhanced.get("notes"):
            enhanced["notes"] = f"HOOK: {phase.hook}\n\n{enhanced['notes']}"
        else:
            enhanced["notes"] = f"HOOK: {phase.hook}"
    
    return enhanced


# ============================================
# API FUNCTIONS
# ============================================

def create_story_structure(
    brief: str,
    topic: str,
    audience: str = "",
    goal: str = "",
    deck_size: int = 15,
    framework: str = None
) -> Dict[str, Any]:
    """
    Hauptfunktion: Erstellt die Story-Struktur.
    
    Returns:
        Dictionary mit narrative_arc, hooks, transitions, recommended_slides
    """
    # Framework parsen
    fw = None
    if framework:
        try:
            fw = StoryFramework(framework)
        except ValueError:
            pass
    
    # Narrative Arc bauen
    arc = build_narrative_arc(brief, topic, fw, audience, goal, deck_size)
    
    # Transitions generieren
    transitions = generate_transitions(arc.phases)
    
    # Hooks generieren
    hooks = generate_hooks(topic, "", audience, 3)
    
    # Empfohlene Slide-Struktur - erweitert auf gewünschte deck_size
    base_slides = [
        {"type": phase.slide_type, "purpose": phase.purpose, "emotion": phase.emotion, "title": phase.name}
        for phase in arc.phases
    ]
    
    # deck_size ist int (Anzahl Slides vom Frontend-Schieberegler)
    target_count = int(deck_size) if isinstance(deck_size, (int, float)) else 15
    target_count = max(5, min(150, target_count))
    
    # Erweitere auf gewünschte Anzahl
    recommended_slides = list(base_slides)  # Kopie
    
    if len(recommended_slides) < target_count:
        # Zusätzliche Slide-Typen für Erweiterung
        expansion_types = [
            {"type": "data", "purpose": "Daten und Fakten präsentieren", "emotion": "analytical", "title": "Daten & Fakten"},
            {"type": "case_study", "purpose": "Praxisbeispiel zeigen", "emotion": "credible", "title": "Fallstudie"},
            {"type": "comparison", "purpose": "Alternativen vergleichen", "emotion": "rational", "title": "Vergleich"},
            {"type": "deep_dive", "purpose": "Details vertiefen", "emotion": "informative", "title": "Deep Dive"},
            {"type": "technical", "purpose": "Technische Details", "emotion": "precise", "title": "Technische Details"},
            {"type": "benefits", "purpose": "Vorteile hervorheben", "emotion": "positive", "title": "Ihre Vorteile"},
            {"type": "process", "purpose": "Prozess erklären", "emotion": "structured", "title": "Unser Prozess"},
            {"type": "timeline", "purpose": "Zeitplan zeigen", "emotion": "organized", "title": "Timeline"},
            {"type": "team", "purpose": "Team vorstellen", "emotion": "trustworthy", "title": "Unser Team"},
            {"type": "testimonial", "purpose": "Referenzen zeigen", "emotion": "credible", "title": "Referenzen"},
            {"type": "metrics", "purpose": "Erfolgskennzahlen", "emotion": "measurable", "title": "KPIs & Metriken"},
            {"type": "risks", "purpose": "Risiken adressieren", "emotion": "honest", "title": "Risiken & Mitigation"},
            {"type": "roadmap", "purpose": "Fahrplan zeigen", "emotion": "forward-looking", "title": "Roadmap"},
            {"type": "budget", "purpose": "Kosten darstellen", "emotion": "transparent", "title": "Budget & Investition"},
            {"type": "roi", "purpose": "Return on Investment", "emotion": "compelling", "title": "ROI / Business Case"},
            {"type": "implementation", "purpose": "Umsetzung planen", "emotion": "actionable", "title": "Implementierung"},
            {"type": "support", "purpose": "Support anbieten", "emotion": "reassuring", "title": "Support & Service"},
            {"type": "faq", "purpose": "Fragen beantworten", "emotion": "helpful", "title": "FAQ"},
            {"type": "appendix", "purpose": "Zusatzinfos", "emotion": "thorough", "title": "Anhang"},
        ]
        
        # Füge Slides vor dem letzten (CTA/Next Steps) ein
        insert_pos = max(1, len(recommended_slides) - 1)
        expansion_idx = 0
        
        while len(recommended_slides) < target_count and expansion_idx < len(expansion_types) * 3:
            slide = expansion_types[expansion_idx % len(expansion_types)].copy()
            
            # Bei Wiederholung: Nummerierung hinzufügen
            cycle = expansion_idx // len(expansion_types)
            if cycle > 0:
                slide["title"] = f"{slide['title']} ({cycle + 1})"
            
            recommended_slides.insert(insert_pos, slide)
            insert_pos += 1
            expansion_idx += 1
    
    return {
        "ok": True,
        "framework": {
            "id": arc.framework.value,
            "name": FRAMEWORK_STRUCTURES[arc.framework]["name"]
        },
        "narrative_arc": {
            "opening_hook": arc.opening_hook,
            "closing_cta": arc.closing_call_to_action,
            "key_message": arc.key_message,
            "emotional_journey": arc.emotional_journey
        },
        "phases": [asdict(p) for p in arc.phases],
        "transitions": transitions,
        "hooks": [asdict(h) for h in hooks],
        "recommended_slides": recommended_slides
    }


def list_frameworks() -> Dict[str, Any]:
    """Listet alle verfügbaren Storytelling-Frameworks."""
    frameworks = []
    for fw in StoryFramework:
        structure = FRAMEWORK_STRUCTURES.get(fw, {})
        frameworks.append({
            "id": fw.value,
            "name": structure.get("name", fw.value),
            "phases": len(structure.get("phases", [])),
            "best_for": structure.get("phases", [{}])[0].get("purpose", "")
        })
    
    return {"ok": True, "frameworks": frameworks}


def check_status() -> Dict[str, Any]:
    """Gibt den Status der Story Engine zurück."""
    return {
        "ok": True,
        "frameworks_available": len(StoryFramework),
        "llm_available": HAS_LLM and (llm_enabled() if llm_enabled else False),
        "features": ["framework_detection", "hook_generation", "cta_optimization", "narrative_arc", "transitions"]
    }
