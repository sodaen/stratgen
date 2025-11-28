# StratGen

> KI-gestützter Strategie-Präsentationsgenerator für Agenturen, Freelancer und Konzerne

## 🎯 Was ist StratGen?

StratGen ist ein lokaler KI-Agent, der professionelle Strategie-Präsentationen automatisch generiert. Das System kombiniert:

- **RAG (Retrieval-Augmented Generation)** – Nutzt deine eigenen Dokumente als Wissensbasis
- **Lokale LLMs** – Läuft komplett offline mit Ollama (Mistral, Llama, etc.)
- **Strukturierte Ausgabe** – Generiert echte PPTX-Dateien mit Slides, Bullets, Notes

## 🏗️ Architektur

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (soon)                        │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ Agent   │ │ Content │ │ Knowledge│ │ Export  │            │
│  │ Router  │ │ Router  │ │ Router  │ │ Router  │            │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
└──────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Ollama    │     │    Qdrant    │     │   Services   │
│  (Local LLM) │     │ (Vector DB)  │     │  (Generator) │
└──────────────┘     └──────────────┘     └──────────────┘
```

## 🚀 Schnellstart

### Voraussetzungen

- Python 3.11+
- [Ollama](https://ollama.ai/) installiert
- Optional: [Qdrant](https://qdrant.tech/) für RAG

### Installation

```bash
# Repository klonen
git clone git@github.com:YOUR-USERNAME/stratgen.git
cd stratgen

# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env bearbeiten (OLLAMA_HOST etc.)

# Ollama starten & Modell laden
ollama pull mistral

# Server starten
uvicorn backend.api:app --host 0.0.0.0 --port 8011 --reload
```

### Ersten Agent-Run starten

```bash
# Präsentation generieren
curl -X POST http://localhost:8011/agent/run_v2 \
  -H "Content-Type: application/json" \
  -d '{"topic": "KI-Strategie für Mittelstand", "k": 3}'

# Ergebnis: {"ok": true, "project_id": "proj-123", "pptx_url": "/exports/download/..."}
```

## 📁 Projektstruktur

```
stratgen/
├── backend/           # FastAPI API-Router
│   ├── api.py         # Haupt-App mit Auto-Discovery
│   ├── agent_*.py     # Agent-Orchestrierung
│   ├── content_api.py # Content-Generierung
│   ├── knowledge_api.py # RAG-Suche
│   └── pptx_api.py    # PPTX-Export
├── services/          # Business Logic
│   ├── generator.py   # Slide-Plan-Generierung
│   ├── llm.py         # LLM-Abstraktion
│   ├── rag_pipeline.py # Vector-Suche
│   └── providers/     # Externe APIs (optional)
├── scripts/           # Utilities & Tests
├── data/              # Lokale Daten (gitignored)
└── static/            # Statische Assets
```

## 🔒 Datenschutz

StratGen ist für **maximalen Datenschutz** konzipiert:

- ✅ **Komplett lokal** – Keine Cloud-Abhängigkeiten erforderlich
- ✅ **Eigene LLMs** – Ollama läuft auf deinem Server
- ✅ **Eigene Vektor-DB** – Qdrant speichert lokal
- ✅ **Optionale APIs** – Statista/Brandwatch nur wenn gewünscht

## 🛠️ Konfiguration

Siehe `.env.example` für alle Optionen. Die wichtigsten:

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `LLM_PROVIDER` | `ollama`, `anthropic`, `openai` | `ollama` |
| `OLLAMA_HOST` | Ollama-Server URL | `http://127.0.0.1:11434` |
| `LLM_MODEL` | Modellname | `mistral` |
| `QDRANT_URL` | Qdrant-Server URL | `http://127.0.0.1:6333` |

## 📚 API-Dokumentation

Nach dem Start verfügbar unter:
- Swagger UI: http://localhost:8011/docs
- ReDoc: http://localhost:8011/redoc
- OpenAPI JSON: http://localhost:8011/openapi.json

### Wichtige Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/agent/run_v2` | POST | Vollständiger Agent-Run |
| `/content/preview` | GET | Content-Vorschau generieren |
| `/knowledge/search_semantic` | GET | Semantische Suche |
| `/projects/{id}` | GET | Projekt abrufen |
| `/pptx/render_from_project/{id}` | POST | PPTX generieren |
| `/health` | GET | Health-Check |

## 🧪 Tests

```bash
# Smoke-Test (alle Endpoints)
./scripts/smoke_agent.sh

# Einzelner Test
curl http://localhost:8011/health
```

## 🗺️ Roadmap

- [x] MVP: Agent-Pipeline mit PPTX-Export
- [x] RAG: Semantische Suche über lokale Dokumente
- [ ] Frontend: React/Next.js Briefing-Wizard
- [ ] Templates: Professionelle PPTX-Vorlagen
- [ ] Charts: Automatische Diagramm-Generierung
- [ ] Multi-Tenant: Organisationen & Benutzer

## 📄 Lizenz

Proprietär – Alle Rechte vorbehalten.

## 🤝 Beitragen

Dieses Projekt wird aktiv entwickelt. Bei Fragen oder Vorschlägen: Issue erstellen.
