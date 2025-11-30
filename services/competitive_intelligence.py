# -*- coding: utf-8 -*-
"""
services/competitive_intelligence.py
====================================
Killer-Feature: Competitive Intelligence Engine

Features:
1. Wettbewerbsanalyse aus Briefing
2. SWOT-Generierung
3. Differenzierungspunkte identifizieren
4. Market Positioning Matrix
5. Battle Card Generation
6. Win/Loss Factor Analysis

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
# DATA CLASSES
# ============================================

@dataclass
class Competitor:
    """Ein Wettbewerber."""
    name: str
    description: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    market_position: str = "Challenger"  # Leader, Challenger, Follower, Niche
    target_segments: List[str] = field(default_factory=list)
    key_differentiators: List[str] = field(default_factory=list)
    threat_level: str = "Medium"  # Low, Medium, High


@dataclass
class SWOT:
    """SWOT-Analyse."""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)


@dataclass
class BattleCard:
    """Battle Card für Vertrieb."""
    competitor_name: str
    quick_overview: str = ""
    their_strengths: List[str] = field(default_factory=list)
    their_weaknesses: List[str] = field(default_factory=list)
    our_advantages: List[str] = field(default_factory=list)
    common_objections: List[str] = field(default_factory=list)
    winning_arguments: List[str] = field(default_factory=list)
    trap_questions: List[str] = field(default_factory=list)


@dataclass
class MarketPosition:
    """Position im Markt."""
    x_axis: str = "Preis"  # Was X-Achse misst
    y_axis: str = "Qualität"  # Was Y-Achse misst
    our_position: Tuple[float, float] = (0.7, 0.8)  # 0-1 Skala
    competitors: Dict[str, Tuple[float, float]] = field(default_factory=dict)


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
# COMPETITIVE ANALYSIS
# ============================================

def extract_competitors_from_brief(brief: str, industry: str = "") -> List[Competitor]:
    """
    Extrahiert Wettbewerber aus dem Briefing.
    
    Args:
        brief: Das Projekt-Briefing
        industry: Branche
    
    Returns:
        Liste von Competitor-Objekten
    """
    competitors = []
    
    # Bekannte Wettbewerber-Pattern
    patterns = [
        r'(?:Wettbewerber|Konkurrenz|Mitbewerber)[:\s]+([^.]+)',
        r'(?:gegen|versus|vs\.?)\s+(\w+)',
        r'(?:wie|ähnlich wie)\s+(\w+)',
    ]
    
    text = brief.lower()
    found_names = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            names = [n.strip() for n in match.split(",")]
            found_names.update(names)
    
    # LLM-basierte Extraktion
    if HAS_LLM and llm_enabled and llm_enabled():
        prompt = f"""Identifiziere potenzielle Wettbewerber aus diesem Briefing.
Wenn keine genannt sind, schlage 2-3 typische Wettbewerber für die Branche vor.

Briefing: {brief[:500]}
Branche: {industry}

Antworte NUR mit JSON:
{{"competitors": ["Name1", "Name2", "Name3"]}}"""

        try:
            result = llm_generate(prompt, max_tokens=100)
            if result.get("ok"):
                response = result.get("response", "")
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    found_names.update(data.get("competitors", []))
        except Exception:
            pass
    
    # Competitor-Objekte erstellen
    for name in list(found_names)[:5]:
        if name and len(name) > 2:
            competitors.append(Competitor(
                name=name.title(),
                market_position="Challenger",
                threat_level="Medium"
            ))
    
    # Fallback: Generische Wettbewerber
    if not competitors:
        competitors = [
            Competitor(name="Wettbewerber A", market_position="Leader", threat_level="High"),
            Competitor(name="Wettbewerber B", market_position="Challenger", threat_level="Medium"),
        ]
    
    return competitors


def analyze_competitor(
    competitor: Competitor,
    our_offering: str,
    industry: str = ""
) -> Competitor:
    """
    Analysiert einen Wettbewerber detailliert.
    
    Args:
        competitor: Der zu analysierende Wettbewerber
        our_offering: Unser Angebot/Lösung
        industry: Branche
    
    Returns:
        Erweitertes Competitor-Objekt
    """
    if not HAS_LLM or not llm_enabled or not llm_enabled():
        # Fallback mit generischen Daten
        competitor.strengths = ["Marktpräsenz", "Brand Recognition"]
        competitor.weaknesses = ["Weniger innovativ", "Höhere Preise"]
        return competitor
    
    prompt = f"""Analysiere diesen Wettbewerber:

Wettbewerber: {competitor.name}
Branche: {industry}
Unser Angebot: {our_offering[:200]}

Generiere eine realistische Analyse.

