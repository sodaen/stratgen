# STRATGEN – Sprint-Roadmap (Stand: 2026-03-11)

## Abgeschlossen ✅

| Sprint | Version | Features |
|--------|---------|----------|
| Sprint 1 | v3.56.0 | Strategy/Competitor LLM, Self-Learning Hook, Polling-Fix |
| Sprint 2 | v3.56.0 | Auto Images, 8 Layout-Typen, _hex_to_rgb Bug |
| Sprint 3 | v3.56.0 | Data Import (CSV/XLSX→Chart), Multi-Turn Chat + Streaming |
| Sprint 4 | v3.56.0 | Offline Mode, Health-Check, Deploy-Helper |

---

## Sprint 5 – Deep Research Backend (→ v3.57.0)

**Ziel:** Aktive Web-Recherche die direkt in die RAG Knowledge Base einfließt.

### Backend

**`backend/deep_research_api.py`** — neue Endpoints:
- `POST /research/deep/start` – startet eine Recherche-Session (topic, queries, depth)
- `GET  /research/deep/{session_id}/status` – aktueller Fortschritt (SSE-fähig)
- `GET  /research/deep/{session_id}/stream` – Live-Fortschritt als SSE
- `GET  /research/deep/{session_id}/results` – Ergebnisse abrufen
- `POST /research/deep/{session_id}/ingest` – Ergebnisse → Qdrant knowledge_base
- `GET  /research/deep/sessions` – alle Recherche-Sessions

**`services/deep_research.py`** — Research Engine:
- Web-Suche via Tavily API (primär) oder DuckDuckGo (Fallback, kostenlos)
- Offline-Guard: `is_offline()` → sofortiger Abbruch
- Deduplication: URL-Hashing vor Ingest
- Rate-Limiting: max. 10 Queries/Minute, konfigurierbares Limit
- Quellenqualität-Scoring (Domain-Reputation, Aktualität)
- Ergebnis-Typen: web_page, news_article, academic, wiki

**`services/research_ingest.py`** — RAG-Integration:
- Chunking + Embedding → `knowledge_base` Collection in Qdrant
- Metadaten: `source_type=deep_research`, `session_id`, `query`, `retrieved_at`
- Deduplizierung mit bestehenden KB-Einträgen (Hash-Vergleich)
- `research_quality_score` als Qdrant-Payload für RAG-Gewichtung

**Generator-Integration:**
- `deep_research=true` Flag in `LiveGenerationRequest`
- Vor Generierung: relevante Research-Sessions in RAG-Kontext laden
- `sources` im Slide-Dict enthält Research-Quellen

### ENV
```
TAVILY_API_KEY=tvly-...       # optional, Fallback: DuckDuckGo
RESEARCH_MAX_QUERIES=10       # Rate-Limit pro Session
RESEARCH_MAX_RESULTS=20       # Max. Ergebnisse pro Query
RESEARCH_AUTO_INGEST=true     # Automatisch in KB indexieren
```

---

## Sprint 6 – Frontend: Chat + Data Import (→ v3.58.0)

**Ziel:** Die in Sprint 3 implementierten Backend-Features im Frontend nutzbar machen.

### Chat-Sidebar im Editor
- Chat-Panel rechts neben dem Slide-Editor
- Multi-Turn Verlauf mit Scroll
- Streaming-Anzeige (Token für Token)
- Thumbs up/down pro Antwort
- Kontext: aktueller Slide wird mitgeschickt

### Data Import UI
- Upload-Bereich für CSV/XLSX auf der Dashboard-Seite
- Spalten-Auswahl nach Upload (Dropdown)
- Chart-Vorschau (PNG) bevor Export
- "Als Slide hinzufügen"-Button → fügt Chart-Slide zur Session

### Bildbibliothek UI
- Neue Seite `/images` mit Grid-Ansicht
- Upload mit Drag & Drop
- Tags + Kunde + Thema bearbeiten
- Bild löschen
- Vorschau des Auto-Taggings

### Offline-Toggle
- Im Dashboard-Header: Status-Badge (Online/Offline)
- Klick → Toggle (POST /offline/enable|disable)
- Health-Check-Popup bei Hover

---

## Sprint 7 – Deep Research Frontend (→ v3.59.0)

**Ziel:** Deep Research bekommt einen eigenen Menüpunkt mit vollständiger UI.

### Neuer Menüpunkt "Research" im Sidebar

**Research-Übersicht (`/research`):**
- Alle bisherigen Research-Sessions
- Status: laufend / abgeschlossen / fehlgeschlagen
- Ergebnis-Vorschau (Top-Quellen, Zusammenfassung)
- "In Präsentation verwenden"-Button

**Research starten:**
- Formular: Topic, Tiefe (quick/standard/deep), Sprache
- Queries vorschlagen (LLM generiert Suchanfragen)
- Start → Weiterleitung zur Live-Ansicht

**Live-Fortschrittsansicht (`/research/{session_id}`):**
- Live-Feed: jede gefundene Quelle erscheint sofort (SSE)
- Quellen-Karten mit: Titel, URL, Snippet, Qualitäts-Score
- Fortschrittsbalken (x von y Queries fertig)
- "Abbrechen"-Button
- Automatisches Ingest wenn fertig (mit Toggle)

**Pipeline-Integration:**
- Beim Starten einer neuen Präsentation: "Research verwenden"-Toggle
- Zeigt verfügbare Research-Sessions zum Thema
- Ausgewählte Sessions fließen in RAG-Kontext der Generierung

### Porter's Five Forces Frontend
- Neues Tab in Strategy-Bereich
- Radar-Chart der 5 Kräfte (D3.js oder Recharts)
- Textfelder für jede Kraft editierbar

---

## Sprint 8 – Tests + Custom Templates + Landing Page (→ v3.60.0)

**Ziel:** Produktionsreife, Dokumentation, öffentliche Präsenz.

### Tests
- `tests/test_strategy_api.py` – SWOT, Porter Endpoints
- `tests/test_competitor_api.py` – Matrix, Profile
- `tests/test_data_import.py` – CSV/XLSX Parsing, Chart
- `tests/test_chat_api.py` – Session, Multi-Turn, Streaming
- `tests/test_offline.py` – Guards, Toggle
- `tests/test_pptx_designer.py` – alle 8 Layout-Typen
- GitHub Actions CI: automatisch bei Push auf staging

### Custom Templates
- Upload `.pptx` als Basis-Template
- Template-Manager: Liste, Vorschau, löschen
- Generator nutzt Template-Farben + Master-Layouts

### Landing Page (GitHub Pages)
- `docs/index.html` – statische Landing Page
- Features, Screenshots, Installation
- GitHub Pages aktiviert auf `main`

---

## Grundsätze (unverändert)

- **Backend first**: Jede Funktion via API testbar bevor Frontend
- **Kein Fake-Data**: Stubs klar als solche markiert
- **Offline-sicher**: Jeder externe Call hinter `is_offline()` Guard
- **RAG überall**: Neue Funktionen nutzen Kontext aus Wissensdatenbank
- **Self-Learning**: Jeder Export + jede Research-Session → Qdrant
- **Privacy-first**: Keine Daten verlassen die Maschine ohne explizite Konfiguration
