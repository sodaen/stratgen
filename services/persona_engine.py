# -*- coding: utf-8 -*-
"""
services/persona_engine.py
==========================
Killer-Feature: Persona & Archetypen Engine

Features:
1. Automatische Zielgruppenanalyse aus Briefing
2. Persona-Generierung mit demografischen Details
3. Archetypen-Zuordnung (12 Jung'sche Archetypen)
4. Buyer Journey Mapping
5. Pain Points & Motivations Extraction
6. Kommunikationsstil-Empfehlungen

Author: StratGen Agent V3.5
"""
from __future__ import annotations
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================
# ARCHETYPEN DEFINITION (12 Jung'sche)
# ============================================

class Archetype(str, Enum):
    """Die 12 universellen Archetypen nach Carl Jung."""
    
    # Sehnsucht nach Paradies
    INNOCENT = "innocent"          # Der Unschuldige - Optimistisch, will Glück
    EXPLORER = "explorer"          # Der Entdecker - Freiheit, Authentizität
    SAGE = "sage"                  # Der Weise - Wahrheit, Verstehen
    
    # Hinterlassen einer Spur
    HERO = "hero"                  # Der Held - Mut, Meisterschaft
    OUTLAW = "outlaw"              # Der Rebell - Befreiung, Revolution
    MAGICIAN = "magician"          # Der Magier - Transformation, Vision
    
    # Verbindung zu anderen
    EVERYMAN = "everyman"          # Der Jedermann - Zugehörigkeit, Realismus
    LOVER = "lover"                # Der Liebende - Intimität, Leidenschaft
    JESTER = "jester"              # Der Narr - Freude, Leichtigkeit
    
    # Struktur geben
    CAREGIVER = "caregiver"        # Der Fürsorgliche - Helfen, Großzügigkeit
    RULER = "ruler"                # Der Herrscher - Kontrolle, Erfolg
    CREATOR = "creator"            # Der Schöpfer - Innovation, Ausdruck


