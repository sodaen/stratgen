# STRATGEN

**Local-First AI Agent for Professional Business Presentations**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![License: Commercial](https://img.shields.io/badge/License-Commercial-green.svg)](LICENSE_COMMERCIAL)
[![Version](https://img.shields.io/badge/version-3.56.0-blue)](https://github.com/sodaen/stratgen/releases)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)

STRATGEN is a privacy-first, local AI agent that automatically generates professional PowerPoint strategy presentations. All processing happens on your machine — no cloud, no data sharing.

---

## Features

### ✅ Implemented (v3.56.0)

| Feature | Status | Details |
|---------|--------|---------|
| **Strategy Analysis** | ✅ Live | SWOT, Porter's Five Forces via LLM + RAG |
| **Competitor Research** | ✅ Live | LLM scoring 1–10, deep-dive profiles |
| **PPTX Generation** | ✅ Live | 8–22 slides, 8 layout types, auto images |
| **Auto Images** | ✅ Live | resolve_for_slide(), auto-tagging on upload |
| **Data Import** | ✅ Live | CSV/XLSX → matplotlib chart → slide |
| **Interactive Chat** | ✅ Live | Multi-turn RAG chat, SSE streaming, feedback |
| **Self-Learning** | ✅ Live | Every export indexed in Qdrant automatically |
| **Offline Mode** | ✅ Live | `STRATGEN_OFFLINE=true` blocks all external calls |
| **Knowledge Base** | ✅ Live | Qdrant vector DB, semantic search, RAG |

### 🔜 Planned

| Feature | Sprint | Details |
|---------|--------|---------|
| **Deep Research** | Sprint 5 | Web search → RAG pipeline, visual progress UI |
| **Frontend: Chat** | Sprint 6 | Chat sidebar in editor |
| **Frontend: Data Import** | Sprint 6 | Upload + chart preview |
| **Frontend: Deep Research** | Sprint 7 | Dedicated menu, live progress |
| **Custom Templates** | Sprint 7 | Custom .pptx template support |
| **Tests + Docs** | Sprint 8 | pytest suite, API docs |

---

## Stack

- **Backend**: FastAPI (80+ endpoints, auto-discover routers)
- **LLM**: Ollama (local) · OpenAI · Anthropic — switchable via ENV
- **Vector DB**: Qdrant (local)
- **Embeddings**: sentence-transformers (local)
- **Presentation**: python-pptx
- **Charts**: matplotlib
- **Frontend**: React + Vite
- **Task Queue**: Celery + Redis
- **Storage**: SQLite + JSON + local filesystem

---

## Quick Start

### Requirements

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai) with `mistral` model
- [Qdrant](https://qdrant.tech) running locally

### Installation

```bash
git clone https://github.com/sodaen/stratgen.git
cd stratgen

# Python backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && npm run build && cd ..

# Environment
cp .env.example .env
# Edit .env: set LLM_MODEL, QDRANT_URL etc.

# Start
sudo systemctl start stratgen
# or:
gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.api:app --bind 127.0.0.1:8011
```

### After Restart

```bash
# Wait for backend to be ready:
bash scripts/deploy_wait.sh
```

---

## Environment Variables

```bash
# LLM Provider (ollama | openai | anthropic)
LLM_PROVIDER=ollama
LLM_MODEL=mistral
OLLAMA_HOST=http://127.0.0.1:11434

# Offline Mode — blocks all external HTTP calls
STRATGEN_OFFLINE=false

# Qdrant
QDRANT_URL=http://127.0.0.1:6333

# Optional: OpenAI fallback
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
```

---

## Key API Endpoints

```
POST /strategy/swot          SWOT analysis via LLM + RAG
POST /strategy/porter        Porter's Five Forces
POST /strategy/gen           Full strategy presentation

POST /competitors/matrix     Competitor matrix LLM scoring
POST /competitors/profile    Deep-dive competitor profile

POST /data-import/upload     CSV/XLSX → column detection
POST /data-import/chart      → matplotlib chart
POST /data-import/to-slide   One-shot: file → slide dict

POST /chat/{id}/message      Multi-turn RAG chat
POST /chat/{id}/message/stream  SSE token streaming
POST /chat/{id}/feedback     Thumbs up/down → self-learning

POST /images/upload          Upload image to library
GET  /images/resolve         Find best image for slide

GET  /offline/status         Current offline mode status
POST /offline/enable         Enable offline mode (no restart)
GET  /offline/health         Live ping all external services

GET  /learning/stats         Self-learning statistics
```

Full API docs: `http://localhost:8011/docs`

---

## Architecture

```
frontend/          React + Vite (port 3000)
backend/           FastAPI routers (auto-discovered *_api.py)
services/          Business logic
  offline.py       Central offline mode control
  pptx_designer_v2.py  PPTX generation (8 layout types)
  image_store.py   Image library with auto-tagging
  self_learning.py Export → Qdrant indexing
  chat_learner.py  Chat feedback → RAG
data/
  strategies/      Saved strategy analyses
  competitors/     Saved competitor analyses
  imports/         CSV/XLSX imports
  chats/           Chat sessions
  exports/         Generated PPTX files
images/library/    Uploaded images (gitignored)
```

---

## License

Dual License:

- **AGPL-3.0** — for open source projects ([LICENSE](LICENSE))
- **Commercial** — for proprietary/SaaS use ([LICENSE_COMMERCIAL](LICENSE_COMMERCIAL))

© SODAEN 2024–2026

---

## Changelog

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for version history.
