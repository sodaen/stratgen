# -*- coding: utf-8 -*-
"""
services/argument_engine.py
===========================
Features:
- Argument Chain Builder
- Objection Handler
- Consistency Checker

Baut logische Argumentationsketten und prüft Konsistenz.

Author: StratGen Agent V3.6
"""
from __future__ import annotations
import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class ArgumentLink:
    """Ein Glied in der Argumentationskette."""
    type: str  # claim, evidence, reasoning, conclusion
    content: str
    strength: float  # 0-1
    sources: List[str] = field(default_factory=list)


@dataclass
class ArgumentChain:
    """Eine vollständige Argumentationskette."""
    thesis: str
    links: List[ArgumentLink]
    overall_strength: float
    gaps: List[str]  # Identifizierte Lücken


@dataclass
class Objection:
    """Ein möglicher Einwand."""
    objection: str
    severity: str  # low, medium, high
    counter_argument: str
    evidence_needed: str


@dataclass
class ConsistencyIssue:
    """Ein Konsistenzproblem."""
    type: str  # number, term, tone, logic
    description: str
    locations: List[str]  # Wo das Problem auftritt
    suggestion: str


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
# ARGUMENT CHAIN BUILDER
# ============================================

ARGUMENT_PATTERNS = {
    "problem_solution": [
        {"type": "claim", "template": "Das Problem: {problem}"},
        {"type": "evidence", "template": "Dies zeigt sich durch: {evidence}"},
        {"type": "reasoning", "template": "Die Auswirkungen sind: {impact}"},
        {"type": "claim", "template": "Unsere Lösung: {solution}"},
        {"type": "evidence", "template": "Beweis der Wirksamkeit: {proof}"},
        {"type": "conclusion", "template": "Daher empfehlen wir: {recommendation}"}
    ],
    "cause_effect": [
        {"type": "claim", "template": "Ursache: {cause}"},
        {"type": "reasoning", "template": "Mechanismus: {mechanism}"},
        {"type": "evidence", "template": "Beobachtete Effekte: {effects}"},
        {"type": "conclusion", "template": "Schlussfolgerung: {conclusion}"}
    ],
    "comparison": [
        {"type": "claim", "template": "Option A: {option_a}"},
        {"type": "claim", "template": "Option B: {option_b}"},
        {"type": "evidence", "template": "Vergleichskriterien: {criteria}"},
        {"type": "reasoning", "template": "Bewertung: {evaluation}"},
        {"type": "conclusion", "template": "Empfehlung: {recommendation}"}
    ]
}


def build_argument_chain(
    thesis: str,
    supporting_points: List[str],
    evidence: List[str] = None,
    pattern: str = "problem_solution"
) -> ArgumentChain:
    """
    Baut eine logische Argumentationskette.
    
    Args:
        thesis: Hauptthese
        supporting_points: Unterstützende Punkte
        evidence: Belege
        pattern: Argumentationsmuster
    
    Returns:
        ArgumentChain-Objekt
    """
    links = []
    gaps = []
    
    # Thesis als erstes Link
    links.append(ArgumentLink(
        type="thesis",
        content=thesis,
        strength=0.9 if len(thesis) > 20 else 0.6
    ))
    
    # Supporting Points als Claims
    for point in supporting_points:
        strength = 0.7
        if len(point) < 20:
            strength = 0.5
            gaps.append(f"Punkt zu kurz: '{point[:30]}...'")
        
        links.append(ArgumentLink(
            type="claim",
            content=point,
            strength=strength
        ))
    
    # Evidence
    if evidence:
        for ev in evidence:
            links.append(ArgumentLink(
                type="evidence",
                content=ev,
                strength=0.8,
                sources=["Knowledge Base"]
            ))
    else:
        gaps.append("Keine Belege/Evidenz angegeben")
    
    # Conclusion
    links.append(ArgumentLink(
        type="conclusion",
        content=f"Basierend auf {len(supporting_points)} Argumenten empfehlen wir die Umsetzung.",
        strength=0.7
    ))
    
    # Gesamtstärke berechnen
    if links:
        overall = sum(l.strength for l in links) / len(links)
        # Abzug für Lücken
        overall -= len(gaps) * 0.1
        overall = max(0.3, min(1.0, overall))
    else:
        overall = 0.3
    
    return ArgumentChain(
        thesis=thesis,
        links=links,
        overall_strength=round(overall, 2),
        gaps=gaps
    )