# Archetypen-Details
ARCHETYPE_DETAILS = {
    Archetype.INNOCENT: {
        "name_de": "Der Unschuldige",
        "motto": "Frei zu sein, um du selbst zu sein",
        "core_desire": "Das Paradies erlangen",
        "goal": "Glücklich sein",
        "fear": "Bestraft werden für etwas Falsches",
        "strategy": "Das Richtige tun",
        "weakness": "Langweilig durch Naivität",
        "talent": "Glaube und Optimismus",
        "brands": ["Coca-Cola", "Dove", "McDonald's"],
        "tone": "Optimistisch, ehrlich, einfach",
        "colors": ["Weiß", "Pastellfarben", "Hellblau"]
    },
    Archetype.EXPLORER: {
        "name_de": "Der Entdecker",
        "motto": "Grenze mich nicht ein",
        "core_desire": "Freiheit, eigenen Weg finden",
        "goal": "Authentisches, erfülltes Leben",
        "fear": "Gefangen sein, Konformität",
        "strategy": "Reisen, neue Erfahrungen suchen",
        "weakness": "Ziellos umherwandern",
        "talent": "Autonomie, Ehrgeiz, Treue zu sich selbst",
        "brands": ["Jeep", "Patagonia", "North Face"],
        "tone": "Abenteuerlustig, unabhängig, mutig",
        "colors": ["Erdtöne", "Grün", "Orange"]
    },
    Archetype.SAGE: {
        "name_de": "Der Weise",
        "motto": "Die Wahrheit wird dich befreien",
        "core_desire": "Wahrheit finden",
        "goal": "Intelligenz nutzen, um die Welt zu verstehen",
        "fear": "Getäuscht werden, Ignoranz",
        "strategy": "Informationen und Wissen suchen",
        "weakness": "Kann ewig studieren ohne zu handeln",
        "talent": "Weisheit, Intelligenz",
        "brands": ["Google", "BBC", "MIT"],
        "tone": "Intelligent, analytisch, vertrauenswürdig",
        "colors": ["Blau", "Grau", "Weiß"]
    },
    Archetype.HERO: {
        "name_de": "Der Held",
        "motto": "Wo ein Wille ist, ist auch ein Weg",
        "core_desire": "Durch mutige Taten beweisen",
        "goal": "Meisterschaft, die Welt verbessern",
        "fear": "Schwäche, Aufgeben",
        "strategy": "So stark wie möglich werden",
        "weakness": "Arroganz, immer ein Feind brauchen",
        "talent": "Kompetenz und Mut",
        "brands": ["Nike", "FedEx", "BMW"],
        "tone": "Mutig, entschlossen, inspirierend",
        "colors": ["Rot", "Schwarz", "Gold"]
    },
    Archetype.OUTLAW: {
        "name_de": "Der Rebell",
        "motto": "Regeln sind da, um gebrochen zu werden",
        "core_desire": "Rache oder Revolution",
        "goal": "Das Nicht-Funktionierende zerstören",
        "fear": "Machtlos oder unwirksam sein",
        "strategy": "Stören, zerstören, schockieren",
        "weakness": "Zur dunklen Seite wechseln",
        "talent": "Ungeheuerliche Freiheit",
        "brands": ["Harley-Davidson", "Diesel", "Virgin"],
        "tone": "Rebellisch, provokant, wild",
        "colors": ["Schwarz", "Rot", "Dunkle Töne"]
    },
    Archetype.MAGICIAN: {
        "name_de": "Der Magier",
        "motto": "Ich mache Dinge möglich",
        "core_desire": "Grundlegende Gesetze verstehen",
        "goal": "Träume wahr werden lassen",
        "fear": "Unbeabsichtigte negative Folgen",
        "strategy": "Vision entwickeln und leben",
        "weakness": "Manipulativ werden",
        "talent": "Transformation finden",
        "brands": ["Apple", "Disney", "Tesla"],
        "tone": "Visionär, inspirierend, transformativ",
        "colors": ["Lila", "Blau", "Silber"]
    },
    Archetype.EVERYMAN: {
        "name_de": "Der Jedermann",
        "motto": "Alle Menschen sind gleich geschaffen",
        "core_desire": "Verbindung mit anderen",
        "goal": "Dazugehören",
        "fear": "Ausgestoßen werden",
        "strategy": "Bodenständige Tugenden entwickeln",
        "weakness": "Oberflächlichkeit",
        "talent": "Realismus, Empathie",
        "brands": ["IKEA", "Volkswagen", "Budweiser"],
        "tone": "Ehrlich, bodenständig, freundlich",
        "colors": ["Braun", "Beige", "Grün"]
    },
    Archetype.LOVER: {
        "name_de": "Der Liebende",
        "motto": "Du bist der Einzige",
        "core_desire": "Intimität und Erfahrung",
        "goal": "In Beziehung sein mit Menschen und Umgebung",
        "fear": "Allein sein, ungeliebt",
        "strategy": "Attraktiver werden",
        "weakness": "Alles tun, um Aufmerksamkeit zu bekommen",
        "talent": "Leidenschaft, Dankbarkeit, Wertschätzung",
        "brands": ["Chanel", "Victoria's Secret", "Häagen-Dazs"],
        "tone": "Leidenschaftlich, sinnlich, intim",
        "colors": ["Rot", "Pink", "Gold"]
    },
    Archetype.JESTER: {
        "name_de": "Der Narr",
        "motto": "Man lebt nur einmal",
        "core_desire": "Im Moment leben mit Freude",
        "goal": "Spaß haben, die Welt erhellen",
        "fear": "Langweilig sein",
        "strategy": "Spielen, Witze machen, lustig sein",
        "weakness": "Leichtfertigkeit, Zeitverschwendung",
        "talent": "Freude",
        "brands": ["M&M's", "Old Spice", "Ben & Jerry's"],
        "tone": "Humorvoll, verspielt, unbeschwert",
        "colors": ["Gelb", "Orange", "Bunte Farben"]
    },
    Archetype.CAREGIVER: {
        "name_de": "Der Fürsorgliche",
        "motto": "Liebe deinen Nächsten wie dich selbst",
        "core_desire": "Andere beschützen und pflegen",
        "goal": "Anderen helfen",
        "fear": "Egoismus und Undankbarkeit",
        "strategy": "Dinge für andere tun",
        "weakness": "Ausgenutzt werden",
        "talent": "Mitgefühl, Großzügigkeit",
        "brands": ["Johnson & Johnson", "Volvo", "UNICEF"],
        "tone": "Fürsorglich, warmherzig, unterstützend",
        "colors": ["Blau", "Rosa", "Weiß"]
    },
    Archetype.RULER: {
        "name_de": "Der Herrscher",
        "motto": "Macht ist nicht alles, sie ist das Einzige",
        "core_desire": "Kontrolle",
        "goal": "Erfolgreiche Gemeinschaft/Familie schaffen",
        "fear": "Chaos, gestürzt werden",
        "strategy": "Führung ausüben",
        "weakness": "Autoritär werden",
        "talent": "Verantwortung, Führung",
        "brands": ["Mercedes-Benz", "Rolex", "American Express"],
        "tone": "Autoritär, kontrolliert, luxuriös",
        "colors": ["Gold", "Dunkelblau", "Schwarz"]
    },
    Archetype.CREATOR: {
        "name_de": "Der Schöpfer",
        "motto": "Wenn du es dir vorstellen kannst, kann es gemacht werden",
        "core_desire": "Etwas von bleibendem Wert schaffen",
        "goal": "Vision verwirklichen",
        "fear": "Mittelmäßige Vision oder Ausführung",
        "strategy": "Fähigkeiten entwickeln",
        "weakness": "Perfektionismus",
        "talent": "Kreativität und Vorstellungskraft",
        "brands": ["Lego", "Adobe", "Apple"],
        "tone": "Kreativ, innovativ, inspirierend",
        "colors": ["Orange", "Gelb", "Bunt"]
    }
}


