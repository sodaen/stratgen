# STRATGEN – Release Notes

<!-- 
HINWEIS FÜR MAINTAINER:
Neue Einträge immer OBEN einfügen.
Format: ## [vX.Y.Z] – YYYY-MM-DD
Kategorien: Added | Changed | Fixed | Removed | Security
-->

---

## [v3.56.0] – 2026-03-11

### Added
- **Sprint 1 – Echte LLM-Integration**
  - `POST /strategy/swot` – SWOT-Analyse via Ollama/OpenAI + RAG-Kontext
  - `POST /strategy/porter` – Porter's Five Forces mit Scoring 1–10
  - `POST /strategy/gen` – Vollständige Strategiepräsentation (8/14/22 Slides)
  - `POST /competitors/matrix` – LLM-Scoring statt Fake-Symbolen
  - `POST /competitors/profile` – Deep-Dive Wettbewerberprofil
  - Self-Learning: `on_export_complete()` indexiert jeden PPTX-Export in Qdrant
  - Export-Hook in `api_export_bridge.py` nach jedem PPTX-Write

- **Sprint 2 – Auto Images + Layout-Optimierung**
  - `resolve_for_slide()` bei jedem PPTX-Export automatisch aufgerufen
  - Auto-Tagging beim Bild-Upload (Dateiname → Keywords)
  - 8 neue Slide-Layout-Typen: Agenda, CTA, KPI, SWOT, Timeline, Image, Comparison, Statement

- **Sprint 3 – Data Import + Chat**
  - `POST /data-import/upload` – CSV/XLSX hochladen, Spalten automatisch erkennen
  - `POST /data-import/chart` – matplotlib-Chart generieren (bar/line/pie)
  - `POST /data-import/to-slide` – One-Shot: Datei → fertiger Slide-Dict
  - `POST /chat/{id}/message` – Multi-Turn Chat mit RAG-Kontext
  - `POST /chat/{id}/message/stream` – SSE Token-Streaming
  - `POST /chat/{id}/feedback` – Feedback → Self-Learning
  - `scripts/deploy_wait.sh` – Wartet nach Restart bis Backend bereit

- **Sprint 4 – Offline Mode**
  - `services/offline.py` – Zentrales Modul: `is_offline()`, `guard()` Decorator
  - `POST /offline/enable|disable` – Runtime-Toggle ohne Neustart
  - `GET /offline/health` – Live-Ping aller externen Services
  - Offline-Guards in `data_services`, `strategy_api`, `competitor_api`, `chat_api`

### Fixed
- `_hex_to_rgb` Bug: G-Kanal war doppelt → alle PPTX-Farben falsch
- `get_embedding()` IndentationError in `self_learning.py`
- World Bank API: TTL-Cache verhindert 8.640 HTTP-Calls/Tag bei Status-Polls
- Pipeline-Polling: adaptiv 1s (aktiv) / 5s (idle) statt immer 1s

### Changed
- `enable_images=True` in allen Export-Pfaden (vorher überall `False`)
- `images/library/`, `data/imports/`, `data/chats/` in `.gitignore` aufgenommen

---

## [v3.55.3] – 2026-03-10

### Added
- Open Source Release (AGPL-3.0 + Commercial Dual License)
- Lokale LLM-Integration via Ollama
- Qdrant RAG-Pipeline
- PPTX-Generierung mit python-pptx
- React Frontend (Vite)
- Celery Task Queue
- Knowledge Base mit semantischer Suche

---

<!--
SPRINT-ROADMAP (kommende Releases):

v3.57.0 – Sprint 5: Deep Research Backend
  - deep_research_api.py: Web-Suche → Qdrant-Ingest Pipeline
  - ResearchSession: Fortschritt tracken (SSE)
  - Tavily/Brave/Serper Integration (optional, OFFLINE-sicher)
  - research_results → knowledge_base Collection
  - deep_research=true Flag im Generator

v3.58.0 – Sprint 6: Frontend Chat + Data Import
  - Chat-Sidebar im PPTX-Editor
  - Data-Import Upload + Chart-Vorschau
  - Bildbibliothek-Verwaltung UI
  - Offline-Toggle im Dashboard

v3.59.0 – Sprint 7: Frontend Deep Research
  - Eigener Menüpunkt "Research"
  - Visueller Fortschritt (Quellen live anzeigen)
  - Ergebnisse in Pipeline einbinden
  - Porter's Five Forces Frontend

v3.60.0 – Sprint 8: Tests + Custom Templates
  - pytest-Suite (Backend + Integration)
  - Custom .pptx Template Support
  - API-Dokumentation
  - Landing Page (GitHub Pages)
-->
