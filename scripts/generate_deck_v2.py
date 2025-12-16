#!/usr/bin/env python3
"""
STRATGEN CLI Generator v2 - Intelligente Präsentationserstellung.

Erstellt professionelle Strategie-Präsentationen mit:
- Kapitel-basierter Struktur
- Verschiedenen Slide-Typen
- Knowledge Base Integration
- Professionellem PPTX Export

Verwendung:
    python generate_deck_v2.py --topic "Mein Thema" --slides 50 --output deck.pptx
    python generate_deck_v2.py --topic "GTM Strategie" --template gtm --slides 80

Author: Stratgen Team
Version: 2.0
"""

import sys
import os
import time
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Pfad für Stratgen-Module
STRATGEN_DIR = os.getenv("STRATGEN_DIR", "/home/sodaen/stratgen")
sys.path.insert(0, STRATGEN_DIR)

from pptx_designer_v3 import PPTXDesignerV3
from slide_structure_engine import SlideStructureEngine, create_gtm_structure


def print_header():
    """Zeigt Header an."""
    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  STRATGEN INTELLIGENT PRESENTATION GENERATOR v2                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()


def print_progress(current: int, total: int, title: str, elapsed: float):
    """Zeigt Fortschritt an."""
    pct = current / total * 100
    bar_width = 30
    filled = int(bar_width * current / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    # Geschätzte Restzeit
    if current > 0:
        eta = (elapsed / current) * (total - current)
        eta_str = f"{eta:.0f}s"
    else:
        eta_str = "..."
    
    print(f"\r  [{bar}] {pct:5.1f}% | Slide {current:3d}/{total} | {title[:35]:<35} | ETA: {eta_str}  ", end="", flush=True)


async def generate_slide_content(
    slide_def: Dict[str, Any],
    topic: str,
    brief: str,
    customer_name: str,
    industry: str,
    use_knowledge: bool = True
) -> Dict[str, Any]:
    """
    Generiert Content für einen einzelnen Slide.
    
    Args:
        slide_def: Slide-Definition aus der Struktur
        topic: Präsentationsthema
        brief: Briefing-Text
        customer_name: Kundenname
        industry: Branche
        use_knowledge: Knowledge Base verwenden
    
    Returns:
        Slide-Daten mit generiertem Content
    """
    slide_type = slide_def.get("type", "bullets")
    title = slide_def.get("title", "")
    content_hint = slide_def.get("content_hint", "")
    
    # Knowledge Base durchsuchen
    knowledge_snippets = []
    if use_knowledge:
        try:
            from services.knowledge_enhanced import search_knowledge_base
            
            # Suchqueries basierend auf Slide
            queries = [title, topic, f"{title} {industry}"]
            
            seen = set()
            for query in queries[:2]:
                results = search_knowledge_base(query, k=3)
                for r in results:
                    if r.score >= 0.6 and r.title not in seen:
                        seen.add(r.title)
                        knowledge_snippets.append({
                            "title": r.title,
                            "content": r.snippet[:400],
                            "score": r.score
                        })
            
            knowledge_snippets = sorted(knowledge_snippets, key=lambda x: -x["score"])[:4]
        except Exception:
            pass
    
    # LLM-Prompt basierend auf Slide-Typ
    prompt = _build_prompt(slide_type, title, topic, brief, customer_name, industry, content_hint, knowledge_snippets)
    
    # LLM aufrufen
    try:
        from services.llm import generate as llm_generate
        
        response = llm_generate(prompt, temperature=0.7, max_tokens=800)
        
        # Response parsen
        bullets = _parse_response(response, slide_type)
        
    except Exception as e:
        # Fallback
        bullets = [
            f"Strategischer Punkt zu {title}",
            f"Relevante Analyse für {topic}",
            f"Handlungsempfehlung für {industry}",
            f"Nächste Schritte definieren"
        ]
    
    # Slide-Daten zusammenstellen
    return {
        "type": slide_type,
        "title": title,
        "bullets": bullets,
        "content": "\n\n".join(bullets) if slide_type == "text" else "",
        "notes": f"Slide: {title}",
        "layout_hint": _get_layout_hint(slide_type),
        "knowledge_used": len(knowledge_snippets) > 0,
        "sources": [ks["title"] for ks in knowledge_snippets] if knowledge_snippets else []
    }


def _build_prompt(
    slide_type: str,
    title: str,
    topic: str,
    brief: str,
    customer: str,
    industry: str,
    hint: str,
    knowledge: List[Dict]
) -> str:
    """Erstellt den LLM-Prompt."""
    
    knowledge_context = ""
    if knowledge:
        knowledge_context = "\n\nRELEVANTES WISSEN:\n"
        for k in knowledge[:3]:
            knowledge_context += f"[{k['title']}]: {k['content'][:300]}\n\n"
    
    type_instructions = {
        "title": "Erstelle einen eindrucksvollen Haupttitel und Untertitel.",
        "chapter": "Erstelle einen kurzen, prägnanten Kapitel-Titel und optionalen Untertitel.",
        "executive_summary": "Erstelle 4-5 Key Points, die das Wichtigste zusammenfassen. Jeder Punkt sollte 1-2 Sätze haben.",
        "bullets": "Erstelle 4-6 prägnante Bullet Points. Jeder Bullet sollte 1-2 vollständige Sätze sein, keine Stichworte.",
        "text": "Erstelle 2-3 ausführliche Absätze (insgesamt 300-500 Wörter) mit Herleitung und Analyse.",
        "persona": "Erstelle eine Persona: Name, Rolle, Alter, Unternehmensgröße, 3 Pain Points, 3 Goals, 1 typisches Zitat.",
        "comparison": "Erstelle Vergleichspunkte für 3 Optionen/Wettbewerber. Pro Option 3-4 Merkmale.",
        "chart": "Erstelle 4-5 Key Insights zu Daten/Statistiken, die visualisiert werden sollten.",
        "timeline": "Erstelle 4-6 Phasen/Meilensteine mit Zeitangaben und Beschreibung.",
        "quote": "Erstelle ein aussagekräftiges Zitat (1-2 Sätze) mit fiktiver aber realistischer Quelle.",
        "conclusion": "Erstelle 3-5 nummerierte Key Takeaways als Fazit.",
        "contact": "Erstelle einen freundlichen Abschluss mit Einladung zur Diskussion."
    }
    
    instruction = type_instructions.get(slide_type, type_instructions["bullets"])
    
    prompt = f"""Du bist ein erfahrener Strategieberater und erstellst professionellen Präsentations-Content.

PRÄSENTATION: {topic}
KUNDE: {customer or 'Unternehmen'}
BRANCHE: {industry or 'Business'}
SLIDE-TITEL: {title}
SLIDE-TYP: {slide_type}

BRIEFING:
{brief[:500] if brief else 'Erstelle eine professionelle Strategie-Präsentation.'}
{knowledge_context}

AUFGABE: {instruction}

{hint}

WICHTIG:
- Schreibe professionell und überzeugend
- Nutze konkrete Fakten und Zahlen wo möglich
- Vermeide Floskeln und allgemeine Aussagen
- Jeder Punkt sollte einen klaren Mehrwert bieten
- Verwende die Knowledge Base Informationen sinnvoll

Antworte NUR mit dem Content, keine Erklärungen. Für Bullets: Ein Bullet pro Zeile, beginnend mit "• "."""

    return prompt


def _parse_response(response: str, slide_type: str) -> List[str]:
    """Parst die LLM-Response zu Bullets."""
    if not response:
        return ["Kein Content generiert"]
    
    lines = response.strip().split("\n")
    bullets = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Entferne Bullet-Zeichen
        for prefix in ["• ", "- ", "* ", "→ "]:
            if line.startswith(prefix):
                line = line[len(prefix):]
                break
        
        # Entferne Nummerierung
        if line and line[0].isdigit() and (line[1] == "." or line[1] == ")"):
            line = line[2:].strip()
        
        if line and len(line) > 10:
            bullets.append(line)
    
    # Für Text-Slides: Behalte Absätze
    if slide_type == "text" and len(bullets) < 3:
        # Keine echten Bullets gefunden, behandle als Fließtext
        paragraphs = response.strip().split("\n\n")
        bullets = [p.strip() for p in paragraphs if p.strip()]
    
    return bullets[:8] if bullets else ["Strategische Analyse erforderlich"]


def _get_layout_hint(slide_type: str) -> str:
    """Gibt Layout-Hinweis für Slide-Typ."""
    hints = {
        "title": "Title Slide",
        "chapter": "Section Header",
        "executive_summary": "Two Content",
        "bullets": "Title and Content",
        "text": "Title and Content",
        "persona": "Picture with Caption",
        "comparison": "Comparison",
        "chart": "Title and Content",
        "timeline": "Title and Content",
        "quote": "Quote",
        "conclusion": "Title and Content",
        "contact": "Title Slide"
    }
    return hints.get(slide_type, "Title and Content")


async def generate_presentation(
    topic: str,
    brief: str = "",
    customer_name: str = "",
    industry: str = "",
    target_slides: int = 50,
    template: str = "gtm_strategy",
    use_knowledge: bool = True,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Generiert eine komplette Präsentation.
    
    Args:
        topic: Präsentationsthema
        brief: Briefing-Text
        customer_name: Kundenname
        industry: Branche
        target_slides: Ziel-Anzahl Slides
        template: Template (gtm_strategy, pitch_deck)
        use_knowledge: Knowledge Base verwenden
        output_path: Ausgabe-Pfad für PPTX
    
    Returns:
        Ergebnis-Dict mit Statistiken
    """
    start_time = time.time()
    
    # 1. Struktur generieren
    print("  Generiere Struktur...")
    engine = SlideStructureEngine(template=template)
    structure = engine.generate_structure(
        topic=topic,
        target_slides=target_slides,
        customer_name=customer_name,
        industry=industry,
        brief=brief
    )
    
    print(f"  → {len(structure)} Slides geplant")
    print()
    
    # 2. Content für jeden Slide generieren
    slides = []
    knowledge_count = 0
    
    for i, slide_def in enumerate(structure, 1):
        elapsed = time.time() - start_time
        print_progress(i, len(structure), slide_def.get("title", ""), elapsed)
        
        slide_data = await generate_slide_content(
            slide_def=slide_def,
            topic=topic,
            brief=brief,
            customer_name=customer_name,
            industry=industry,
            use_knowledge=use_knowledge
        )
        
        slides.append(slide_data)
        
        if slide_data.get("knowledge_used"):
            knowledge_count += 1
    
    print()
    print()
    
    # 3. PPTX erstellen
    print("  Erstelle PPTX...")
    
    designer = PPTXDesignerV3(
        palette="corporate",
        company_name=customer_name,
        include_slide_numbers=True
    )
    
    pptx_bytes = designer.create_presentation(
        slides=slides,
        title=topic,
        company=customer_name,
        include_sources_slide=True
    )
    
    # 4. Speichern
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(pptx_bytes)
        
        size_kb = len(pptx_bytes) / 1024
        print(f"  → Gespeichert: {output_path} ({size_kb:.1f} KB)")
    
    duration = time.time() - start_time
    
    return {
        "ok": True,
        "slides_count": len(slides),
        "knowledge_slides": knowledge_count,
        "duration_seconds": round(duration, 1),
        "slides_per_minute": round(len(slides) / (duration / 60), 1) if duration > 0 else 0,
        "output_path": str(output_path) if output_path else None,
        "slides": slides
    }


def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description="STRATGEN Intelligent Presentation Generator v2"
    )
    parser.add_argument("--topic", required=True, help="Präsentationsthema")
    parser.add_argument("--brief", default="", help="Ausführliches Briefing")
    parser.add_argument("--customer", default="", help="Kundenname")
    parser.add_argument("--industry", default="", help="Branche")
    parser.add_argument("--slides", type=int, default=50, help="Anzahl Slides (default: 50)")
    parser.add_argument("--template", default="gtm_strategy", help="Template (gtm_strategy, pitch_deck)")
    parser.add_argument("--output", default="", help="Ausgabe-Pfad (.pptx)")
    parser.add_argument("--no-knowledge", action="store_true", help="Knowledge Base nicht verwenden")
    parser.add_argument("--json", action="store_true", help="Auch JSON ausgeben")
    
    args = parser.parse_args()
    
    print_header()
    
    print(f"  Thema:    {args.topic}")
    print(f"  Kunde:    {args.customer or '(nicht angegeben)'}")
    print(f"  Branche:  {args.industry or '(nicht angegeben)'}")
    print(f"  Slides:   {args.slides}")
    print(f"  Template: {args.template}")
    print()
    
    # Output-Pfad
    if not args.output:
        safe_topic = "".join(c if c.isalnum() else "-" for c in args.topic[:30])
        timestamp = int(time.time())
        args.output = f"data/exports/{safe_topic}-{timestamp}.pptx"
    
    # Generation starten
    result = asyncio.run(generate_presentation(
        topic=args.topic,
        brief=args.brief,
        customer_name=args.customer,
        industry=args.industry,
        target_slides=args.slides,
        template=args.template,
        use_knowledge=not args.no_knowledge,
        output_path=args.output
    ))
    
    # JSON speichern falls gewünscht
    if args.json and result.get("slides"):
        json_path = Path(args.output).with_suffix(".json")
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  → JSON: {json_path}")
    
    # Ergebnis
    print()
    print("═" * 67)
    print(f"  ✅ Generierung abgeschlossen!")
    print(f"  Slides:     {result['slides_count']}")
    print(f"  Dauer:      {result['duration_seconds']}s")
    print(f"  Speed:      {result['slides_per_minute']} slides/min")
    print(f"  Knowledge:  {result['knowledge_slides']}/{result['slides_count']} Slides")
    print(f"  Output:     {result['output_path']}")
    print("═" * 67)
    print()


if __name__ == "__main__":
    main()