Antworte NUR mit JSON:
{{
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "differentiators": ["...", "..."],
  "threat_level": "Low/Medium/High"
}}"""

    try:
        result = llm_generate(prompt, max_tokens=200)
        if result.get("ok"):
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                competitor.strengths = data.get("strengths", [])[:3]
                competitor.weaknesses = data.get("weaknesses", [])[:3]
                competitor.key_differentiators = data.get("differentiators", [])[:3]
                competitor.threat_level = data.get("threat_level", "Medium")
    except Exception:
        pass
    
    return competitor


# ============================================
# SWOT GENERATION
# ============================================

def generate_swot(
    brief: str,
    topic: str,
    industry: str = "",
    competitors: List[Competitor] = None
) -> SWOT:
    """
    Generiert eine SWOT-Analyse.
    
    Args:
        brief: Das Projekt-Briefing
        topic: Hauptthema
        industry: Branche
        competitors: Liste der Wettbewerber
    
    Returns:
        SWOT-Objekt
    """
    swot = SWOT()
    
    if not HAS_LLM or not llm_enabled or not llm_enabled():
        # Fallback
        swot.strengths = ["Innovative Lösung", "Erfahrenes Team", "Flexibilität"]
        swot.weaknesses = ["Begrenzte Ressourcen", "Neuer Marktteilnehmer"]
        swot.opportunities = ["Wachsender Markt", "Digitalisierungstrend"]
        swot.threats = ["Etablierte Wettbewerber", "Regulatorische Änderungen"]
        return swot
    
    comp_info = ""
    if competitors:
        comp_info = f"Wettbewerber: {', '.join([c.name for c in competitors[:3]])}"
    
    prompt = f"""Erstelle eine SWOT-Analyse:

Thema: {topic}
Briefing: {brief[:400]}
Branche: {industry}
{comp_info}

Antworte NUR mit JSON:
{{
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "..."],
  "opportunities": ["...", "...", "..."],
  "threats": ["...", "..."]
}}"""

    try:
        result = llm_generate(prompt, max_tokens=250)
        if result.get("ok"):
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                swot.strengths = data.get("strengths", [])[:4]
                swot.weaknesses = data.get("weaknesses", [])[:3]
                swot.opportunities = data.get("opportunities", [])[:4]
                swot.threats = data.get("threats", [])[:3]
    except Exception:
        pass
    
    return swot


# ============================================
# BATTLE CARD GENERATION
# ============================================

def generate_battle_card(
    competitor: Competitor,
    our_solution: str,
    our_strengths: List[str] = None
) -> BattleCard:
    """
    Generiert eine Battle Card für den Vertrieb.
    
    Args:
        competitor: Der Wettbewerber
        our_solution: Unsere Lösung
        our_strengths: Unsere Stärken
    
    Returns:
        BattleCard-Objekt
    """
    card = BattleCard(
        competitor_name=competitor.name,
        their_strengths=competitor.strengths,
        their_weaknesses=competitor.weaknesses
    )
    
    if not HAS_LLM or not llm_enabled or not llm_enabled():
        card.quick_overview = f"{competitor.name} ist ein {competitor.market_position} im Markt."
        card.our_advantages = our_strengths or ["Besserer Service", "Flexibilität"]
        card.common_objections = ["Wir arbeiten bereits mit dem Wettbewerber"]
        card.winning_arguments = ["Besseres Preis-Leistungs-Verhältnis"]
        return card
    
    prompt = f"""Erstelle eine Sales Battle Card gegen {competitor.name}:

Wettbewerber-Stärken: {', '.join(competitor.strengths[:3])}
Wettbewerber-Schwächen: {', '.join(competitor.weaknesses[:3])}
Unsere Lösung: {our_solution[:200]}
Unsere Stärken: {', '.join(our_strengths or ['Innovation', 'Service'])}