def strengthen_argument(chain: ArgumentChain, knowledge_base: List[str] = None) -> Dict[str, Any]:
    """
    Schlägt Verbesserungen für eine Argumentationskette vor.
    
    Args:
        chain: Die zu verbessernde Kette
        knowledge_base: Verfügbare Fakten
    
    Returns:
        Verbesserungsvorschläge
    """
    suggestions = []
    
    # Prüfe auf fehlende Evidence
    evidence_links = [l for l in chain.links if l.type == "evidence"]
    claim_links = [l for l in chain.links if l.type == "claim"]
    
    if len(evidence_links) < len(claim_links):
        suggestions.append({
            "type": "missing_evidence",
            "message": f"Nur {len(evidence_links)} Belege für {len(claim_links)} Behauptungen",
            "action": "Fügen Sie mehr Belege aus der Knowledge Base hinzu"
        })
    
    # Prüfe schwache Links
    weak_links = [l for l in chain.links if l.strength < 0.6]
    for link in weak_links:
        suggestions.append({
            "type": "weak_argument",
            "message": f"Schwaches Argument: '{link.content[:50]}...'",
            "action": "Konkretisieren Sie diesen Punkt"
        })
    
    # Knowledge Base Vorschläge
    if knowledge_base:
        suggestions.append({
            "type": "knowledge_available",
            "message": f"{len(knowledge_base)} relevante Fakten in Knowledge Base",
            "action": "Nutzen Sie diese als Belege"
        })
    
    return {
        "ok": True,
        "current_strength": chain.overall_strength,
        "potential_strength": min(1.0, chain.overall_strength + 0.2),
        "suggestions": suggestions,
        "gaps": chain.gaps
    }


# ============================================
# OBJECTION HANDLER
# ============================================

COMMON_OBJECTIONS = {
    "price": {
        "objections": [
            "Das ist zu teuer",
            "Das Budget reicht nicht",
            "Der ROI ist nicht klar"
        ],
        "counter_strategies": [
            "TCO-Vergleich zeigen",
            "ROI-Berechnung präsentieren",
            "Phasenweise Implementierung vorschlagen"
        ]
    },
    "risk": {
        "objections": [
            "Das Risiko ist zu hoch",
            "Wir haben schlechte Erfahrungen gemacht",
            "Was wenn es nicht funktioniert?"
        ],
        "counter_strategies": [
            "Risikomanagement-Plan zeigen",
            "Erfolgsgeschichten präsentieren",
            "Pilotprojekt anbieten"
        ]
    },
    "timing": {
        "objections": [
            "Jetzt ist nicht der richtige Zeitpunkt",
            "Wir haben andere Prioritäten",
            "Das dauert zu lange"
        ],
        "counter_strategies": [
            "Kosten des Abwartens aufzeigen",
            "Quick Wins identifizieren",
            "Agilen Ansatz vorschlagen"
        ]
    },
    "change": {
        "objections": [
            "Das Team wird das nicht akzeptieren",
            "Zu viel Veränderung auf einmal",
            "Wir machen das schon immer so"
        ],
        "counter_strategies": [
            "Change Management Plan zeigen",
            "Schrittweise Einführung",
            "Erfolge anderer Unternehmen"
        ]
    },
    "competition": {
        "objections": [
            "Wir arbeiten bereits mit X",
            "Was unterscheidet Sie vom Wettbewerb?",
            "Andere sind günstiger"
        ],
        "counter_strategies": [
            "Battle Card nutzen",
            "Differenzierungspunkte betonen",
            "Qualität vs. Preis argumentieren"
        ]
    }
}


