"""
Intelligenter Präsentations-Generator v2 für Stratgen.
Verbessert: Spezifische Titel, mehr Variation, bessere Prompts.
"""

import os
import sys
import json
import time
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, '/home/sodaen/stratgen')

# Research Enrichment für externe Daten
try:
    from services.research_enrichment import enrich_topic, generate_research_prompt_context, get_slide_enrichment
    from services.unified_knowledge import search_for_slide as knowledge_search
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    def knowledge_search(*args, **kwargs): return {"knowledge": [], "templates": []}

try:
    pass  # placeholder für original imports
    HAS_RESEARCH = True
except ImportError:
    HAS_RESEARCH = False
    def enrich_topic(*args, **kwargs): return {}
    def generate_research_prompt_context(*args, **kwargs): return ""
    def get_slide_enrichment(*args, **kwargs): return {}


@dataclass
class PresentationBrief:
    """Briefing für eine Präsentation."""
    topic: str
    objective: str = ""
    customer: str = ""
    industry: str = ""
    target_audience: str = ""
    key_messages: List[str] = None
    slide_count: int = 30
    style: str = "corporate"
    language: str = "de"


# Spezifische Titel-Vorlagen pro Kapitel und Slide-Typ
TITLE_TEMPLATES = {
    "market": {
        "text": ["Marktüberblick {industry}", "Der {industry}-Markt im Wandel", "Marktdynamik und Trends", "Aktuelle Marktsituation"],
        "chart": ["Marktgröße und Wachstum", "TAM / SAM / SOM Analyse", "Marktentwicklung 2020-2025", "Marktsegmentierung"],
        "bullets": ["Zentrale Markttrends", "Wachstumstreiber im Markt", "Marktchancen für {customer}", "Key Market Insights"],
    },
    "competition": {
        "comparison": ["Wettbewerbsvergleich", "{customer} vs. Wettbewerb", "Feature-Matrix", "Anbietervergleich"],
        "bullets": ["Unsere Differenzierung", "Wettbewerbsvorteile", "Warum {customer}?", "Unique Selling Points"],
        "text": ["Wettbewerbslandschaft", "Analyse der Mitbewerber", "Positionierung im Markt"],
    },
    "customers": {
        "persona": ["Zielkunde: {persona_type}", "Buyer Persona: {persona_type}", "Idealer Kunde: {persona_type}"],
        "bullets": ["Customer Journey", "Kaufentscheidungsprozess", "Touchpoints und Kanäle", "Kundenbedürfnisse"],
        "text": ["Zielgruppensegmentierung", "Kundenanalyse", "Wer sind unsere Kunden?"],
    },
    "value_prop": {
        "text": ["Das Problem", "Die Herausforderung", "Warum jetzt handeln?", "Pain Points der Zielgruppe",
                 "Unsere Lösung", "Der {customer}-Ansatz", "So lösen wir das Problem", "Die Innovation"],
        "quote": ["Kundenstimme", "Was unsere Kunden sagen", "Erfolgsgeschichte", "Testimonial"],
        "comparison": ["Vorher vs. Nachher", "Der Unterschied", "Mit und ohne {customer}"],
    },
    "strategy": {
        "text": ["Strategischer Ansatz", "Go-to-Market Strategie", "Unser Marktansatz", "Die Wachstumsstrategie"],
        "bullets": ["Vertriebskanäle", "Marketing-Mix", "Kommunikationsstrategie", "Channel-Strategie"],
        "chart": ["Pricing-Strategie", "Preismodell", "Revenue Model", "Umsatzplanung"],
    },
    "execution": {
        "timeline": ["Roadmap 2025", "Meilensteine", "Umsetzungsplan", "Go-Live Timeline"],
        "bullets": ["Aktionsplan Q1", "Nächste 90 Tage", "Prioritäten Phase 1", "Quick Wins"],
        "chart": ["Budget-Allokation", "Investitionsplan", "Ressourcenverteilung", "Kostenstruktur"],
        "text": ["Risiken und Mitigation", "Herausforderungen meistern", "Risk Management"],
    },
    "metrics": {
        "chart": ["Ziele Jahr 1", "KPI Dashboard", "Erfolgskennzahlen", "Target Metrics"],
        "bullets": ["Key Performance Indicators", "Messbare Ziele", "Success Metrics", "OKRs"],
        "text": ["ROI-Berechnung", "Business Case", "Return on Investment", "Wirtschaftlichkeit"],
    },
    "closing": {
        "conclusion": ["Key Takeaways", "Zusammenfassung", "Das Wichtigste in Kürze", "Fazit"],
        "bullets": ["Nächste Schritte", "Call to Action", "So geht es weiter", "Handlungsempfehlungen"],
    }
}

