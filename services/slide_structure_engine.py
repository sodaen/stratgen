"""
Intelligente Slide-Struktur-Engine für Stratgen.

Erstellt professionelle Präsentationsstrukturen mit:
- Kapitel-basierter Organisation
- Kontextsensitiven Slide-Typen
- Logischen Herleitung-Sequenzen
- Verschiedenen Content-Formaten (Bullets, Text, Persona, Charts, etc.)

Author: Stratgen Team
Version: 1.0
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class SlideType(Enum):
    """Verfügbare Slide-Typen."""
    TITLE = "title"
    CHAPTER = "chapter"
    EXECUTIVE_SUMMARY = "executive_summary"
    BULLETS = "bullets"
    TEXT = "text"
    PERSONA = "persona"
    COMPARISON = "comparison"
    CHART = "chart"
    TIMELINE = "timeline"
    QUOTE = "quote"
    CONCLUSION = "conclusion"
    CONTACT = "contact"


@dataclass
class ChapterTemplate:
    """Template für ein Kapitel."""
    name: str
    title: str
    subtitle: str
    slides: List[Tuple[SlideType, str, str]]  # (type, title, description)


# ========================================
# VORDEFINIERTE KAPITEL-TEMPLATES
# ========================================

GTM_STRATEGY_CHAPTERS = [
    ChapterTemplate(
        name="intro",
        title="Einführung",
        subtitle="Überblick und Zielsetzung",
        slides=[
            (SlideType.TITLE, "{topic}", "Deckblatt"),
            (SlideType.EXECUTIVE_SUMMARY, "Executive Summary", "Die wichtigsten Punkte auf einen Blick"),
            (SlideType.TEXT, "Ausgangssituation", "Kontext und Hintergrund"),
            (SlideType.BULLETS, "Zielsetzung", "Was wir erreichen wollen"),
        ]
    ),
    ChapterTemplate(
        name="market",
        title="Marktanalyse",
        subtitle="Verstehen des Marktes und seiner Dynamiken",
        slides=[
            (SlideType.CHAPTER, "Der Markt", "Marktanalyse und Potenzial"),
            (SlideType.TEXT, "Marktüberblick", "Größe, Wachstum und Trends"),
            (SlideType.CHART, "TAM / SAM / SOM", "Marktpotenzial-Analyse"),
            (SlideType.BULLETS, "Markttrends", "Die wichtigsten Entwicklungen"),
            (SlideType.TEXT, "Markt-Dynamiken", "Treiber und Barrieren"),
        ]
    ),
    ChapterTemplate(
        name="competition",
        title="Wettbewerb",
        subtitle="Wettbewerbslandschaft und Positionierung",
        slides=[
            (SlideType.CHAPTER, "Wettbewerbsanalyse", "Positionierung im Markt"),
            (SlideType.COMPARISON, "Wettbewerber-Übersicht", "Die wichtigsten Player"),
            (SlideType.CHART, "Feature-Matrix", "Funktionsvergleich"),
            (SlideType.TEXT, "Wettbewerbsvorteile", "Unsere Differenzierung"),
            (SlideType.BULLETS, "Positionierung", "Wie wir uns abheben"),
        ]
    ),
    ChapterTemplate(
        name="customers",
        title="Zielgruppen",
        subtitle="Unsere Kunden verstehen",
        slides=[
            (SlideType.CHAPTER, "Zielgruppen & Personas", "Wen wir erreichen wollen"),
            (SlideType.TEXT, "Segmentierung", "Marktsegmente und Priorisierung"),
            (SlideType.PERSONA, "Persona: Entscheider", "C-Level / Geschäftsführung"),
            (SlideType.PERSONA, "Persona: Anwender", "Operatives Team"),
            (SlideType.BULLETS, "Buying Journey", "Der Kaufentscheidungsprozess"),
            (SlideType.TEXT, "Pain Points & Needs", "Herausforderungen der Zielgruppe"),
        ]
    ),
    ChapterTemplate(
        name="value_proposition",
        title="Value Proposition",
        subtitle="Unser Wertversprechen",
        slides=[
            (SlideType.CHAPTER, "Unser Angebot", "Value Proposition"),
            (SlideType.TEXT, "Das Problem", "Welches Problem lösen wir?"),
            (SlideType.TEXT, "Unsere Lösung", "Wie wir das Problem lösen"),
            (SlideType.BULLETS, "Kernnutzen", "Die wichtigsten Vorteile"),
            (SlideType.COMPARISON, "Vorher / Nachher", "Der Unterschied"),
            (SlideType.QUOTE, "Kundennutzen", "Was Kunden sagen"),
        ]
    ),
    ChapterTemplate(
        name="strategy",
        title="Go-to-Market Strategie",
        subtitle="Wie wir den Markt erobern",
        slides=[
            (SlideType.CHAPTER, "GTM Strategie", "Unser Marktansatz"),
            (SlideType.TEXT, "Strategischer Ansatz", "Überblick und Philosophie"),
            (SlideType.BULLETS, "Vertriebskanäle", "Wie wir Kunden erreichen"),
            (SlideType.CHART, "Pricing-Strategie", "Preismodell und Pakete"),
            (SlideType.BULLETS, "Marketing-Mix", "Kommunikation und Kampagnen"),
            (SlideType.TEXT, "Content-Strategie", "Thought Leadership aufbauen"),
        ]
    ),
    ChapterTemplate(
        name="execution",
        title="Umsetzung",
        subtitle="Der Weg zum Erfolg",
        slides=[
            (SlideType.CHAPTER, "Umsetzungsplan", "Execution is everything"),
            (SlideType.TIMELINE, "Roadmap", "Phasen und Meilensteine"),
            (SlideType.BULLETS, "Q1 Aktionsplan", "Erste 90 Tage"),
            (SlideType.CHART, "Budget-Allokation", "Investitionen nach Bereich"),
            (SlideType.BULLETS, "Team & Ressourcen", "Was wir brauchen"),
            (SlideType.TEXT, "Risiken & Mitigation", "Herausforderungen managen"),
        ]
    ),
    ChapterTemplate(
        name="metrics",
        title="Erfolgsmessung",
        subtitle="KPIs und Ziele",
        slides=[
            (SlideType.CHAPTER, "Erfolgsmessung", "KPIs und Metriken"),
            (SlideType.CHART, "Ziele Jahr 1", "Quantitative Targets"),
            (SlideType.BULLETS, "Key Performance Indicators", "Was wir messen"),
            (SlideType.TEXT, "ROI-Berechnung", "Business Case"),
        ]
    ),
    ChapterTemplate(
        name="closing",
        title="Abschluss",
        subtitle="Zusammenfassung und nächste Schritte",
        slides=[
            (SlideType.CONCLUSION, "Key Takeaways", "Das Wichtigste in Kürze"),
            (SlideType.BULLETS, "Nächste Schritte", "Immediate Actions"),
            (SlideType.CONTACT, "Vielen Dank!", "Fragen & Diskussion"),
        ]
    ),
]


PITCH_DECK_CHAPTERS = [
    ChapterTemplate(
        name="intro",
        title="",
        subtitle="",
        slides=[
            (SlideType.TITLE, "{topic}", ""),
            (SlideType.TEXT, "Das Problem", "Welches Problem lösen wir?"),
            (SlideType.TEXT, "Unsere Lösung", "Wie wir das Problem lösen"),
        ]
    ),
    ChapterTemplate(
        name="product",
        title="Produkt",
        subtitle="",
        slides=[
            (SlideType.CHAPTER, "Das Produkt", ""),
            (SlideType.BULLETS, "Features", "Was wir bieten"),
            (SlideType.COMPARISON, "Vorher / Nachher", ""),
            (SlideType.QUOTE, "Kundenstimme", ""),
        ]
    ),
    ChapterTemplate(
        name="market",
        title="Markt",
        subtitle="",
        slides=[
            (SlideType.CHAPTER, "Der Markt", ""),
            (SlideType.CHART, "Marktgröße", "TAM / SAM / SOM"),
            (SlideType.COMPARISON, "Wettbewerb", ""),
        ]
    ),
    ChapterTemplate(
        name="business",
        title="Business Model",
        subtitle="",
        slides=[
            (SlideType.CHAPTER, "Business Model", ""),
            (SlideType.CHART, "Pricing", ""),
            (SlideType.CHART, "Financials", ""),
            (SlideType.TIMELINE, "Roadmap", ""),
        ]
    ),
    ChapterTemplate(
        name="team",
        title="Team",
        subtitle="",
        slides=[
            (SlideType.CHAPTER, "Das Team", ""),
            (SlideType.PERSONA, "Gründer 1", ""),
            (SlideType.PERSONA, "Gründer 2", ""),
        ]
    ),
    ChapterTemplate(
        name="ask",
        title="Ask",
        subtitle="",
        slides=[
            (SlideType.CHAPTER, "Der Ask", ""),
            (SlideType.BULLETS, "Investment", ""),
            (SlideType.TIMELINE, "Use of Funds", ""),
            (SlideType.CONTACT, "Let's Talk!", ""),
        ]
    ),
]


# ========================================
# STRUKTUR-GENERATOR
# ========================================

class SlideStructureEngine:
    """
    Generiert intelligente Präsentationsstrukturen.
    """
    
    TEMPLATES = {
        "gtm_strategy": GTM_STRATEGY_CHAPTERS,
        "pitch_deck": PITCH_DECK_CHAPTERS,
    }
    
    def __init__(self, template: str = "gtm_strategy"):
        """
        Initialisiert die Engine.
        
        Args:
            template: Template-Name (gtm_strategy, pitch_deck)
        """
        self.template = self.TEMPLATES.get(template, GTM_STRATEGY_CHAPTERS)
    
    def generate_structure(
        self,
        topic: str,
        target_slides: int = 50,
        customer_name: str = "",
        industry: str = "",
        brief: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generiert eine Slide-Struktur basierend auf dem Template.
        
        Args:
            topic: Präsentationstitel
            target_slides: Ziel-Anzahl Slides
            customer_name: Kundenname
            industry: Branche
            brief: Briefing-Text
        
        Returns:
            Liste von Slide-Definitionen
        """
        structure = []
        chapter_number = 0
        
        # Berechne Slides pro Kapitel
        total_base_slides = sum(len(ch.slides) for ch in self.template)
        expansion_factor = max(1.0, target_slides / total_base_slides)
        
        for chapter in self.template:
            # Kapitel-Opener (falls nicht Intro)
            if chapter.name != "intro" and chapter.name != "closing":
                chapter_number += 1
            
            for slide_type, title_template, description in chapter.slides:
                # Titel mit Variablen ersetzen
                title = title_template.format(
                    topic=topic,
                    customer=customer_name,
                    industry=industry
                )
                
                slide_def = {
                    "type": slide_type.value,
                    "title": title,
                    "chapter": chapter.title,
                    "chapter_number": chapter_number if chapter.name not in ["intro", "closing"] else None,
                    "description": description,
                    "content_hint": self._get_content_hint(slide_type, title, brief),
                }
                
                structure.append(slide_def)
                
                # Bei vielen Slides: Expansion für bestimmte Typen
                if expansion_factor > 1.5 and slide_type in [SlideType.BULLETS, SlideType.TEXT]:
                    # Füge Detail-Slides hinzu
                    for i in range(int(expansion_factor) - 1):
                        detail_slide = {
                            "type": "bullets",
                            "title": f"{title} - Details {i+2}",
                            "chapter": chapter.title,
                            "content_hint": f"Weitere Details zu: {title}",
                        }
                        structure.append(detail_slide)
        
        # Auf Ziel-Anzahl trimmen
        if len(structure) > target_slides:
            structure = structure[:target_slides]
        
        return structure
    
    def _get_content_hint(self, slide_type: SlideType, title: str, brief: str) -> str:
        """Generiert Content-Hinweise für LLM."""
        hints = {
            SlideType.TITLE: "Erstelle einen eindrucksvollen Titel mit Untertitel.",
            SlideType.CHAPTER: "Kurzer, prägnanter Kapitel-Opener.",
            SlideType.EXECUTIVE_SUMMARY: "4-5 Key Points, die das Wichtigste zusammenfassen.",
            SlideType.BULLETS: "4-6 prägnante Bullet Points mit je 1-2 Sätzen.",
            SlideType.TEXT: "2-3 Absätze ausführlicher Erklärungstext (300-500 Wörter).",
            SlideType.PERSONA: "Name, Rolle, Unternehmen, Alter, Pain Points, Goals, Zitat.",
            SlideType.COMPARISON: "2-4 Spalten mit Vergleichspunkten.",
            SlideType.CHART: "Daten und Key Insights zur Visualisierung.",
            SlideType.TIMELINE: "4-6 Phasen mit Zeitangaben.",
            SlideType.QUOTE: "Ein aussagekräftiges Zitat mit Quellenangabe.",
            SlideType.CONCLUSION: "3-5 nummerierte Key Takeaways.",
            SlideType.CONTACT: "Kontaktdaten und Abschluss.",
        }
        return hints.get(slide_type, "Erstelle passenden Content.")
    
    def adjust_for_complexity(
        self,
        structure: List[Dict[str, Any]],
        complexity_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Passt Struktur basierend auf Themen-Komplexität an.
        
        Komplexe Themen bekommen mehr Text-Slides für Herleitung,
        einfache Themen bleiben bei Bullets.
        
        Args:
            structure: Basis-Struktur
            complexity_scores: Dict mit Thema -> Komplexität (0-1)
        
        Returns:
            Angepasste Struktur
        """
        adjusted = []
        
        for slide in structure:
            chapter = slide.get("chapter", "")
            complexity = complexity_scores.get(chapter, 0.5)
            
            # Hohe Komplexität: Bullets -> Text + Bullets (Herleitung + Conclusion)
            if complexity > 0.7 and slide.get("type") == "bullets":
                # Füge Herleitung-Slide ein
                herleitung = slide.copy()
                herleitung["type"] = "text"
                herleitung["title"] = f"{slide['title']} - Analyse"
                herleitung["content_hint"] = "Ausführliche Herleitung und Analyse (2-3 Absätze)."
                adjusted.append(herleitung)
                
                # Original als Conclusion
                slide["title"] = f"{slide['title']} - Fazit"
                slide["content_hint"] = "Zusammenfassung der wichtigsten Punkte in Bullets."
            
            adjusted.append(slide)
        
        return adjusted


def create_gtm_structure(
    topic: str,
    target_slides: int = 50,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Erstellt eine GTM-Strategie Struktur.
    
    Args:
        topic: Präsentationstitel
        target_slides: Ziel-Anzahl Slides
        **kwargs: Weitere Parameter (customer_name, industry, brief)
    
    Returns:
        Liste von Slide-Definitionen
    """
    engine = SlideStructureEngine(template="gtm_strategy")
    return engine.generate_structure(topic, target_slides, **kwargs)


def create_pitch_structure(
    topic: str,
    target_slides: int = 15,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Erstellt eine Pitch Deck Struktur.
    
    Args:
        topic: Präsentationstitel
        target_slides: Ziel-Anzahl Slides
        **kwargs: Weitere Parameter
    
    Returns:
        Liste von Slide-Definitionen
    """
    engine = SlideStructureEngine(template="pitch_deck")
    return engine.generate_structure(topic, target_slides, **kwargs)