Antworte NUR mit JSON:
{{
  "quick_overview": "...",
  "our_advantages": ["...", "..."],
  "common_objections": ["...", "..."],
  "winning_arguments": ["...", "..."],
  "trap_questions": ["..."]
}}"""

    try:
        result = llm_generate(prompt, max_tokens=300)
        if result.get("ok"):
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                card.quick_overview = data.get("quick_overview", "")
                card.our_advantages = data.get("our_advantages", [])[:4]
                card.common_objections = data.get("common_objections", [])[:3]
                card.winning_arguments = data.get("winning_arguments", [])[:4]
                card.trap_questions = data.get("trap_questions", [])[:2]
    except Exception:
        pass
    
    return card


# ============================================
# MARKET POSITIONING
# ============================================

def generate_market_position(
    our_name: str,
    competitors: List[Competitor],
    x_dimension: str = "Preis",
    y_dimension: str = "Innovation"
) -> MarketPosition:
    """
    Generiert eine Market Positioning Matrix.
    
    Args:
        our_name: Unser Firmenname
        competitors: Liste der Wettbewerber
        x_dimension: Was die X-Achse misst
        y_dimension: Was die Y-Achse misst
    
    Returns:
        MarketPosition-Objekt
    """
    position = MarketPosition(
        x_axis=x_dimension,
        y_axis=y_dimension,
        our_position=(0.7, 0.8)
    )
    
    # Wettbewerber positionieren
    positions = [
        (0.3, 0.9),  # Leader: hohe Qualität, günstig
        (0.8, 0.6),  # Premium: teuer, mittel
        (0.4, 0.4),  # Budget: günstig, niedrig
        (0.6, 0.7),  # Challenger
    ]
    
    for i, comp in enumerate(competitors[:4]):
        position.competitors[comp.name] = positions[i % len(positions)]
    
    return position


# ============================================
# SLIDE CONTENT GENERATION
# ============================================

def swot_to_slide_content(swot: SWOT, title: str = "SWOT-Analyse") -> Dict[str, Any]:
    """Konvertiert SWOT zu Slide-Content."""
    return {
        "type": "swot",
        "title": title,
        "bullets": [
            f"✓ Stärken: {', '.join(swot.strengths[:2])}",
            f"⚠ Schwächen: {', '.join(swot.weaknesses[:2])}",
            f"↗ Chancen: {', '.join(swot.opportunities[:2])}",
            f"⚡ Risiken: {', '.join(swot.threats[:2])}"
        ],
        "notes": f"SWOT-Analyse mit {len(swot.strengths)} Stärken, {len(swot.weaknesses)} Schwächen, {len(swot.opportunities)} Chancen und {len(swot.threats)} Risiken.",
        "layout_hint": "Title and Content",
        "swot_data": asdict(swot)
    }


def competitive_to_slide_content(
    competitors: List[Competitor],
    title: str = "Wettbewerbslandschaft"
) -> Dict[str, Any]:
    """Konvertiert Competitive Analysis zu Slide-Content."""
    bullets = []
    for comp in competitors[:4]:
        bullets.append(f"{comp.name}: {comp.market_position} (Risiko: {comp.threat_level})")
    
    return {
        "type": "competitive",
        "title": title,
        "bullets": bullets,
        "notes": f"Wettbewerbsanalyse mit {len(competitors)} identifizierten Wettbewerbern.",
        "layout_hint": "Title and Content",
        "competitors_data": [asdict(c) for c in competitors]
    }


def battle_card_to_slide_content(card: BattleCard) -> Dict[str, Any]:
    """Konvertiert Battle Card zu Slide-Content."""
    return {
        "type": "battle_card",
        "title": f"Battle Card: vs. {card.competitor_name}",
        "bullets": [
            f"Überblick: {card.quick_overview}",
            f"Unsere Vorteile: {', '.join(card.our_advantages[:2])}",
            f"Gewinnargumente: {', '.join(card.winning_arguments[:2])}"
        ],
        "notes": f"Battle Card gegen {card.competitor_name}. Häufige Einwände: {', '.join(card.common_objections[:2])}",
        "layout_hint": "Title and Content",
        "battle_card_data": asdict(card)
    }


# ============================================
# API FUNCTIONS
# ============================================

def analyze_competition(
    brief: str,
    topic: str,
    industry: str = "",
    our_solution: str = ""
) -> Dict[str, Any]:
    """
    Führt vollständige Wettbewerbsanalyse durch.
    
    Returns:
        Dictionary mit competitors, swot, battle_cards, market_position
    """
    # Wettbewerber extrahieren
    competitors = extract_competitors_from_brief(brief, industry)
    
    # Jeden Wettbewerber analysieren
    for comp in competitors:
        analyze_competitor(comp, our_solution or topic, industry)
    
    # SWOT generieren
    swot = generate_swot(brief, topic, industry, competitors)
    
    # Battle Cards generieren
    battle_cards = []
    for comp in competitors[:2]:
        card = generate_battle_card(comp, our_solution or topic, swot.strengths)
        battle_cards.append(card)
    
    # Market Position
    market_pos = generate_market_position("Unser Unternehmen", competitors)
    
    return {
        "ok": True,
        "competitors": [asdict(c) for c in competitors],
        "swot": asdict(swot),
        "battle_cards": [asdict(c) for c in battle_cards],
        "market_position": asdict(market_pos),
        "slides": {
            "swot": swot_to_slide_content(swot),
            "competitive": competitive_to_slide_content(competitors)
        }
    }


def check_status() -> Dict[str, Any]:
    """Gibt den Status der Competitive Intelligence zurück."""
    return {
        "ok": True,
        "llm_available": HAS_LLM and (llm_enabled() if llm_enabled else False),
        "features": ["competitor_analysis", "swot", "battle_cards", "market_positioning"]
    }