# Persona-Typen für Variation
PERSONA_TYPES = [
    ("Entscheider", "C-Level / Geschäftsführung"),
    ("IT-Leiter", "Technische Leitung"),
    ("Projektleiter", "Operative Ebene"),
    ("Einkäufer", "Beschaffung"),
    ("Anwender", "End-User"),
    ("Berater", "Externer Consultant"),
]


DECK_TEMPLATES = {
    "gtm_strategy": {
        "name": "Go-to-Market Strategie",
        "chapters": [
            {"name": "intro", "title": "Einführung", "slides": ["title", "executive_summary"]},
            {"name": "market", "title": "Marktanalyse", "slides": ["chapter", "text", "chart", "bullets"]},
            {"name": "competition", "title": "Wettbewerb", "slides": ["chapter", "comparison", "bullets"]},
            {"name": "customers", "title": "Zielgruppen", "slides": ["chapter", "persona", "persona", "bullets"]},
            {"name": "value_prop", "title": "Value Proposition", "slides": ["chapter", "text", "text", "quote"]},
            {"name": "strategy", "title": "Strategie", "slides": ["chapter", "text", "bullets", "chart"]},
            {"name": "execution", "title": "Umsetzung", "slides": ["chapter", "timeline", "bullets", "chart"]},
            {"name": "metrics", "title": "Erfolgsmessung", "slides": ["chapter", "chart", "bullets"]},
            {"name": "closing", "title": "Abschluss", "slides": ["conclusion", "bullets", "contact"]},
        ]
    },
    "pitch_deck": {
        "name": "Pitch Deck",
        "chapters": [
            {"name": "intro", "title": "", "slides": ["title"]},
            {"name": "market", "title": "Problem", "slides": ["chapter", "text"]},
            {"name": "value_prop", "title": "Lösung", "slides": ["chapter", "text", "bullets"]},
            {"name": "competition", "title": "Produkt", "slides": ["chapter", "bullets", "comparison"]},
            {"name": "market", "title": "Markt", "slides": ["chapter", "chart"]},
            {"name": "strategy", "title": "Business Model", "slides": ["chapter", "chart", "bullets"]},
            {"name": "metrics", "title": "Traction", "slides": ["chapter", "chart"]},
            {"name": "customers", "title": "Team", "slides": ["chapter", "persona", "persona"]},
            {"name": "closing", "title": "Investment", "slides": ["chapter", "bullets", "contact"]},
        ]
    },
    "sales_deck": {
        "name": "Sales Präsentation",
        "chapters": [
            {"name": "intro", "title": "", "slides": ["title", "executive_summary"]},
            {"name": "market", "title": "Herausforderung", "slides": ["chapter", "text", "bullets"]},
            {"name": "value_prop", "title": "Unsere Lösung", "slides": ["chapter", "text", "bullets", "comparison"]},
            {"name": "competition", "title": "Vorteile", "slides": ["chapter", "bullets", "quote"]},
            {"name": "customers", "title": "Referenzen", "slides": ["chapter", "text", "quote"]},
            {"name": "strategy", "title": "Angebot", "slides": ["chapter", "chart", "bullets"]},
            {"name": "closing", "title": "Nächste Schritte", "slides": ["conclusion", "contact"]},
        ]
    }
}


