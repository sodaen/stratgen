# STRATGEN v3.35 - Intelligente Präsentations-Architektur

## PROBLEM-ANALYSE

### Aktueller Zustand:
1. PPTXDesignerV2 fügt Bullets NICHT korrekt ein
2. Alle Slides haben das gleiche Format (Titel + Bullets)
3. Keine Kapitel-Struktur
4. Keine kontextsensitive Darstellung
5. Keine Bilder/Graphen Integration

### Ziel-Zustand:
Eine professionelle Strategie-Präsentation mit:
- Kapitel-Slides mit Hero-Bildern
- Verschiedene Slide-Typen (Bullets, Text, Graph, Persona, Vergleich)
- Intelligente Content-Verteilung
- Logische Themen-Herleitung über mehrere Slides

## ARCHITEKTUR-ENTSCHEIDUNG

### Option A: PPTXDesignerV2 fixen + erweitern
- Bullet-Bug fixen
- Neue Slide-Typen hinzufügen
- Layout-Engine erweitern

### Option B: Komplett neues Presentation Engine (empfohlen)
- Modulares Design
- Content-Type-aware Rendering
- Template-basiert
- Erweiterbar

## SLIDE-TYPEN (neu)

| Typ | Verwendung | Layout |
|-----|------------|--------|
| chapter | Kapitel-Eröffnung | Hero-Bild + Großer Titel |
| title | Deck-Titel | Logo, Titel, Untertitel, Datum |
| executive_summary | Zusammenfassung | 2-Spalten, Key Points |
| bullets | Standard-Content | Titel + 4-6 Bullets |
| text | Ausführlicher Text | Titel + Fließtext (Herleitung) |
| persona | Persona-Steckbrief | Bild + Daten + Eigenschaften |
| comparison | Vergleich/Matrix | Tabelle oder Spalten |
| chart | Daten-Visualisierung | Graph + Interpretation |
| quote | Zitat/Testimonial | Großes Zitat + Quelle |
| timeline | Roadmap/Timeline | Horizontale Zeitleiste |
| conclusion | Fazit/Key Takeaways | Numbered Key Points |
| contact | Kontakt-Slide | Logo + Kontaktdaten |

## KAPITEL-STRUKTUR (für GTM)

1. **KAPITEL: Einführung**
   - chapter: "Markteinführung ProjectAI"
   - title: Deck-Titel
   - executive_summary

2. **KAPITEL: Marktanalyse**
   - chapter: "Der Markt"
   - text: Markt-Herleitung
   - chart: TAM/SAM/SOM
   - bullets: Key Insights

3. **KAPITEL: Wettbewerb**
   - chapter: "Wettbewerbslandschaft"
   - comparison: Feature-Matrix
   - text: Analyse
   - bullets: Differenzierung

4. **KAPITEL: Zielgruppen**
   - chapter: "Unsere Kunden"
   - persona: CTO Persona
   - persona: IT-Leiter Persona
   - bullets: Buying Journey

5. **KAPITEL: Strategie**
   - chapter: "Go-to-Market Strategie"
   - text: Ansatz-Herleitung
   - chart: Pricing
   - timeline: Roadmap
   - bullets: Key Actions

6. **KAPITEL: Abschluss**
   - conclusion: Key Takeaways
   - contact: Kontakt

## IMPLEMENTIERUNG

### Phase 1: Bullet-Bug fixen (sofort)
- PPTXDesignerV2._add_content_slide() prüfen
- Bullets korrekt in Placeholder einfügen

### Phase 2: Slide-Type Routing
- Slide-Daten enthalten "type" und "content_type"
- PPTXDesignerV2 routet zu korrekter Render-Methode

### Phase 3: Neue Slide-Typen
- _add_chapter_slide()
- _add_persona_slide()
- _add_comparison_slide()
- _add_text_slide()
- _add_chart_slide()

### Phase 4: Intelligente Struktur
- live_generator.py: Kapitel-basierte Struktur
- Content-Komplexität → Slide-Typ Mapping