def generate_objections(
    topic: str,
    industry: str = "",
    solution_type: str = ""
) -> List[Objection]:
    """
    Generiert typische Einwände für ein Thema.
    
    Args:
        topic: Das Thema/die Lösung
        industry: Branche
        solution_type: Art der Lösung
    
    Returns:
        Liste von Objection-Objekten
    """
    objections = []
    
    # Alle Kategorien durchgehen
    for category, data in COMMON_OBJECTIONS.items():
        obj = data["objections"][0]
        counter = data["counter_strategies"][0]
        
        objections.append(Objection(
            objection=obj,
            severity="medium",
            counter_argument=counter,
            evidence_needed=f"Daten zu {category} für {industry or 'Ihre Branche'}"
        ))
    
    # LLM für spezifischere Objections
    if HAS_LLM and llm_enabled and llm_enabled():
        prompt = f"""Generiere 3 typische Einwände gegen: {topic}
Branche: {industry or 'Allgemein'}

Antworte NUR mit JSON:
{{"objections": [
  {{"objection": "...", "severity": "high/medium/low", "counter": "..."}}
]}}"""
        
        try:
            result = llm_generate(prompt, max_tokens=200)
            if result.get("ok"):
                response = result.get("response", "")
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    for obj in data.get("objections", [])[:3]:
                        objections.append(Objection(
                            objection=obj.get("objection", ""),
                            severity=obj.get("severity", "medium"),
                            counter_argument=obj.get("counter", ""),
                            evidence_needed=""
                        ))
        except Exception:
            pass
    
    return objections


def create_objection_slide(objections: List[Objection]) -> Dict[str, Any]:
    """Erstellt einen Slide mit Einwand-Behandlung."""
    bullets = []
    for obj in objections[:4]:
        bullets.append(f"Einwand: \"{obj.objection}\"")
        bullets.append(f"→ {obj.counter_argument}")
    
    return {
        "type": "objection_handling",
        "title": "Häufige Fragen & Einwände",
        "bullets": bullets,
        "notes": "Proaktive Behandlung typischer Einwände",
        "layout_hint": "Title and Content"
    }


# ============================================
# CONSISTENCY CHECKER
# ============================================

def check_number_consistency(slides: List[Dict[str, Any]]) -> List[ConsistencyIssue]:
    """Prüft Zahlen-Konsistenz über alle Slides."""
    issues = []
    
    # Zahlen mit Kontext sammeln
    numbers = defaultdict(list)
    
    for idx, slide in enumerate(slides):
        text = f"{slide.get('title', '')} {' '.join(slide.get('bullets', []))}"
        
        # Prozente
        for match in re.finditer(r'(\d+(?:[.,]\d+)?)\s*%', text):
            value = match.group(1)
            context = text[max(0, match.start()-20):match.end()+20]
            numbers[f"percent_{value}"].append((idx, context))
        
        # Euro-Beträge
        for match in re.finditer(r'(\d+(?:[.,]\d+)?)\s*(?:€|EUR|Euro|Mio)', text):
            value = match.group(1)
            context = text[max(0, match.start()-20):match.end()+20]
            numbers[f"euro_{value}"].append((idx, context))
    
    # Prüfe auf widersprüchliche Zahlen
    for key, occurrences in numbers.items():
        if len(occurrences) > 1:
            contexts = [o[1] for o in occurrences]
            # Prüfe ob gleiche Zahl in unterschiedlichem Kontext
            # TODO: Smarter Vergleich
    
    return issues


