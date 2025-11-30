# -*- coding: utf-8 -*-
"""
services/briefing_analyzer.py
=============================
Killer-Feature: Smart Briefing Analyzer

Features:
1. Automatische Briefing-Analyse
2. Fehlende Informationen identifizieren
3. Briefing-Qualitätsscore
4. Vorschläge zur Verbesserung
5. Automatische Kategorisierung
6. Entity Extraction (Firmen, Personen, Zahlen)
7. Intent Detection

Author: StratGen Agent V3.5
"""
from __future__ import annotations
import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================
# ENUMS
# ============================================

class BriefingQuality(str, Enum):
    """Qualitätsstufen eines Briefings."""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"            # 70-89%
    FAIR = "fair"            # 50-69%
    POOR = "poor"            # 30-49%
    INSUFFICIENT = "insufficient"  # <30%


class PresentationIntent(str, Enum):
    """Hauptintention der Präsentation."""
    INFORM = "inform"          # Informieren
    PERSUADE = "persuade"      # Überzeugen
    SELL = "sell"              # Verkaufen
    EDUCATE = "educate"        # Schulen
    REPORT = "report"          # Berichten
    PITCH = "pitch"            # Pitchen
    STRATEGY = "strategy"      # Strategie vorstellen


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class ExtractedEntity:
    """Eine extrahierte Entität."""
    type: str  # company, person, number, date, product, technology
    value: str
    context: str = ""
    confidence: float = 0.8


@dataclass
class MissingInformation:
    """Eine fehlende Information."""
    category: str
    description: str
    importance: str = "Medium"  # Low, Medium, High, Critical
    suggestion: str = ""


@dataclass
class BriefingAnalysis:
    """Vollständige Briefing-Analyse."""
    quality_score: float  # 0-100
    quality_level: BriefingQuality
    intent: PresentationIntent
    
    # Extrahierte Informationen
    entities: List[ExtractedEntity] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Erkannte Elemente
    has_customer_info: bool = False
    has_industry_info: bool = False
    has_timeline: bool = False
    has_budget: bool = False
    has_goals: bool = False
    has_audience: bool = False
    has_competitors: bool = False
    
    # Fehlende Informationen
    missing: List[MissingInformation] = field(default_factory=list)
    
    # Empfehlungen
    recommendations: List[str] = field(default_factory=list)
    
    # Deck-Empfehlung
    recommended_deck_size: str = "medium"
    recommended_slide_types: List[str] = field(default_factory=list)


# ============================================
# REQUIRED FIELDS
# ============================================

REQUIRED_FIELDS = {
    "customer_info": {
        "keywords": ["kunde", "klient", "auftraggeber", "unternehmen", "firma", "gmbh", "ag", "company"],
        "importance": "High",
        "description": "Kundeninformationen",
        "suggestion": "Nennen Sie den Kundennamen und relevante Unternehmensinformationen."
    },
    "industry": {
        "keywords": ["branche", "industrie", "sektor", "bereich", "markt"],
        "importance": "High",
        "description": "Brancheninformationen",
        "suggestion": "Geben Sie die Branche des Kunden an (z.B. Fertigung, IT, Healthcare)."
    },
    "goals": {
        "keywords": ["ziel", "erreichen", "outcome", "ergebnis", "zweck", "absicht", "intention"],
        "importance": "Critical",
        "description": "Präsentationsziel",
        "suggestion": "Was soll die Präsentation erreichen? (z.B. Überzeugung, Entscheidung, Information)"
    },
    "audience": {
        "keywords": ["zielgruppe", "publikum", "empfänger", "entscheider", "c-level", "management", "team"],
        "importance": "High",
        "description": "Zielgruppe",
        "suggestion": "Wer ist die Zielgruppe? (z.B. C-Level, Fachabteilung, Mitarbeiter)"
    },
    "timeline": {
        "keywords": ["termin", "deadline", "datum", "wann", "zeitplan", "timeline", "bis zum"],
        "importance": "Medium",
        "description": "Zeitrahmen",
        "suggestion": "Gibt es einen Termin oder Zeitrahmen für die Präsentation?"
    },
    "budget": {
        "keywords": ["budget", "kosten", "investition", "preis", "euro", "€", "betrag"],
        "importance": "Medium",
        "description": "Budget/Kosten",
        "suggestion": "Gibt es Budgetinformationen oder Kostenrahmen?"
    },
    "competitors": {
        "keywords": ["wettbewerb", "konkurrenz", "mitbewerber", "alternative", "vergleich"],
        "importance": "Low",
        "description": "Wettbewerbsinformationen",
        "suggestion": "Gibt es relevante Wettbewerber oder Alternativen?"
    }
}


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
# ENTITY EXTRACTION
# ============================================