class IntelligentDeckGenerator:
    """Generiert intelligente Präsentationen aus Briefings."""
    
    def __init__(self, template: str = "gtm_strategy"):
        self.template = DECK_TEMPLATES.get(template, DECK_TEMPLATES["gtm_strategy"])
        self.llm_calls = 0
        self.collected_sources = []  # Sammelt Quellen aus allen Slides
        self.persona_index = 0
        self.slide_titles_used = set()
    
    def _call_llm(self, prompt: str, max_tokens: int = 600) -> str:
        """Ruft das LLM auf."""
        try:
            from services.llm import generate
            self.llm_calls += 1
            result = generate(prompt, temperature=0.7, max_tokens=max_tokens)
            if isinstance(result, dict):
                if result.get('ok'):
                    return result.get('response', '')
                else:
                    print(f"  LLM Error: {result.get('error', 'Unknown')}")
                    return ""
            return str(result)
        except Exception as e:
            print(f"  LLM Error: {e}")
            return ""
    
    def _get_specific_title(self, chapter_name: str, slide_type: str, brief: PresentationBrief, context: Dict = None) -> str:
        """Generiert einen spezifischen Titel für den Slide."""
        templates = TITLE_TEMPLATES.get(chapter_name, {}).get(slide_type, [])
        
        if not templates:
            # Fallback-Titel basierend auf Slide-Typ
            fallbacks = {
                "text": ["Analyse", "Überblick", "Details", "Hintergrund"],
                "bullets": ["Kernpunkte", "Highlights", "Wichtige Aspekte"],
                "chart": ["Daten & Fakten", "Zahlen im Überblick", "Kennzahlen"],
                "comparison": ["Vergleich", "Gegenüberstellung"],
                "timeline": ["Zeitplan", "Meilensteine"],
                "quote": ["Stimmen", "Feedback"],
            }
            templates = fallbacks.get(slide_type, ["Inhalt"])
        
        # Wähle einen noch nicht verwendeten Titel
        available = [t for t in templates if t not in self.slide_titles_used]
        if not available:
            available = templates
        
        title = random.choice(available)
        self.slide_titles_used.add(title)
        
        # Ersetze Platzhalter
        title = title.replace("{customer}", brief.customer or "Unternehmen")
        title = title.replace("{industry}", brief.industry or "Markt")
        
        if context and "persona_type" in context:
            title = title.replace("{persona_type}", context["persona_type"])
        
        return title
    
    def _get_persona_type(self) -> tuple:
        """Gibt den nächsten Persona-Typ zurück."""
        persona = PERSONA_TYPES[self.persona_index % len(PERSONA_TYPES)]
        self.persona_index += 1
        return persona
    
    def _generate_slide_content(self, slide_type: str, chapter_name: str, chapter_title: str, 
                                 brief: PresentationBrief, slide_index: int) -> Dict[str, Any]:
        """Generiert den Inhalt für einen einzelnen Slide."""
        
        slide = {"type": slide_type}
        context = {}
        
        # Spezielle Slides ohne LLM
        if slide_type == "title":
            slide["title"] = brief.topic
            slide["subtitle"] = brief.objective[:100] if brief.objective else f"Präsentation für {brief.customer}"
            return slide
        
        if slide_type == "contact":
            slide["title"] = "Vielen Dank!"
            slide["subtitle"] = "Fragen und Diskussion"
            slide["bullets"] = [brief.customer, f"Branche: {brief.industry}"] if brief.customer else []
            return slide
        
        if slide_type == "chapter":
            slide["title"] = chapter_title
            slide["chapter_number"] = str(slide_index)
            slide["subtitle"] = self._get_chapter_subtitle(chapter_name, brief)
            return slide
        
        # Persona-Context
        if slide_type == "persona":
            persona_type, persona_desc = self._get_persona_type()
            context["persona_type"] = persona_type
            context["persona_desc"] = persona_desc
        
        # Spezifischer Titel
        title = self._get_specific_title(chapter_name, slide_type, brief, context)
        slide["title"] = title
        
        # Knowledge Base Suche für zusätzlichen Kontext
        try:
            if KNOWLEDGE_AVAILABLE:
                knowledge_result = knowledge_search(
                    slide_type=slide_type,
                    slide_title=title,
                    brief=f"{brief.topic} {brief.industry}",
                    context={"chapter": chapter_title}
                )
                knowledge_texts = [k.get("text", "")[:200] for k in knowledge_result.get("knowledge", [])[:3]]
                if knowledge_texts:
                    context["knowledge_context"] = "\n".join(knowledge_texts)
        except Exception as e:
            pass  # Knowledge ist optional
        
        # LLM für Content
        prompt = self._build_enhanced_prompt(slide_type, title, chapter_title, brief, context)
        response = self._call_llm(prompt, max_tokens=450)
        
        # Response parsen
        parsed = self._parse_response(response, slide_type, context)
        slide.update(parsed)
        
        # Titel beibehalten (nicht überschreiben)
        slide["title"] = title
        
        return slide
    
    def _get_chapter_subtitle(self, chapter_name: str, brief: PresentationBrief) -> str:
        """Generiert einen Untertitel für Kapitel."""
        subtitles = {
            "market": f"Chancen im {brief.industry or 'Markt'}",
            "competition": "Positionierung und Differenzierung",
            "customers": "Zielgruppen verstehen",
            "value_prop": "Unser Wertversprechen",
            "strategy": "Der Weg zum Erfolg",
            "execution": "Von der Strategie zur Umsetzung",
            "metrics": "Erfolg messbar machen",
            "closing": "Zusammenfassung und Ausblick",
        }
        return subtitles.get(chapter_name, "")
    
    def _build_enhanced_prompt(self, slide_type: str, title: str, chapter_title: str, 
                               brief: PresentationBrief, context: Dict) -> str:
        """Erstellt einen verbesserten, spezifischen Prompt."""
        
        type_instructions = {
            "executive_summary": """Erstelle 4-5 Executive Summary Punkte für diese Präsentation.
Jeder Punkt sollte:
- Ein konkretes Highlight oder Ergebnis nennen
- Zahlen/Fakten enthalten wo möglich
- 1-2 Sätze lang sein
Format: Beginne jeden Punkt mit "- " """,

            "text": f"""Erstelle strukturierten Content zum Thema "{title}" für {brief.customer or 'das Unternehmen'}.

FORMAT (WICHTIG - gut lesbar für Präsentation):

**Kernaussage:** [1 prägnanter Satz]

**Kontext:**
[2-3 Sätze mit Zahlen/Fakten zur Branche {brief.industry or 'B2B'}]

**Unsere Position:**
[2-3 Sätze wie {brief.customer or 'wir'} das Thema adressiert]

**Fazit:** [1 Satz mit konkretem Nutzen]

REGELN:
- Jeder Abschnitt max. 3 Sätze
- Konkrete Zahlen mit Quellenangabe
- Keine Textwüsten - gut strukturiert""",

            "bullets": f"""Erstelle 5-6 prägnante Bullet Points zum Thema "{title}".
Jeder Bullet sollte:
- Einen vollständigen Satz mit konkreter Aussage
- Bezug zu {brief.customer or 'dem Unternehmen'} haben
- Keine generischen Floskeln
Format: Beginne jeden Punkt mit "- " """,

            "persona": f"""Erstelle eine detaillierte Buyer Persona für {context.get('persona_type', 'Entscheider')} ({context.get('persona_desc', '')}).

Zielgruppe: {brief.target_audience or 'Geschäftskunden'}
Branche: {brief.industry or 'B2B'}

Format (genau einhalten):
Name: [Realistischer deutscher Vor- und Nachname]
Rolle: [Position und Unternehmensgröße]
Alter: [Alter und Karrierestufe]
Verantwortung: [Was verantwortet diese Person]
Budget: [Typisches Budget]
Entscheidungsrolle: [Entscheider/Influencer/User]

Pain Points:
- [Konkretes Problem 1]
- [Konkretes Problem 2]
- [Konkretes Problem 3]

Goals:
- [Ziel 1]
- [Ziel 2]
- [Ziel 3]

Zitat: "[Typische Aussage dieser Persona]" """,

            "comparison": f"""Erstelle einen aussagekräftigen Wettbewerbsvergleich für {brief.customer or 'unser Unternehmen'}.

BRANCHE: {brief.industry or 'B2B'}

WICHTIG: 
- Nenne ECHTE Wettbewerber aus der Branche (z.B. Siemens, Bosch, ABB für Industrie)
- Keine Platzhalter wie "Alternative A"
- Konkrete, messbare Aussagen

FORMAT:
Kriterium | {brief.customer or 'Wir'} | [Echter Wettbewerber 1] | [Echter Wettbewerber 2]
[Kernthema] | ✓ [konkreter Vorteil] | ✗ [Schwäche] | ○ [neutral]
Innovation | [Bewertung mit Begründung] | [Bewertung] | [Bewertung]
Nachhaltigkeit | [Bewertung] | [Bewertung] | [Bewertung]
Preis-Leistung | [Bewertung] | [Bewertung] | [Bewertung]
Service | [Bewertung] | [Bewertung] | [Bewertung]""",


            "chart": f"""Erstelle 4-5 Key Insights mit Daten/Zahlen zum Thema "{title}".
Diese werden in einem Chart visualisiert.

Jeder Insight sollte:
- Eine konkrete Zahl oder Prozentwert enthalten
- Relevant für {brief.industry or 'die Branche'} sein
- Einen Trend oder Vergleich zeigen

Format: Beginne jeden Punkt mit "- " """,

            "timeline": f"""Erstelle eine Roadmap/Timeline mit 4-6 Phasen für {brief.customer or 'das Projekt'}.

Jede Phase sollte enthalten:
- Zeitraum (Q1 2025, Monat 1-3, etc.)
- Kurze Beschreibung der Aktivitäten
- Erwartetes Ergebnis

Format: Beginne jeden Punkt mit "- " """,

            "quote": f"""Erstelle ein überzeugendes Testimonial/Zitat passend zu {brief.customer or 'der Lösung'}.

Das Zitat sollte:
- Einen konkreten Nutzen oder Erfolg beschreiben
- Authentisch klingen
- 2-3 Sätze lang sein

Format:
"[Das Zitat hier]"
- [Name], [Position], [Unternehmen]""",

            "conclusion": f"""Erstelle 4-5 Key Takeaways als Fazit der Präsentation "{brief.topic}".

Jeder Takeaway sollte:
- Eine zentrale Erkenntnis zusammenfassen
- Handlungsorientiert sein
- Zum Briefing-Ziel passen: {brief.objective[:200] if brief.objective else 'Überzeugung der Zielgruppe'}

Format: Beginne jeden Punkt mit einer Nummer "1. ", "2. ", etc.""",
        }
        
        instruction = type_instructions.get(slide_type, type_instructions["bullets"])
        
        prompt = f"""Du bist ein erfahrener Strategieberater und erstellst professionellen Präsentations-Content.

PRÄSENTATION: {brief.topic}
KAPITEL: {chapter_title}
SLIDE-TITEL: {title}
KUNDE: {brief.customer or 'Unternehmen'}
BRANCHE: {brief.industry or 'Business'}
ZIELGRUPPE: {brief.target_audience or 'Entscheider'}

BRIEFING:
{brief.objective[:500] if brief.objective else 'Erstelle überzeugende Inhalte.'}

AUFGABE:
{instruction}

RECHERCHE-KONTEXT:
{self.research_context if hasattr(self, 'research_context') and self.research_context else 'Keine externen Daten verfügbar.'}

INTERNES WISSEN (aus Knowledge Base):
{context.get('knowledge_context', 'Kein spezifisches Wissen verfügbar.')}

WICHTIG - QUALITÄTSREGELN:

SPRACHE:
- Schreibe AUSSCHLIESSLICH auf Deutsch
- Keine englischen Sätze oder Absätze
- Englische Fachbegriffe nur wenn etabliert (z.B. "Marketing", "ROI")

KONKRETHEIT:
- Vermeide generische Phrasen wie "ist wichtig", "muss sich anpassen"
- Jede Aussage braucht konkrete Zahlen, Fakten oder Beispiele
- Beziehe dich immer auf {brief.customer or 'das Unternehmen'} und {brief.industry or 'die Branche'}

QUELLEN:
- Nenne bei Statistiken die Quelle: (Quelle: Statista 2024)
- Sammle alle Quellen für die Quellenfolie

VERBOTEN:
- "Die digitale Transformation ist wichtig/entscheidend"
- "In Zeiten von..." / "Im heutigen Wettbewerb"
- "Max Mustermann" oder offensichtliche Platzhalter
- Wiederholung von Inhalten aus anderen Slides

Der Content muss zum Slide-Titel "{title}" passen.
Antworte NUR mit dem geforderten Content."""

        return prompt
    
    def _parse_response(self, response: str, slide_type: str, context: Dict) -> Dict[str, Any]:
        """Parst die LLM-Response."""
        result = {}
        
        # Extrahiere Quellen aus dem Response
        if response:
            import re
            source_patterns = [
                r'\(Quelle:\s*([^)]+)\)',
                r'\(([^)]*(?:Statista|FAZ|Horizont|BCG|McKinsey|Gartner|IDC|Bitkom|DIHK|IHK|Handelsblatt|VDMA|Destatis|Bundesregierung|EU-Kommission|Fraunhofer|VDI)[^)]*(?:\d{4})?[^)]*)\)',
                r'laut\s+([A-Z][\w\s]+\d{4})',
                r'\(Stand:\s*([^)]+)\)',
            ]
            for pattern in source_patterns:
                try:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    for match in matches:
                        if match and len(match) > 3 and match not in self.collected_sources:
                            self.collected_sources.append(match.strip())
                except:
                    pass
        
        if not response:
            result["bullets"] = ["Strategische Analyse", "Konkrete Maßnahmen", "Messbare Ergebnisse"]
            return result
        
        # Prüfe auf Englisch und ersetze
        english_phrases = {
            "The ": "Die ", "This ": "Dies ", " is ": " ist ", " are ": " sind ",
            " will ": " wird ", " can ": " kann ", " has ": " hat ",
            "strategy": "Strategie", "business": "Geschäft", "market": "Markt",
            "customer": "Kunde", "solution": "Lösung"
        }
        for eng, ger in english_phrases.items():
            if eng in response and response.count(eng) < 3:  # Nur wenn wenige Vorkommen
                response = response.replace(eng, ger)
        
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        
        if slide_type == "persona":
            result["bullets"] = []
            result["pain_points"] = []
            result["goals"] = []
            
            current_section = "info"
            for line in lines:
                line_lower = line.lower()
                
                if line_lower.startswith("name:"):
                    result["persona_name"] = line.split(":", 1)[1].strip()
                elif line_lower.startswith("rolle:") or line_lower.startswith("position:"):
                    result["persona_role"] = line.split(":", 1)[1].strip()
                elif "pain point" in line_lower or line_lower == "pain points:":
                    current_section = "pain"
                elif "goal" in line_lower or "ziel" in line_lower:
                    current_section = "goals"
                elif line_lower.startswith("zitat:") or line_lower.startswith('"'):
                    quote = line.split(":", 1)[1].strip() if ":" in line else line
                    result["quote"] = quote.strip('"').strip("'")
                elif line.startswith("-"):
                    clean = line[1:].strip()
                    if current_section == "pain":
                        result["pain_points"].append(clean)
                    elif current_section == "goals":
                        result["goals"].append(clean)
                    else:
                        result["bullets"].append(clean)
                elif ":" in line and current_section == "info":
                    result["bullets"].append(line)
            
            if not result.get("persona_name"):
                result["persona_name"] = context.get("persona_type", "Zielkunde")
            if not result.get("persona_role"):
                result["persona_role"] = context.get("persona_desc", "Entscheider")
            
            return result
        
        if slide_type == "comparison":
            result["headers"] = ["Aspekt", "Unsere Lösung", "Alternative"]
            result["bullets"] = []
            
            for line in lines:
                if "|" in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        if "kriterium" not in parts[0].lower() and "aspekt" not in parts[0].lower():
                            result["bullets"].extend(parts[:4])
                        else:
                            result["headers"] = parts[:4]
                elif line.startswith("-"):
                    result["bullets"].append(line[1:].strip())
            
            return result
        
        if slide_type == "quote":
            for line in lines:
                if line.startswith('"') or line.startswith("„"):
                    result["quote"] = line.strip('"„"\'')
                elif line.startswith("-") and "quote" in result:
                    result["source"] = line[1:].strip()
                elif not result.get("quote"):
                    result["quote"] = line.strip('"„"\'')
            
            return result
        
        if slide_type == "timeline":
            result["phases"] = []
            for line in lines:
                clean = line.lstrip("-•* ").strip()
                if clean and len(clean) > 5:
                    result["phases"].append(clean)
            return result
        
        if slide_type == "conclusion":
            result["bullets"] = []
            for line in lines:
                clean = line.lstrip("-•*0123456789.) ").strip()
                if clean and len(clean) > 10:
                    result["bullets"].append(clean)
            if len(result["bullets"]) > 4:
                result["cta"] = result["bullets"].pop()
            return result
        
        if slide_type == "text":
            # Für Text: Absätze sammeln
            paragraphs = []
            current = []
            for line in lines:
                if line.startswith("-"):
                    if current:
                        paragraphs.append(" ".join(current))
                        current = []
                    paragraphs.append(line[1:].strip())
                else:
                    current.append(line)
            if current:
                paragraphs.append(" ".join(current))
            result["bullets"] = paragraphs if paragraphs else [response]
            return result
        
        # Default: Bullets
        result["bullets"] = []
        for line in lines:
            clean = line.lstrip("-•* ").strip()
            if clean and len(clean) > 5:
                result["bullets"].append(clean)
        
        return result
    
    def _detect_template(self, brief: PresentationBrief) -> str:
        """Erkennt automatisch das beste Template."""
        topic_lower = brief.topic.lower()
        objective_lower = brief.objective.lower()
        
        if any(x in topic_lower for x in ["gtm", "go-to-market", "markteintritt", "launch"]):
            return "gtm_strategy"
        if any(x in topic_lower for x in ["pitch", "investor", "funding", "startup"]):
            return "pitch_deck"
        if any(x in topic_lower for x in ["sales", "verkauf", "angebot", "vertrieb"]):
            return "sales_deck"
        
        return "gtm_strategy"
    
    def generate(self, brief: PresentationBrief, progress_callback=None) -> List[Dict[str, Any]]:
        """Generiert eine komplette Präsentation."""
        
        # Research-Kontext für bessere Inhalte
        if HAS_RESEARCH:
            print("  Recherchiere externe Quellen...")
            self.research_context = generate_research_prompt_context(brief.topic, brief.industry)
            self.topic_enrichment = enrich_topic(brief.topic, brief.industry)
        else:
            self.research_context = ""
            self.topic_enrichment = {}
        
        template_name = self._detect_template(brief)
        self.template = DECK_TEMPLATES.get(template_name, self.template)
        
        print(f"  Template: {self.template['name']}")
        
        slides = []
        chapter_num = 0
        total_slides = sum(len(ch["slides"]) for ch in self.template["chapters"])
        current_slide = 0
        
        for chapter in self.template["chapters"]:
            chapter_name = chapter["name"]
            chapter_title = chapter["title"]
            
            if chapter_name not in ["intro", "closing"]:
                chapter_num += 1
            
            for slide_type in chapter["slides"]:
                current_slide += 1
                
                if progress_callback:
                    progress_callback(current_slide, total_slides, f"{chapter_title}: {slide_type}")
                
                slide = self._generate_slide_content(
                    slide_type=slide_type,
                    chapter_name=chapter_name,
                    chapter_title=chapter_title,
                    brief=brief,
                    slide_index=chapter_num
                )
                
                slides.append(slide)
        
        
        # Füge Quellenfolie vor dem letzten Slide (contact) ein
        if self.collected_sources:
            # Bereinige und dedupliziere Quellen
            cleaned_sources = []
            seen = set()
            skip_patterns = ["eigene", "intern", "unternehmen", "erfahrung"]
            
            for src in self.collected_sources:
                # Normalisiere
                src_clean = src.strip()
                src_clean = src_clean.replace("Quelle: ", "").replace("Quelle:", "")
                src_lower = src_clean.lower()
                
                # Skip interne/eigene Quellen
                if any(skip in src_lower for skip in skip_patterns):
                    continue
                
                # Skip Duplikate (case-insensitive)
                if src_lower in seen:
                    continue
                
                # Skip zu kurze Einträge
                if len(src_clean) < 5:
                    continue
                
                seen.add(src_lower)
                cleaned_sources.append(src_clean)
            
            unique_sources = cleaned_sources
            # Reichere Quellen mit URLs an
            try:
                from services.source_urls import enrich_sources
                enriched_sources = enrich_sources(unique_sources[:20])
            except:
                enriched_sources = unique_sources[:20]
            
            sources_slide = {
                "type": "sources",
                "title": "Quellen & Referenzen",
                "sources": enriched_sources
            }
            # Füge vor dem letzten Slide ein (contact)
            if slides and slides[-1].get("type") == "contact":
                slides.insert(-1, sources_slide)
            else:
                slides.append(sources_slide)
            print(f"  Quellenfolie mit {len(unique_sources)} Quellen hinzugefügt")
        
        # Skaliere auf gewünschte Slide-Anzahl wenn nötig
        if hasattr(brief, 'slide_count') and brief.slide_count and len(slides) < brief.slide_count:
            try:
                from services.plan_scale import expand_to_length
                plan = [{"kind": s.get("type", "content"), "title": s.get("title", ""), "bullets": s.get("bullets", [])} for s in slides]
                expanded = expand_to_length(plan, brief.slide_count)
                slides = [{"type": p.get("kind", "content"), "title": p.get("title", ""), "bullets": p.get("bullets", [])} for p in expanded]
                print(f"  Slides skaliert: {len(slides)} (Ziel: {brief.slide_count})")
            except Exception as e:
                print(f"  Skalierung übersprungen: {e}")
        return slides


