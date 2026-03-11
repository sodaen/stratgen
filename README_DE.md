# STRATGEN

**Lokaler KI-Agent für professionelle Business-Präsentationen**

[![License: AGPL-3.0](https://img.shields.io/badge/Lizenz-AGPL--3.0-blue.svg)](LICENSE)
[![License: Commercial](https://img.shields.io/badge/Lizenz-Kommerziell-green.svg)](LICENSE_COMMERCIAL)
[![Version](https://img.shields.io/badge/version-3.56.0-blue)](https://github.com/sodaen/stratgen/releases)

STRATGEN ist ein privacy-first, lokaler KI-Agent der automatisch professionelle PowerPoint-Strategiepräsentationen erstellt. Alle Berechnungen laufen auf deiner Maschine — kein Cloud, keine Datenweitergabe.

---

## Funktionen

### ✅ Implementiert (v3.56.0)

| Funktion | Status | Details |
|----------|--------|---------|
| **Strategieanalyse** | ✅ Live | SWOT, Porter's Five Forces via LLM + RAG |
| **Wettbewerbsanalyse** | ✅ Live | LLM-Scoring 1–10, Deep-Dive-Profile |
| **PPTX-Generierung** | ✅ Live | 8–22 Slides, 8 Layout-Typen, Auto-Bilder |
| **Auto Images** | ✅ Live | resolve_for_slide(), Auto-Tagging beim Upload |
| **Daten-Import** | ✅ Live | CSV/XLSX → matplotlib-Chart → Slide |
| **Interaktiver Chat** | ✅ Live | Multi-Turn RAG-Chat, SSE-Streaming, Feedback |
| **Self-Learning** | ✅ Live | Jeder Export wird automatisch in Qdrant indexiert |
| **Offline-Modus** | ✅ Live | `STRATGEN_OFFLINE=true` sperrt alle externen Calls |
| **Wissensdatenbank** | ✅ Live | Qdrant Vektor-DB, semantische Suche, RAG |

### 🔜 Geplant

| Funktion | Sprint | Details |
|----------|--------|---------|
| **Deep Research** | Sprint 5 | Web-Suche → RAG-Pipeline, visuelle Fortschrittsanzeige |
| **Frontend: Chat** | Sprint 6 | Chat-Sidebar im Editor |
| **Frontend: Daten-Import** | Sprint 6 | Upload + Chart-Vorschau |
| **Frontend: Deep Research** | Sprint 7 | Eigener Menüpunkt, Live-Fortschritt, Ergebnisansicht |
| **Custom Templates** | Sprint 7 | Eigene .pptx-Vorlagen |
| **Tests + Dokumentation** | Sprint 8 | pytest-Suite, API-Docs |

---

## Technologie-Stack

- **Backend**: FastAPI (80+ Endpunkte, Auto-Discovery für Router)
- **LLM**: Ollama (lokal) · OpenAI · Anthropic — per ENV wählbar
- **Vektor-DB**: Qdrant (lokal)
- **Embeddings**: sentence-transformers (lokal)
- **Präsentation**: python-pptx
- **Charts**: matplotlib
- **Frontend**: React + Vite
- **Task-Queue**: Celery + Redis
- **Speicher**: SQLite + JSON + lokales Dateisystem

---

## Schnellstart

### Voraussetzungen

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai) mit `mistral`-Modell
- [Qdrant](https://qdrant.tech) lokal laufend

### Installation

```bash
git clone https://github.com/sodaen/stratgen.git
cd stratgen

# Python-Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && npm run build && cd ..

# Umgebungsvariablen
cp .env.example .env
# .env bearbeiten: LLM_MODEL, QDRANT_URL etc. setzen

# Starten
sudo systemctl start stratgen
# oder:
gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.api:app --bind 127.0.0.1:8011
```

### Nach jedem Neustart

```bash
# Warten bis Backend bereit ist:
bash scripts/deploy_wait.sh
```

---

## Umgebungsvariablen

```bash
# LLM-Provider (ollama | openai | anthropic)
LLM_PROVIDER=ollama
LLM_MODEL=mistral
OLLAMA_HOST=http://127.0.0.1:11434

# Offline-Modus — sperrt alle externen HTTP-Calls
STRATGEN_OFFLINE=false

# Qdrant
QDRANT_URL=http://127.0.0.1:6333

# Optional: OpenAI-Fallback
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
```

---

## Wichtige API-Endpunkte

```
POST /strategy/swot          SWOT-Analyse via LLM + RAG
POST /strategy/porter        Porter's Five Forces
POST /strategy/gen           Vollständige Strategiepräsentation

POST /competitors/matrix     Wettbewerbsmatrix LLM-Scoring
POST /competitors/profile    Deep-Dive Wettbewerberprofil

POST /data-import/upload     CSV/XLSX → Spalten-Erkennung
POST /data-import/chart      → matplotlib-Chart
POST /data-import/to-slide   One-Shot: Datei → Slide-Dict

POST /chat/{id}/message      Multi-Turn RAG-Chat
POST /chat/{id}/message/stream  SSE Token-Streaming
POST /chat/{id}/feedback     Daumen hoch/runter → Self-Learning

POST /images/upload          Bild in Bibliothek hochladen
GET  /images/resolve         Bestes Bild für Slide finden

GET  /offline/status         Aktueller Offline-Modus Status
POST /offline/enable         Offline-Modus einschalten (kein Neustart)
GET  /offline/health         Live-Ping aller externen Services

GET  /learning/stats         Self-Learning Statistiken
```

Vollständige API-Docs: `http://localhost:8011/docs`

---

## Architektur

```
frontend/          React + Vite (Port 3000)
backend/           FastAPI Router (Auto-Discovery *_api.py)
services/          Business Logic
  offline.py       Zentrales Offline-Modus-Modul
  pptx_designer_v2.py  PPTX-Generierung (8 Layout-Typen)
  image_store.py   Bildbibliothek mit Auto-Tagging
  self_learning.py Export → Qdrant-Indexierung
  chat_learner.py  Chat-Feedback → RAG
data/
  strategies/      Gespeicherte Strategieanalysen
  competitors/     Gespeicherte Wettbewerbsanalysen
  imports/         CSV/XLSX Importe
  chats/           Chat-Sessions
  exports/         Generierte PPTX-Dateien
images/library/    Hochgeladene Bilder (gitignored)
```

---

## Lizenz

Dual-Lizenz:

- **AGPL-3.0** — für Open-Source-Projekte ([LICENSE](LICENSE))
- **Kommerziell** — für proprietäre/SaaS-Nutzung ([LICENSE_COMMERCIAL](LICENSE_COMMERCIAL))

© SODAEN 2024–2026

---

## Changelog

Siehe [RELEASE_NOTES.md](RELEASE_NOTES.md) für die Versionshistorie.