# ============================================
# PERSONA DATA CLASS
# ============================================

@dataclass
class Persona:
    """Eine generierte Persona."""
    name: str
    age: int
    gender: str
    job_title: str
    company_size: str
    industry: str
    
    # Archetyp
    primary_archetype: Archetype
    secondary_archetype: Optional[Archetype] = None
    
    # Demografisch
    income_level: str = "Mittel"
    education: str = "Bachelor"
    location: str = "Deutschland"
    
    # Psychografisch
    goals: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    motivations: List[str] = field(default_factory=list)
    
    # Verhalten
    decision_factors: List[str] = field(default_factory=list)
    information_sources: List[str] = field(default_factory=list)
    preferred_channels: List[str] = field(default_factory=list)
    
    # Kommunikation
    communication_style: str = "Professional"
    key_messages: List[str] = field(default_factory=list)
    
    # Buyer Journey
    journey_stage: str = "Awareness"  # Awareness, Consideration, Decision
    
    # Quote
    quote: str = ""
    
    # Bild-Beschreibung für AI-Generierung
    image_prompt: str = ""


# ============================================
# INDUSTRY PROFILES
# ============================================

INDUSTRY_PROFILES = {
    "fertigung": {
        "typical_titles": ["Produktionsleiter", "Werksleiter", "Betriebsleiter", "Qualitätsmanager", "Supply Chain Manager"],
        "challenges": ["Effizienzsteigerung", "Kostensenkung", "Qualitätssicherung", "Digitalisierung", "Fachkräftemangel"],
        "decision_factors": ["ROI", "Implementierungszeit", "Kompatibilität", "Support"],
        "typical_archetypes": [Archetype.RULER, Archetype.HERO, Archetype.SAGE]
    },
    "technologie": {
        "typical_titles": ["CTO", "IT-Leiter", "DevOps Engineer", "Product Manager", "Tech Lead"],
        "challenges": ["Skalierbarkeit", "Security", "Innovation", "Time-to-Market", "Talentakquise"],
        "decision_factors": ["Technische Exzellenz", "Integration", "Skalierbarkeit", "Community"],
        "typical_archetypes": [Archetype.CREATOR, Archetype.MAGICIAN, Archetype.EXPLORER]
    },
    "finanzen": {
        "typical_titles": ["CFO", "Finanzvorstand", "Controller", "Risk Manager", "Compliance Officer"],
        "challenges": ["Regulierung", "Risikomanagement", "Digitalisierung", "Kostenkontrolle"],
        "decision_factors": ["Compliance", "Sicherheit", "ROI", "Reputation"],
        "typical_archetypes": [Archetype.RULER, Archetype.SAGE, Archetype.CAREGIVER]
    },
    "healthcare": {
        "typical_titles": ["Klinikleiter", "Chefarzt", "Pflegedienstleitung", "Medical Director"],
        "challenges": ["Patientenversorgung", "Kostendruck", "Digitalisierung", "Fachkräftemangel"],
        "decision_factors": ["Patientensicherheit", "Evidenzbasierung", "Effizienz"],
        "typical_archetypes": [Archetype.CAREGIVER, Archetype.SAGE, Archetype.HERO]
    },
    "retail": {
        "typical_titles": ["Geschäftsführer", "Marketing Director", "E-Commerce Manager", "Category Manager"],
        "challenges": ["Kundengewinnung", "Omnichannel", "Personalisierung", "Margendruck"],
        "decision_factors": ["Kundenerlebnis", "ROI", "Skalierbarkeit"],
        "typical_archetypes": [Archetype.EVERYMAN, Archetype.LOVER, Archetype.JESTER]
    },
    "beratung": {
        "typical_titles": ["Partner", "Senior Consultant", "Managing Director", "Principal"],
        "challenges": ["Differenzierung", "Talentbindung", "Digitale Services", "Skalierung"],
        "decision_factors": ["Expertise", "Track Record", "Methodik"],
        "typical_archetypes": [Archetype.SAGE, Archetype.HERO, Archetype.MAGICIAN]
    },
    "marketing": {
        "typical_titles": ["CMO", "Marketing Director", "Brand Manager", "Performance Manager"],
        "challenges": ["ROI-Nachweis", "Datenschutz", "Kanalvielfalt", "Content-Produktion"],
        "decision_factors": ["Messbarkeit", "Kreativität", "Integration"],
        "typical_archetypes": [Archetype.CREATOR, Archetype.MAGICIAN, Archetype.LOVER]
    },
    "default": {
        "typical_titles": ["Geschäftsführer", "Abteilungsleiter", "Projektleiter", "Manager"],
        "challenges": ["Effizienz", "Wachstum", "Innovation", "Mitarbeiter"],
        "decision_factors": ["Kosten", "Nutzen", "Risiko", "Zeit"],
        "typical_archetypes": [Archetype.HERO, Archetype.RULER, Archetype.SAGE]
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
# ARCHETYPE DETECTION
# ============================================

def detect_archetype_from_brief(
    brief: str,
    industry: str = "",
    audience: str = ""
) -> Tuple[Archetype, float, str]:
    """
    Erkennt den passenden Archetyp aus Briefing.
    
    Returns:
        Tuple von (Archetype, Confidence, Rationale)
    """
    text = f"{brief} {industry} {audience}".lower()
    
    # Keyword-Mapping
    archetype_keywords = {
        Archetype.HERO: ["erfolg", "leistung", "gewinnen", "meister", "champion", "führend", "stark"],
        Archetype.SAGE: ["wissen", "expertise", "verstehen", "analyse", "forschung", "intelligent", "lernen"],
        Archetype.EXPLORER: ["innovation", "neu", "entdecken", "pioneer", "trend", "zukunft", "anders"],
        Archetype.CREATOR: ["kreativ", "design", "entwickeln", "bauen", "schaffen", "idee", "gestalten"],
        Archetype.RULER: ["kontrolle", "premium", "luxus", "führung", "management", "qualität", "standard"],
        Archetype.CAREGIVER: ["helfen", "unterstützen", "service", "kunde", "partner", "sicherheit", "vertrauen"],
        Archetype.MAGICIAN: ["transform", "wandel", "change", "digital", "vision", "zukunft", "möglich"],
        Archetype.EVERYMAN: ["einfach", "praktisch", "alltag", "normal", "fair", "ehrlich", "preis"],
        Archetype.LOVER: ["beziehung", "emotion", "erlebnis", "gefühl", "leidenschaft", "schön", "genuss"],
        Archetype.JESTER: ["spaß", "freude", "locker", "humor", "unterhaltsam", "leicht", "spielerisch"],
        Archetype.OUTLAW: ["anders", "disruptiv", "revolution", "brechen", "mutig", "provokant", "regel"],
        Archetype.INNOCENT: ["einfach", "rein", "natürlich", "tradition", "wert", "familie", "vertrauen"],
    }
    
    scores = {}
    for archetype, keywords in archetype_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[archetype] = score
    
    # Branchenbonus
    industry_lower = industry.lower()
    for ind, profile in INDUSTRY_PROFILES.items():
        if ind in industry_lower:
            for arch in profile.get("typical_archetypes", []):
                scores[arch] = scores.get(arch, 0) + 2
            break
    
    # Bester Archetyp
    if scores:
        best = max(scores, key=scores.get)
        confidence = min(0.9, 0.4 + scores[best] * 0.1)
        rationale = f"Basierend auf Keywords und Branche '{industry}'"
        return best, confidence, rationale
    
    # Default
    return Archetype.HERO, 0.5, "Default Archetyp"


def detect_archetype_llm(
    brief: str,
    industry: str = "",
    audience: str = ""
) -> Tuple[Archetype, float, str]:
    """Erkennt Archetyp via LLM."""
    if not HAS_LLM or not llm_enabled or not llm_enabled():
        return detect_archetype_from_brief(brief, industry, audience)
    
    archetypes_list = "\n".join([f"- {a.value}: {ARCHETYPE_DETAILS[a]['name_de']}" for a in Archetype])
    
    prompt = f"""Analysiere dieses Briefing und bestimme den passenden Marken-Archetyp:

Briefing: {brief[:500]}
Branche: {industry}
Zielgruppe: {audience}

Verfügbare Archetypen:
{archetypes_list}

Antworte NUR mit JSON:
{{"archetype": "hero", "confidence": 0.8, "rationale": "..."}}"""

    try:
        result = llm_generate(prompt, max_tokens=150)
        if result.get("ok"):
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                archetype_str = data.get("archetype", "hero").lower()
                
                try:
                    archetype = Archetype(archetype_str)
                except ValueError:
                    archetype = Archetype.HERO
                
                return archetype, float(data.get("confidence", 0.7)), data.get("rationale", "LLM analysis")
    except Exception:
        pass
    
    return detect_archetype_from_brief(brief, industry, audience)


# ============================================
# PERSONA GENERATION
# ============================================

def generate_persona(
    brief: str,
    industry: str = "",
    audience: str = "",
    company_size: str = "Mittelstand",
    use_llm: bool = True
) -> Persona:
    """
    Generiert eine Persona aus dem Briefing.
    
    Args:
        brief: Das Projekt-Briefing
        industry: Branche
        audience: Zielgruppenbeschreibung
        company_size: Unternehmensgröße
        use_llm: LLM für erweiterte Generierung nutzen?
    
    Returns:
        Persona-Objekt
    """
    # Archetyp bestimmen
    if use_llm:
        primary_archetype, conf, rationale = detect_archetype_llm(brief, industry, audience)
    else:
        primary_archetype, conf, rationale = detect_archetype_from_brief(brief, industry, audience)
    
    # Industry Profile
    industry_lower = industry.lower() if industry else "default"
    profile = None
    for ind, prof in INDUSTRY_PROFILES.items():
        if ind in industry_lower:
            profile = prof
            break
    if not profile:
        profile = INDUSTRY_PROFILES["default"]
    
    # Archetyp-Details
    arch_details = ARCHETYPE_DETAILS.get(primary_archetype, {})
    
    # Basis-Persona erstellen
    import random
    
    names_male = ["Thomas", "Michael", "Stefan", "Andreas", "Markus", "Frank", "Peter"]
    names_female = ["Sandra", "Julia", "Anna", "Katharina", "Maria", "Sabine", "Laura"]
    
    gender = random.choice(["männlich", "weiblich"])
    name = random.choice(names_male if gender == "männlich" else names_female)
    
    persona = Persona(
        name=f"{name} Müller",
        age=random.randint(35, 55),
        gender=gender,
        job_title=random.choice(profile.get("typical_titles", ["Manager"])),
        company_size=company_size,
        industry=industry or "Allgemein",
        primary_archetype=primary_archetype,
        goals=[
            f"Unternehmensziele erreichen",
            f"Effizienz steigern",
            arch_details.get("goal", "Erfolg haben")
        ],
        challenges=profile.get("challenges", ["Effizienz", "Wachstum"])[:4],
        pain_points=[
            f"Zeitdruck und komplexe Entscheidungen",
            f"Unsicherheit bei {industry}-spezifischen Themen",
            arch_details.get("fear", "Misserfolg")
        ],
        motivations=[
            arch_details.get("core_desire", "Erfolg"),
            "Anerkennung im Unternehmen",
            "Messbare Ergebnisse"
        ],
        decision_factors=profile.get("decision_factors", ["Kosten", "Nutzen"])[:4],
        information_sources=["Fachmedien", "LinkedIn", "Empfehlungen", "Webinare"],
        preferred_channels=["E-Mail", "LinkedIn", "Persönliche Meetings"],
        communication_style=arch_details.get("tone", "Professional"),
        key_messages=[
            f"Wir verstehen Ihre Herausforderungen",
            f"Nachweisbare Ergebnisse in {industry}",
            arch_details.get("motto", "Gemeinsam zum Erfolg")
        ],
        journey_stage="Consideration",
        quote=f"\"{arch_details.get('motto', 'Qualität und Effizienz sind mein Maßstab.')}\"",
        image_prompt=f"Professional {gender} executive, {persona.age}s, business attire, confident, {industry} background"
    )
    
    # LLM-Erweiterung
    if use_llm and HAS_LLM and llm_enabled and llm_enabled():
        persona = _enhance_persona_with_llm(persona, brief, audience)
    
    return persona


def _enhance_persona_with_llm(persona: Persona, brief: str, audience: str) -> Persona:
    """Erweitert Persona mit LLM-generierten Details."""
    prompt = f"""Erweitere diese Persona mit spezifischen Details:

Name: {persona.name}
Job: {persona.job_title}
Branche: {persona.industry}
Briefing: {brief[:300]}
Zielgruppe: {audience}

Generiere:
1. Ein authentisches Zitat (1 Satz)
2. Einen spezifischen Pain Point
3. Eine konkrete Motivation

Antworte NUR mit JSON:
{{"quote": "...", "pain_point": "...", "motivation": "..."}}"""

    try:
        result = llm_generate(prompt, max_tokens=150)
        if result.get("ok"):
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if data.get("quote"):
                    persona.quote = f"\"{data['quote']}\""
                if data.get("pain_point"):
                    persona.pain_points.insert(0, data["pain_point"])
                if data.get("motivation"):
                    persona.motivations.insert(0, data["motivation"])
    except Exception:
        pass
    
    return persona


# ============================================
# MULTIPLE PERSONAS
# ============================================

def generate_personas(
    brief: str,
    industry: str = "",
    audience: str = "",
    count: int = 2,
    use_llm: bool = True
) -> List[Persona]:
    """
    Generiert mehrere Personas für verschiedene Stakeholder.
    
    Args:
        brief: Das Projekt-Briefing
        industry: Branche
        audience: Zielgruppenbeschreibung
        count: Anzahl der Personas (max 4)
        use_llm: LLM nutzen?
    
    Returns:
        Liste von Personas
    """
    count = min(4, max(1, count))
    personas = []
    
    # Verschiedene Stakeholder-Typen
    stakeholder_types = [
        {"role": "Decision Maker", "company_size": "Großunternehmen"},
        {"role": "Influencer", "company_size": "Mittelstand"},
        {"role": "User", "company_size": "KMU"},
        {"role": "Champion", "company_size": "Startup"}
    ]
    
    used_archetypes = set()
    
    for i in range(count):
        stakeholder = stakeholder_types[i % len(stakeholder_types)]
        
        persona = generate_persona(
            brief=brief,
            industry=industry,
            audience=f"{audience} - {stakeholder['role']}",
            company_size=stakeholder["company_size"],
            use_llm=use_llm
        )
        
        # Vermeiden gleicher Archetypen
        while persona.primary_archetype in used_archetypes and len(used_archetypes) < len(Archetype):
            # Anderen Archetyp wählen
            for arch in Archetype:
                if arch not in used_archetypes:
                    persona.primary_archetype = arch
                    break
        
        used_archetypes.add(persona.primary_archetype)
        personas.append(persona)
    
    return personas


# ============================================
# PERSONA TO SLIDE CONTENT
# ============================================

def persona_to_slide_content(persona: Persona) -> Dict[str, Any]:
    """Konvertiert eine Persona zu Slide-Content."""
    arch_details = ARCHETYPE_DETAILS.get(persona.primary_archetype, {})
    
    return {
        "type": "persona",
        "title": f"Zielgruppe: {persona.name}",
        "subtitle": f"{persona.job_title} | {persona.industry}",
        "bullets": [
            f"Alter: {persona.age} | {persona.gender.capitalize()}",
            f"Unternehmensgröße: {persona.company_size}",
            f"Archetyp: {arch_details.get('name_de', persona.primary_archetype.value)}",
            f"Hauptziel: {persona.goals[0] if persona.goals else 'Erfolg'}",
            f"Größte Herausforderung: {persona.challenges[0] if persona.challenges else 'Effizienz'}",
        ],
        "notes": f"Persona-Profil für {persona.name}. Kommunikationsstil: {persona.communication_style}. {persona.quote}",
        "layout_hint": "Title and Content",
        "persona_data": asdict(persona)
    }


# ============================================
# API FUNCTIONS
# ============================================

def analyze_audience(
    brief: str,
    industry: str = "",
    audience: str = ""
) -> Dict[str, Any]:
    """
    Analysiert die Zielgruppe aus dem Briefing.
    
    Returns:
        Dictionary mit Archetyp, Persona-Empfehlung, Kommunikationstipps
    """
    archetype, confidence, rationale = detect_archetype_llm(brief, industry, audience)
    arch_details = ARCHETYPE_DETAILS.get(archetype, {})
    
    return {
        "ok": True,
        "primary_archetype": {
            "id": archetype.value,
            "name": arch_details.get("name_de"),
            "confidence": confidence,
            "rationale": rationale
        },
        "communication_recommendations": {
            "tone": arch_details.get("tone"),
            "colors": arch_details.get("colors"),
            "key_message_style": arch_details.get("motto"),
            "brands_for_reference": arch_details.get("brands")
        },
        "audience_insights": {
            "core_desire": arch_details.get("core_desire"),
            "main_fear": arch_details.get("fear"),
            "decision_strategy": arch_details.get("strategy")
        }
    }


def get_archetype_details(archetype_id: str) -> Dict[str, Any]:
    """Gibt Details zu einem Archetyp zurück."""
    try:
        archetype = Archetype(archetype_id.lower())
        return {"ok": True, "archetype": archetype.value, **ARCHETYPE_DETAILS.get(archetype, {})}
    except ValueError:
        return {"ok": False, "error": f"Unknown archetype: {archetype_id}"}


def list_archetypes() -> Dict[str, Any]:
    """Listet alle verfügbaren Archetypen."""
    return {
        "ok": True,
        "archetypes": [
            {
                "id": arch.value,
                "name": ARCHETYPE_DETAILS[arch]["name_de"],
                "motto": ARCHETYPE_DETAILS[arch]["motto"]
            }
            for arch in Archetype
        ]
    }


def check_status() -> Dict[str, Any]:
    """Gibt den Status der Persona Engine zurück."""
    return {
        "ok": True,
        "archetypes_available": len(Archetype),
        "industries_profiled": len(INDUSTRY_PROFILES),
        "llm_available": HAS_LLM and (llm_enabled() if llm_enabled else False)
    }
