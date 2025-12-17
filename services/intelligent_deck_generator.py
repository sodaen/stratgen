"""
Intelligenter Präsentations-Generator für Stratgen.

Generiert komplette Präsentationen aus einem einzigen Briefing:
- Analysiert das Briefing
- Plant die optimale Struktur
- Generiert jeden Slide-Inhalt mit LLM
- Wählt passende Slide-Typen
- Fügt automatisch Bilder hinzu

Author: Stratgen Team
Version: 1.0
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

# Stratgen imports
sys.path.insert(0, '/home/sodaen/stratgen')


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


# Kapitel-Templates für verschiedene Präsentationstypen
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
            {"name": "problem", "title": "Problem", "slides": ["chapter", "text"]},
            {"name": "solution", "title": "Lösung", "slides": ["chapter", "text", "bullets"]},
            {"name": "product", "title": "Produkt", "slides": ["chapter", "bullets", "comparison"]},
            {"name": "market", "title": "Markt", "slides": ["chapter", "chart"]},
            {"name": "business", "title": "Business Model", "slides": ["chapter", "chart", "bullets"]},
            {"name": "traction", "title": "Traction", "slides": ["chapter", "chart"]},
            {"name": "team", "title": "Team", "slides": ["chapter", "persona", "persona"]},
            {"name": "ask", "title": "Investment", "slides": ["chapter", "bullets", "contact"]},
        ]
    },
    "sales_deck": {
        "name": "Sales Präsentation",
        "chapters": [
            {"name": "intro", "title": "", "slides": ["title", "executive_summary"]},
            {"name": "challenge", "title": "Herausforderung", "slides": ["chapter", "text", "bullets"]},
            {"name": "solution", "title": "Unsere Lösung", "slides": ["chapter", "text", "bullets", "comparison"]},
            {"name": "benefits", "title": "Vorteile", "slides": ["chapter", "bullets", "quote"]},
            {"name": "cases", "title": "Referenzen", "slides": ["chapter", "text", "quote"]},
            {"name": "pricing", "title": "Angebot", "slides": ["chapter", "chart", "bullets"]},
            {"name": "closing", "title": "Nächste Schritte", "slides": ["conclusion", "contact"]},
        ]
    },
    "report": {
        "name": "Bericht / Analyse",
        "chapters": [
            {"name": "intro", "title": "", "slides": ["title", "executive_summary"]},
            {"name": "background", "title": "Hintergrund", "slides": ["chapter", "text"]},
            {"name": "analysis", "title": "Analyse", "slides": ["chapter", "text", "chart", "bullets"]},
            {"name": "findings", "title": "Ergebnisse", "slides": ["chapter", "bullets", "chart"]},
            {"name": "recommendations", "title": "Empfehlungen", "slides": ["chapter", "bullets", "text"]},
            {"name": "closing", "title": "Fazit", "slides": ["conclusion", "contact"]},
        ]
    }
}


class IntelligentDeckGenerator:
    """
    Generiert intelligente Präsentationen aus Briefings.
    """
    
    def __init__(self, template: str = "gtm_strategy"):
        self.template = DECK_TEMPLATES.get(template, DECK_TEMPLATES["gtm_strategy"])
        self.llm_calls = 0
        self.total_tokens = 0
    
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Ruft das LLM auf."""
        try:
            from services.llm import generate
            self.llm_calls += 1
            result = generate(prompt, temperature=0.7, max_tokens=max_tokens)
            # Handle dict response from Ollama
            if isinstance(result, dict):
                if result.get('ok'):
                    return result.get('response', '')
                else:
                    print(f"LLM Error: {result.get('error', 'Unknown')}")
                    return ""
            return str(result)
        except Exception as e:
            print(f"LLM Error: {e}")
            return ""
    
    def _detect_template(self, brief: PresentationBrief) -> str:
        """Erkennt automatisch das beste Template."""
        topic_lower = brief.topic.lower()
        objective_lower = brief.objective.lower()
        
        if any(x in topic_lower for x in ["gtm", "go-to-market", "markteintritt", "launch"]):
            return "gtm_strategy"
        if any(x in topic_lower for x in ["pitch", "investor", "funding", "startup"]):
            return "pitch_deck"
        if any(x in topic_lower for x in ["sales", "verkauf", "angebot", "kunde"]):
            return "sales_deck"
        if any(x in topic_lower for x in ["report", "bericht", "analyse", "studie"]):
            return "report"
        
        # Default basierend auf Objective
        if any(x in objective_lower for x in ["verkaufen", "ueberzeugen"]):
            return "sales_deck"
        if any(x in objective_lower for x in ["investment", "finanzierung"]):
            return "pitch_deck"
        
        return "gtm_strategy"
    
    def _generate_slide_content(
        self,
        slide_type: str,
        chapter_title: str,
        brief: PresentationBrief,
        slide_index: int,
        chapter_context: str = ""
    ) -> Dict[str, Any]:
        """Generiert den Inhalt für einen einzelnen Slide."""
        
        # Basis-Struktur
        slide = {"type": slide_type}
        
        # Spezielle Prompts je nach Slide-Typ
        if slide_type == "title":
            slide["title"] = brief.topic
            slide["subtitle"] = brief.objective or f"Präsentation für {brief.customer}" if brief.customer else ""
            return slide
        
        if slide_type == "contact":
            slide["title"] = "Vielen Dank!"
            slide["subtitle"] = "Fragen und Diskussion"
            slide["bullets"] = [brief.customer] if brief.customer else []
            return slide
        
        if slide_type == "chapter":
            slide["title"] = chapter_title
            slide["chapter_number"] = str(slide_index)
            return slide
        
        # LLM für komplexere Slides
        prompt = self._build_slide_prompt(slide_type, chapter_title, brief, chapter_context)
        response = self._call_llm(prompt, max_tokens=600)
        
        # Response parsen
        parsed = self._parse_llm_response(response, slide_type)
        slide.update(parsed)
        
        return slide
    
    def _build_slide_prompt(
        self,
        slide_type: str,
        chapter_title: str,
        brief: PresentationBrief,
        context: str
    ) -> str:
        """Erstellt den Prompt für das LLM."""
        
        type_instructions = {
            "executive_summary": "Erstelle 4-5 Key Points als Executive Summary. Jeder Punkt 1-2 Sätze.",
            "text": "Erstelle 2-3 ausführliche Absätze (insgesamt 200-300 Wörter) mit Analyse und Herleitung.",
            "bullets": "Erstelle 4-6 prägnante Bullet Points. Jeder Bullet 1-2 vollständige Sätze.",
            "persona": "Erstelle eine Buyer Persona mit: Name, Rolle, Alter, 4 Eigenschaften, 3 Pain Points, 3 Goals, 1 Zitat.",
            "comparison": "Erstelle einen Vergleich mit 3 Spalten und je 4 Vergleichspunkten.",
            "chart": "Erstelle 4-5 Datenpunkte/Insights die in einem Chart visualisiert werden könnten.",
            "timeline": "Erstelle 4-6 Phasen/Meilensteine mit Zeitangaben.",
            "quote": "Erstelle ein aussagekräftiges Zitat (1-2 Sätze) mit einer passenden Quelle.",
            "conclusion": "Erstelle 4-5 nummerierte Key Takeaways als Fazit.",
        }
        
        instruction = type_instructions.get(slide_type, type_instructions["bullets"])
        
        prompt = f"""Du bist ein erfahrener Strategieberater und erstellst Präsentations-Inhalte.

PRÄSENTATION: {brief.topic}
KAPITEL: {chapter_title}
KUNDE: {brief.customer or 'Unternehmen'}
BRANCHE: {brief.industry or 'Business'}
ZIELGRUPPE: {brief.target_audience or 'Entscheider'}
SLIDE-TYP: {slide_type}

BRIEFING:
{brief.objective}

{f"KONTEXT: {context}" if context else ""}

AUFGABE: {instruction}

WICHTIG:
- Schreibe auf Deutsch
- Professionell und überzeugend
- Konkrete Fakten und Zahlen verwenden
- Keine Floskeln
- Passend zum Kapitel "{chapter_title}"

Antworte NUR mit dem Content. Für Bullets/Listen: Ein Punkt pro Zeile, mit "- " am Anfang.
Für Personas: Nutze das Format "Name: ...", "Rolle: ...", "Pain Points: ...", etc."""

        return prompt
    
    def _parse_llm_response(self, response: str, slide_type: str) -> Dict[str, Any]:
        """Parst die LLM-Response."""
        result = {}
        
        if not response:
            result["title"] = "Inhalt"
            result["bullets"] = ["Strategischer Punkt", "Analyse erforderlich"]
            return result
        
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        
        if slide_type == "persona":
            # Persona-Parsing
            result["title"] = "Persona"
            result["bullets"] = []
            result["pain_points"] = []
            result["goals"] = []
            
            current_section = "bullets"
            for line in lines:
                line_lower = line.lower()
                if "name:" in line_lower:
                    result["persona_name"] = line.split(":", 1)[1].strip()
                elif "rolle:" in line_lower or "position:" in line_lower:
                    result["persona_role"] = line.split(":", 1)[1].strip()
                elif "pain" in line_lower:
                    current_section = "pain_points"
                elif "goal" in line_lower or "ziel" in line_lower:
                    current_section = "goals"
                elif "zitat:" in line_lower or "quote:" in line_lower:
                    result["quote"] = line.split(":", 1)[1].strip().strip('"')
                elif line.startswith("-"):
                    clean = line[1:].strip()
                    if current_section == "pain_points":
                        result["pain_points"].append(clean)
                    elif current_section == "goals":
                        result["goals"].append(clean)
                    else:
                        result["bullets"].append(clean)
                elif line and not any(x in line_lower for x in ["eigenschaften", "details"]):
                    result["bullets"].append(line)
            
            result["title"] = f"Persona: {result.get('persona_name', 'Zielkunde')}"
            return result
        
        if slide_type == "comparison":
            result["title"] = "Vergleich"
            result["headers"] = ["Aspekt", "Unsere Lösung", "Alternative"]
            result["bullets"] = []
            for line in lines:
                if line.startswith("-"):
                    result["bullets"].append(line[1:].strip())
                elif "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    result["bullets"].extend(parts)
            return result
        
        if slide_type == "quote":
            result["title"] = "Stimme"
            for line in lines:
                if line.startswith('"') or line.startswith("'"):
                    result["quote"] = line.strip('"\'')
                elif "quelle:" in line.lower() or "-" in line:
                    result["source"] = line.replace("Quelle:", "").replace("-", "").strip()
                else:
                    result["quote"] = line
            return result
        
        if slide_type == "timeline":
            result["title"] = "Roadmap"
            result["phases"] = []
            for line in lines:
                clean = line.lstrip("-•* ").strip()
                if clean:
                    result["phases"].append(clean)
            return result
        
        if slide_type in ["executive_summary", "conclusion"]:
            result["title"] = "Executive Summary" if slide_type == "executive_summary" else "Key Takeaways"
            result["bullets"] = []
            for line in lines:
                clean = line.lstrip("-•*0123456789.) ").strip()
                if clean and len(clean) > 10:
                    result["bullets"].append(clean)
            if slide_type == "conclusion" and len(result["bullets"]) > 4:
                result["cta"] = result["bullets"].pop()
            return result
        
        # Default: Bullets oder Text
        result["title"] = "Inhalt"
        
        if slide_type == "text":
            # Für Text-Slides: Absätze behalten
            result["bullets"] = []
            current_para = []
            for line in lines:
                if line.startswith("-"):
                    if current_para:
                        result["bullets"].append(" ".join(current_para))
                        current_para = []
                    result["bullets"].append(line[1:].strip())
                else:
                    current_para.append(line)
            if current_para:
                result["bullets"].append(" ".join(current_para))
        else:
            # Bullets
            result["bullets"] = []
            for line in lines:
                clean = line.lstrip("-•* ").strip()
                if clean and len(clean) > 5:
                    result["bullets"].append(clean)
        
        return result
    
    def generate(self, brief: PresentationBrief, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Generiert eine komplette Präsentation aus dem Briefing.
        
        Args:
            brief: Das Präsentations-Briefing
            progress_callback: Optional callback(current, total, title)
        
        Returns:
            Liste von Slide-Daten
        """
        # Template erkennen oder verwenden
        template_name = self._detect_template(brief)
        self.template = DECK_TEMPLATES.get(template_name, self.template)
        
        print(f"Verwende Template: {self.template['name']}")
        
        slides = []
        slide_index = 0
        chapter_num = 0
        
        # Berechne Slides pro Kapitel basierend auf Ziel
        total_template_slides = sum(len(ch["slides"]) for ch in self.template["chapters"])
        scale_factor = brief.slide_count / total_template_slides
        
        for chapter in self.template["chapters"]:
            chapter_title = chapter["title"]
            chapter_context = f"Kapitel: {chapter_title}" if chapter_title else ""
            
            if chapter["name"] not in ["intro", "closing"]:
                chapter_num += 1
            
            for slide_type in chapter["slides"]:
                slide_index += 1
                
                if progress_callback:
                    progress_callback(slide_index, brief.slide_count, f"{chapter_title}: {slide_type}")
                
                # Generiere Slide
                slide = self._generate_slide_content(
                    slide_type=slide_type,
                    chapter_title=chapter_title,
                    brief=brief,
                    slide_index=chapter_num,
                    chapter_context=chapter_context
                )
                
                slides.append(slide)
                
                # Zusätzliche Slides bei hohem Scale-Factor
                if scale_factor > 1.5 and slide_type in ["bullets", "text"]:
                    extra = int(scale_factor) - 1
                    for i in range(extra):
                        slide_index += 1
                        extra_slide = self._generate_slide_content(
                            slide_type="bullets",
                            chapter_title=f"{chapter_title} - Details",
                            brief=brief,
                            slide_index=chapter_num,
                            chapter_context=chapter_context
                        )
                        slides.append(extra_slide)
        
        print(f"LLM-Aufrufe: {self.llm_calls}")
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
    """
    Hauptfunktion: Generiert eine komplette Präsentation aus einem Briefing.
    
    Args:
        topic: Präsentationsthema
        objective: Ziel der Präsentation
        customer: Kundenname
        industry: Branche
        target_audience: Zielgruppe
        slide_count: Gewünschte Slide-Anzahl
        template: Template (auto, gtm_strategy, pitch_deck, sales_deck, report)
        output_path: Pfad für PPTX-Output
        auto_images: Automatisch Bilder hinzufügen
    
    Returns:
        Dict mit Ergebnis-Infos
    """
    start_time = time.time()
    
    # Briefing erstellen
    brief = PresentationBrief(
        topic=topic,
        objective=objective,
        customer=customer,
        industry=industry,
        target_audience=target_audience,
        slide_count=slide_count
    )
    
    # Generator
    if template == "auto":
        generator = IntelligentDeckGenerator()
    else:
        generator = IntelligentDeckGenerator(template=template)
    
    # Slides generieren
    print(f"Generiere Präsentation: {topic}")
    print(f"Ziel: {slide_count} Slides")
    print()
    
    def progress(current, total, title):
        pct = current / total * 100 if total > 0 else 0
        print(f"  [{current:3d}/{total}] {pct:5.1f}% - {title[:40]}")
    
    slides = generator.generate(brief, progress_callback=progress)
    
    # PPTX erstellen
    from services.pptx_designer_v3 import PPTXDesignerV3
    
    designer = PPTXDesignerV3(
        company_name=customer,
        auto_images=auto_images
    )
    
    pptx_bytes = designer.create_presentation(
        slides=slides,
        title=topic,
        company=customer
    )
    
    # Speichern
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pptx_bytes)
    
    duration = time.time() - start_time
    
    return {
        "ok": True,
        "slides_count": len(slides),
        "llm_calls": generator.llm_calls,
        "duration_seconds": round(duration, 1),
        "output_path": str(output_path) if output_path else None,
        "size_kb": len(pptx_bytes) / 1024,
        "slides": slides
    }


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligenter Präsentations-Generator")
    parser.add_argument("--topic", required=True, help="Präsentationsthema")
    parser.add_argument("--objective", default="", help="Ziel der Präsentation")
    parser.add_argument("--customer", default="", help="Kundenname")
    parser.add_argument("--industry", default="", help="Branche")
    parser.add_argument("--slides", type=int, default=30, help="Anzahl Slides")
    parser.add_argument("--template", default="auto", help="Template")
    parser.add_argument("--output", default="", help="Output-Pfad")
    parser.add_argument("--no-images", action="store_true", help="Keine Bilder")
    
    args = parser.parse_args()
    
    if not args.output:
        safe_topic = "".join(c if c.isalnum() else "-" for c in args.topic[:30])
        args.output = f"data/exports/{safe_topic}-intelligent.pptx"
    
    result = generate_presentation_from_brief(
        topic=args.topic,
        objective=args.objective,
        customer=args.customer,
        industry=args.industry,
        slide_count=args.slides,
        template=args.template,
        output_path=args.output,
        auto_images=not args.no_images
    )
    
    print()
    print("=" * 60)
    print(f"Ergebnis:")
    print(f"  Slides: {result['slides_count']}")
    print(f"  LLM-Aufrufe: {result['llm_calls']}")
    print(f"  Dauer: {result['duration_seconds']}s")
    print(f"  Größe: {result['size_kb']:.1f} KB")
    print(f"  Output: {result['output_path']}")
    print("=" * 60)