def generate_presentation_from_brief(
    topic: str,
    objective: str = "",
    customer: str = "",
    industry: str = "",
    target_audience: str = "",
    slide_count: int = 30,
    template: str = "auto",
    output_path: str = None,
    auto_images: bool = True
) -> Dict[str, Any]:
    """Hauptfunktion: Generiert komplette Präsentation aus Briefing."""
    
    start_time = time.time()
    
    brief = PresentationBrief(
        topic=topic,
        objective=objective,
        customer=customer,
        industry=industry,
        target_audience=target_audience,
        slide_count=slide_count
    )
    
    generator = IntelligentDeckGenerator(template if template != "auto" else "gtm_strategy")
    
    print(f"Generiere: {topic}")
    
    def progress(current, total, title):
        pct = current / total * 100 if total > 0 else 0
        bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
        print(f"  [{bar}] {pct:5.1f}% - {title[:35]}")
    
    slides = generator.generate(brief, progress_callback=progress)
    
    # PPTX erstellen
    from services.pptx_designer_v3 import PPTXDesignerV3
    
    designer = PPTXDesignerV3(company_name=customer, auto_images=auto_images)
    pptx_bytes = designer.create_presentation(slides=slides, title=topic, company=customer)
    
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pptx_bytes)
    
    duration = time.time() - start_time
    
    return {
        "ok": True,
        "slides_count": len(slides),
        "llm_calls": generator.llm_calls,
        "duration_seconds": round(duration, 1),
        "output_path": str(output_path) if output_path else None,
        "size_kb": round(len(pptx_bytes) / 1024, 1),
        "pptx_bytes": pptx_bytes,
        "slides": slides
    }
