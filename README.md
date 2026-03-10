# STRATGEN - Local-First AI Presentation Agent

<p align="center">
  <strong>🔒 Privacy-First • 💻 100% Local • 🚧 Active Development</strong>
</p>

<p align="center">
  <a href="README_DE.md">🇩🇪 Deutsche Version</a>
</p>

---

## 🎯 What is STRATGEN?

**STRATGEN** is a **local-first AI agent** that automatically creates professional business presentations. 

**Key Principle: Your data stays on YOUR servers.**

- ✅ **100% Local Processing** - LLM runs on your hardware (Ollama)
- ✅ **Your Data, Your Control** - Knowledge base stored locally
- ✅ **No Cloud Dependencies** - Works completely offline
- ✅ **GDPR Compliant** - No data leaves your infrastructure
- ✅ **Self-Hosted** - Full control over your installation

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR INFRASTRUCTURE                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Ollama    │  │   Qdrant    │  │     STRATGEN        │  │
│  │  Local LLM  │  │ Vector DB   │  │   Presentation      │  │
│  │  (Mistral)  │  │  (Local)    │  │      Engine         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                    │              │
│         └────────────────┴────────────────────┘              │
│                    All data stays here                       │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Optional Only:   │
                    │  • Web Research   │
                    │  • Image Search   │
                    │  (can be disabled)│
                    └───────────────────┘
```

### Vision

STRATGEN is evolving into a **comprehensive AI strategy agent**:
```
Today:     Presentation Generator (Local LLM + RAG)
           ↓
Next:      Strategy Assistant with Research & Analysis
           ↓  
Goal:      Autonomous Consulting Agent for Business Strategy
```

---

## 🚀 Project Status

This project is under **active development**. Contributions welcome!

### ✅ Available Now (v3.55)

| Feature | Description | Status |
|---------|-------------|--------|
| **Deck Generation** | Complete PPTX with chapters, agenda, sources | ✅ Stable |
| **Local Knowledge Base** | RAG system with Qdrant (runs locally) | ✅ Stable |
| **Local LLM** | Ollama integration (Mistral, Llama, etc.) | ✅ Stable |
| **German Language** | Optimized for German business presentations | ✅ Stable |
| **Template System** | Customizable PPTX templates | ✅ Stable |
| **Source Management** | Automatic citations with URLs | ✅ Stable |
| **Web Interface** | React frontend | ✅ Stable |
| **REST API** | For integration | ✅ Stable |

### 🔨 In Development

| Feature | Description | Status |
|---------|-------------|--------|
| **Deep Research** | Optional web research (can be disabled) | 🔨 WIP |
| **Auto Images** | Local image library support | 🔨 WIP |
| **Layout Optimization** | Better slide layouts | 🔨 WIP |

### 📋 Roadmap

| Feature | Description | Priority |
|---------|-------------|----------|
| **Strategy Analysis** | SWOT, Porter's Five Forces, etc. | 🔴 High |
| **Competitor Research** | Automated analysis | 🔴 High |
| **Data Import** | Excel/CSV for charts | 🟡 Medium |
| **Interactive Mode** | Chat-based refinement | 🟡 Medium |
| **Offline Images** | Local image database | 🟡 Medium |
| **Full Offline Mode** | Zero external connections | 🟢 Planned |

---

## ✨ Features

### 🔒 Privacy-First Design
- **Local LLM**: All AI processing on your hardware
- **Local Vector DB**: Knowledge base never leaves your server
- **No Telemetry**: Zero data collection
- **Air-Gap Ready**: Can run without internet

### 🤖 AI-Powered Content
- Automatic outline based on topic and industry
- Chapter structure with Executive Summary
- Bullet points, analyses, recommendations

### 📊 Local Knowledge Base (RAG)
- Upload company documents (PDF, DOCX, TXT)
- Vector search with Qdrant (local)
- Automatic integration into presentations

### 🎨 Corporate Design
- Customizable PPTX templates
- Company colors, logos, fonts
- Consistent layout across all slides

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for Redis, Qdrant - all local)
- Ollama (local LLM runtime)
- **No cloud accounts required!**

### Installation
```bash
# Clone repository
git clone https://github.com/sodaen/stratgen.git
cd stratgen

# Virtual Environment
python -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Start local services
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
docker run -d --name redis -p 6379:6379 redis

# Start local LLM
ollama serve &
ollama pull mistral  # or llama2, codellama, etc.

# Configuration
cp .env.example /etc/stratgen.env
# Edit settings (all local by default)

# Start STRATGEN
./start.sh
```

### Access

- **Web Interface**: http://localhost:3000
- **API**: http://localhost:8011
- **API Docs**: http://localhost:8011/docs

---

## 🤝 Contributing

Contributions are very welcome!

1. **Fork** the repository
2. **Create branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** (`git commit -m 'Add AmazingFeature'`)
4. **Push** (`git push origin feature/AmazingFeature`)
5. **Open Pull Request**

All contributions must be AGPL-3.0 licensed.

---

## 📁 Project Structure
```
stratgen/
├── backend/              # FastAPI Routes & API
├── frontend/             # React Web Interface
├── services/             # Core Logic
│   ├── intelligent_deck_generator.py   # Main Engine
│   ├── pptx_designer_v3.py            # PowerPoint Builder
│   └── knowledge.py                    # RAG & Vector Search
├── workers/              # Celery Background Tasks
├── templates/pptx/       # PowerPoint Templates
└── data/                 # Runtime Data (local, gitignored)
```

---

## 📝 License

**Dual Licensing:**

| Option | For | Condition |
|--------|-----|-----------|
| **AGPL-3.0** | Open Source, personal use | Modifications must be published |
| **Commercial** | Businesses, Closed-Source | License required |

See [LICENSE](LICENSE) for details.

---

## 👤 Author

**SODAEN**

- GitHub: [@sodaen](https://github.com/sodaen)

---

<p align="center">
  <strong>⭐ Star this repo if you find it useful!</strong><br>
  🔒 Local-First • 🇩🇪 Made in Germany
</p>