def check_term_consistency(slides: List[Dict[str, Any]]) -> List[ConsistencyIssue]:
    """Prüft Begriffskonsistenz."""
    issues = []
    
    # Bekannte Synonyme
    synonym_groups = [
        ["KI", "AI", "Künstliche Intelligenz", "Artificial Intelligence"],
        ["ML", "Machine Learning", "maschinelles Lernen"],
        ["ROI", "Return on Investment", "Rendite"],
        ["Digitalisierung", "digitale Transformation", "Digital Transformation"],
    ]
    
    term_usage = defaultdict(list)
    
    for idx, slide in enumerate(slides):
        text = f"{slide.get('title', '')} {' '.join(slide.get('bullets', []))}".lower()
        
        for group in synonym_groups:
            used_terms = [t for t in group if t.lower() in text]
            if used_terms:
                for term in used_terms:
                    term_usage[tuple(group)].append((idx, term))
    
    # Prüfe auf inkonsistente Verwendung
    for group, usages in term_usage.items():
        terms_used = set(u[1] for u in usages)
        if len(terms_used) > 1:
            issues.append(ConsistencyIssue(
                type="term",
                description=f"Inkonsistente Begriffe: {', '.join(terms_used)}",
                locations=[f"Slide {u[0]+1}" for u in usages],
                suggestion=f"Einheitlich '{list(terms_used)[0]}' verwenden"
            ))
    
    return issues


def check_tone_consistency(slides: List[Dict[str, Any]]) -> List[ConsistencyIssue]:
    """Prüft Tonalitäts-Konsistenz."""
    issues = []
    
    formal_indicators = ["gemäß", "hinsichtlich", "gewährleisten", "implementieren"]
    informal_indicators = ["super", "toll", "cool", "easy", "halt"]
    
    slide_tones = []
    
    for idx, slide in enumerate(slides):
        text = f"{slide.get('title', '')} {' '.join(slide.get('bullets', []))}".lower()
        
        formal_count = sum(1 for w in formal_indicators if w in text)
        informal_count = sum(1 for w in informal_indicators if w in text)
        
        if formal_count > informal_count:
            slide_tones.append((idx, "formal"))
        elif informal_count > formal_count:
            slide_tones.append((idx, "informal"))
        else:
            slide_tones.append((idx, "neutral"))
    
    # Prüfe auf Tonalitätswechsel
    tone_changes = []
    for i in range(1, len(slide_tones)):
        if slide_tones[i][1] != slide_tones[i-1][1] and \
           slide_tones[i][1] != "neutral" and slide_tones[i-1][1] != "neutral":
            tone_changes.append((i, slide_tones[i-1][1], slide_tones[i][1]))
    
    if tone_changes:
        issues.append(ConsistencyIssue(
            type="tone",
            description="Tonalitätswechsel erkannt",
            locations=[f"Slide {c[0]} ({c[1]}→{c[2]})" for c in tone_changes],
            suggestion="Einheitliche Tonalität über alle Slides"
        ))
    
    return issues


def check_deck_consistency(slides: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Führt vollständige Konsistenzprüfung durch.
    
    Args:
        slides: Liste der Slides
    
    Returns:
        Dictionary mit allen Issues
    """
    all_issues = []
    
    all_issues.extend(check_number_consistency(slides))
    all_issues.extend(check_term_consistency(slides))
    all_issues.extend(check_tone_consistency(slides))
    
    # Qualitätsscore
    base_score = 100
    score = base_score - len(all_issues) * 10
    score = max(0, min(100, score))
    
    return {
        "ok": True,
        "consistency_score": score,
        "issues_found": len(all_issues),
        "issues": [asdict(i) for i in all_issues],
        "recommendations": [i.suggestion for i in all_issues]
    }


# ============================================
# API FUNCTIONS
# ============================================

def check_status() -> Dict[str, Any]:
    """Gibt den Status der Argument Engine zurück."""
    return {
        "ok": True,
        "features": ["argument_chain", "objection_handler", "consistency_checker"],
        "objection_categories": list(COMMON_OBJECTIONS.keys()),
        "llm_available": HAS_LLM and (llm_enabled() if llm_enabled else False)
    }