def extract_entities(text: str) -> List[ExtractedEntity]:
    """
    Extrahiert Entitäten aus dem Text.
    
    Args:
        text: Der zu analysierende Text
    
    Returns:
        Liste von ExtractedEntity-Objekten
    """
    entities = []
    
    # Firmen (GmbH, AG, etc.)
    company_pattern = r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)\s*(?:GmbH|AG|SE|KG|e\.V\.|Inc\.|Ltd\.)'
    for match in re.finditer(company_pattern, text):
        entities.append(ExtractedEntity(
            type="company",
            value=match.group(0),
            confidence=0.9
        ))
    
    # Zahlen mit Kontext
    number_patterns = [
        (r'(\d+(?:[.,]\d+)?)\s*(?:€|EUR|Euro)', "currency"),
        (r'(\d+(?:[.,]\d+)?)\s*(?:Mio\.?|Millionen)', "millions"),
        (r'(\d+(?:[.,]\d+)?)\s*%', "percentage"),
        (r'(\d+)\s*(?:Mitarbeiter|MA|Angestellte)', "employees"),
    ]
    
    for pattern, num_type in number_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Kontext extrahieren
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()
            
            entities.append(ExtractedEntity(
                type="number",
                value=match.group(0),
                context=context,
                confidence=0.85
            ))
    
    # Datumsangaben
    date_pattern = r'(\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}|Q[1-4]\s*\d{4}|(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4})'
    for match in re.finditer(date_pattern, text, re.IGNORECASE):
        entities.append(ExtractedEntity(
            type="date",
            value=match.group(0),
            confidence=0.8
        ))
    
    # Technologien
    tech_keywords = ["KI", "AI", "ML", "Cloud", "SaaS", "IoT", "Blockchain", "API", "ERP", "CRM", "Digital"]
    for tech in tech_keywords:
        if re.search(rf'\b{tech}\b', text, re.IGNORECASE):
            entities.append(ExtractedEntity(
                type="technology",
                value=tech,
                confidence=0.75
            ))
    
    return entities


# ============================================
# INTENT DETECTION
# ============================================

def detect_intent(text: str) -> Tuple[PresentationIntent, float]:
    """
    Erkennt die Hauptintention der Präsentation.
    
    Args:
        text: Der Briefing-Text
    
    Returns:
        Tuple von (Intent, Confidence)
    """
    text_lower = text.lower()
    
    intent_keywords = {
        PresentationIntent.SELL: ["verkaufen", "sales", "angebot", "preis", "abschluss", "deal", "contract"],
        PresentationIntent.PITCH: ["pitch", "startup", "investor", "funding", "idee", "konzept"],
        PresentationIntent.PERSUADE: ["überzeugen", "gewinnen", "vorschlag", "empfehlung", "proposal"],
        PresentationIntent.INFORM: ["informieren", "update", "status", "bericht", "zusammenfassung"],
        PresentationIntent.EDUCATE: ["schulen", "training", "workshop", "lernen", "onboarding"],
        PresentationIntent.REPORT: ["report", "analyse", "ergebnis", "quarterly", "jahres"],
        PresentationIntent.STRATEGY: ["strategie", "roadmap", "planung", "vision", "zukunft"],
    }
    
    scores = {}
    for intent, keywords in intent_keywords.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[intent] = score
    
    if scores:
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        confidence = min(0.9, 0.4 + max_score * 0.15)
        return best_intent, confidence
    
    return PresentationIntent.INFORM, 0.5


