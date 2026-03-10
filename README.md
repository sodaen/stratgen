# STRATGEN - AI-Powered Presentation Generator

**STRATGEN** generates professional business presentations using AI. It combines intelligent content generation with corporate design templates to create ready-to-use PowerPoint decks.

## ✨ Features

- 🤖 **AI-Powered Content** - Uses local LLMs (Ollama) or cloud APIs
- 📊 **Knowledge Base** - RAG system with Qdrant for company-specific content
- 🎨 **Corporate Design** - Customizable PPTX templates with brand colors
- 🖼️ **Auto Images** - Automatic image selection from Unsplash
- 🔍 **Deep Research** - Web research integration for current data
- 📈 **Multi-Chapter** - Structured presentations with chapters, agenda, sources
- 🇩🇪 **German Language** - Optimized for German business presentations

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node.js 18+, Redis, Qdrant, Ollama

### Installation
```bash
git clone https://github.com/danielploetz-glitch/stratgen.git
cd stratgen
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
cp .env.example /etc/stratgen.env
./start.sh
```

## 📝 License
**AGPL-3.0** - Commercial use requires explicit permission.

## 👤 Author
**Daniel Plötz** - [@danielploetz-glitch](https://github.com/danielploetz-glitch)