# ============================================
# KEYWORD EXTRACTION
# ============================================

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extrahiert wichtige Keywords aus dem Text.
    
    Args:
        text: Der zu analysierende Text
        max_keywords: Maximale Anzahl Keywords
    
    Returns:
        Liste von Keywords
    """
    # Stopwords
    stopwords = {"der", "die", "das", "und", "oder", "aber", "für", "mit", "von", "zu", "in", "auf",
                 "ist", "sind", "wird", "werden", "hat", "haben", "ein", "eine", "einer", "eines",
                 "sich", "als", "auch", "bei", "nach", "aus", "wenn", "kann", "soll", "muss",
                 "the", "a", "an", "and", "or", "for", "with", "to", "in", "on", "is", "are"}
    
    # Wörter extrahieren
    words = re.findall(r'\b[A-ZÄÖÜa-zäöüß]{3,}\b', text)
    
    # Zählen
    word_counts = {}
    for word in words:
        if word.lower() not in stopwords:
            key = word.lower()
            word_counts[key] = word_counts.get(key, 0) + 1
    
    # Nach Häufigkeit sortieren
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, count in sorted_words[:max_keywords]]


# ============================================
# MAIN ANALYSIS
# ============================================

def analyze_briefing(
    brief: str,
    topic: str = "",
    industry: str = "",
    customer_name: str = ""
) -> BriefingAnalysis:
    """
    Analysiert ein Briefing vollständig.
    
    Args:
        brief: Das Briefing
        topic: Optionales Thema
        industry: Optionale Branche
        customer_name: Optionaler Kundenname
    
    Returns:
        BriefingAnalysis-Objekt
    """
    full_text = f"{topic} {brief} {industry} {customer_name}"
    text_lower = full_text.lower()
    
    # Basis-Analyse
    entities = extract_entities(full_text)
    intent, intent_conf = detect_intent(full_text)
    keywords = extract_keywords(brief)
    
    # Pflichtfelder prüfen
    score = 0
    max_score = 0
    missing = []
    
    checks = {
        "has_customer_info": False,
        "has_industry_info": False,
        "has_timeline": False,
        "has_budget": False,
        "has_goals": False,
        "has_audience": False,
        "has_competitors": False
    }
    
    for field_name, field_info in REQUIRED_FIELDS.items():
        importance = field_info["importance"]
        weight = {"Critical": 25, "High": 20, "Medium": 10, "Low": 5}.get(importance, 10)
        max_score += weight
        
        # Prüfen ob Keywords vorhanden
        found = any(kw in text_lower for kw in field_info["keywords"])
        
        # Zusätzliche Checks
        if field_name == "customer_info" and customer_name:
            found = True
        if field_name == "industry" and industry:
            found = True
        
        if found:
            score += weight
            check_key = f"has_{field_name.replace('_info', '')}" if "_info" in field_name else f"has_{field_name}"
            if check_key in checks:
                checks[check_key] = True
        else:
            missing.append(MissingInformation(
                category=field_name,
                description=field_info["description"],
                importance=importance,
                suggestion=field_info["suggestion"]
            ))
    
    # Textlänge bewerten
    word_count = len(brief.split())
    if word_count > 100:
        score += 10
    elif word_count > 50:
        score += 5
    max_score += 10
    
    # Quality Score berechnen
    quality_score = (score / max_score * 100) if max_score > 0 else 0
    
    # Quality Level bestimmen
    if quality_score >= 90:
        quality_level = BriefingQuality.EXCELLENT
    elif quality_score >= 70:
        quality_level = BriefingQuality.GOOD
    elif quality_score >= 50:
        quality_level = BriefingQuality.FAIR
    elif quality_score >= 30:
        quality_level = BriefingQuality.POOR
    else:
        quality_level = BriefingQuality.INSUFFICIENT
    
    # Deck-Size Empfehlung
    if word_count < 50:
        recommended_deck_size = "short"
    elif word_count > 200:
        recommended_deck_size = "long"
    else:
        recommended_deck_size = "medium"
    
    # Slide-Types Empfehlung basierend auf Intent
    slide_type_map = {
        PresentationIntent.SELL: ["title", "problem", "solution", "benefits", "roi", "next_steps", "contact"],
        PresentationIntent.PITCH: ["title", "problem", "solution", "market", "team", "roadmap", "contact"],
        PresentationIntent.PERSUADE: ["title", "executive_summary", "problem", "solution", "benefits", "next_steps"],
        PresentationIntent.INFORM: ["title", "agenda", "content", "content", "content", "summary"],
        PresentationIntent.EDUCATE: ["title", "agenda", "content", "content", "content", "exercise", "summary"],
        PresentationIntent.REPORT: ["title", "executive_summary", "findings", "analysis", "recommendations"],
        PresentationIntent.STRATEGY: ["title", "executive_summary", "situation", "vision", "strategy", "roadmap", "next_steps"],
    }
    recommended_slides = slide_type_map.get(intent, ["title", "content", "content", "content", "summary"])
    
    # Empfehlungen generieren
    recommendations = []
    for m in missing:
        if m.importance in ["Critical", "High"]:
            recommendations.append(m.suggestion)
    
    if word_count < 30:
        recommendations.append("Das Briefing ist sehr kurz. Fügen Sie mehr Details hinzu für bessere Ergebnisse.")
    
    # LLM-Erweiterung
    if HAS_LLM and llm_enabled and llm_enabled():
        topics = _extract_topics_with_llm(brief)
    else:
        topics = keywords[:5]
    
    return BriefingAnalysis(
        quality_score=round(quality_score, 1),
        quality_level=quality_level,
        intent=intent,
        entities=entities,
        topics=topics,
        keywords=keywords,
        has_customer_info=checks["has_customer_info"],
        has_industry_info=checks.get("has_industry", False),
        has_timeline=checks["has_timeline"],
        has_budget=checks["has_budget"],
        has_goals=checks["has_goals"],
        has_audience=checks["has_audience"],
        has_competitors=checks["has_competitors"],
        missing=missing,
        recommendations=recommendations,
        recommended_deck_size=recommended_deck_size,
        recommended_slide_types=recommended_slides
    )


def _extract_topics_with_llm(brief: str) -> List[str]:
    """Extrahiert Hauptthemen mit LLM."""
    prompt = f"""Extrahiere die 3-5 Hauptthemen aus diesem Briefing:

{brief[:500]}

Antworte NUR mit JSON:
{{"topics": ["Thema1", "Thema2", "Thema3"]}}"""

    try:
        result = llm_generate(prompt, max_tokens=100)
        if result.get("ok"):
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("topics", [])[:5]
    except Exception:
        pass
    
    return []


# ============================================
# API FUNCTIONS
# ============================================

def analyze(
    brief: str,
    topic: str = "",
    industry: str = "",
    customer_name: str = ""
) -> Dict[str, Any]:
    """
    Hauptfunktion: Analysiert ein Briefing.
    
    Returns:
        Dictionary mit vollständiger Analyse
    """
    analysis = analyze_briefing(brief, topic, industry, customer_name)
    
    return {
        "ok": True,
        "quality": {
            "score": analysis.quality_score,
            "level": analysis.quality_level.value,
            "word_count": len(brief.split())
        },
        "intent": {
            "type": analysis.intent.value,
            "description": {
                "inform": "Informationsvermittlung",
                "persuade": "Überzeugung",
                "sell": "Verkauf",
                "educate": "Schulung",
                "report": "Berichterstattung",
                "pitch": "Pitch/Präsentation",
                "strategy": "Strategievorstellung"
            }.get(analysis.intent.value, "Allgemein")
        },
        "extracted": {
            "entities": [asdict(e) for e in analysis.entities],
            "topics": analysis.topics,
            "keywords": analysis.keywords
        },
        "completeness": {
            "customer_info": analysis.has_customer_info,
            "industry_info": analysis.has_industry_info,
            "timeline": analysis.has_timeline,
            "budget": analysis.has_budget,
            "goals": analysis.has_goals,
            "audience": analysis.has_audience,
            "competitors": analysis.has_competitors
        },
        "missing": [asdict(m) for m in analysis.missing],
        "recommendations": analysis.recommendations,
        "suggested": {
            "deck_size": analysis.recommended_deck_size,
            "slide_types": analysis.recommended_slide_types
        }
    }


def check_status() -> Dict[str, Any]:
    """Gibt den Status des Briefing Analyzers zurück."""
    return {
        "ok": True,
        "required_fields": list(REQUIRED_FIELDS.keys()),
        "intents_supported": [i.value for i in PresentationIntent],
        "llm_available": HAS_LLM and (llm_enabled() if llm_enabled else False)
    }
