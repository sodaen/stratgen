# STRATGEN - Lokaler KI-Agent für Präsentationen

<p align="center">
  <strong>🔒 Datenschutz-First • 💻 100% Lokal • 🚧 Aktive Entwicklung</strong>
</p>

<p align="center">
  <a href="README.md">🇬🇧 English Version</a>
</p>

---

## 🎯 Was ist STRATGEN?

**STRATGEN** ist ein **lokal betriebener KI-Agent**, der automatisch professionelle Business-Präsentationen erstellt.

**Kernprinzip: Deine Daten bleiben auf DEINEN Servern.**

- ✅ **100% Lokale Verarbeitung** - LLM läuft auf deiner Hardware (Ollama)
- ✅ **Deine Daten, deine Kontrolle** - Wissensbasis lokal gespeichert
- ✅ **Keine Cloud-Abhängigkeit** - Funktioniert komplett offline
- ✅ **DSGVO-Konform** - Keine Daten verlassen deine Infrastruktur
- ✅ **Self-Hosted** - Volle Kontrolle über deine Installation

### Architektur
```
┌─────────────────────────────────────────────────────────────┐
│                    DEINE INFRASTRUKTUR                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Ollama    │  │   Qdrant    │  │     STRATGEN        │  │
│  │ Lokales LLM │  │ Vektor-DB   │  │   Präsentations-    │  │
│  │  (Mistral)  │  │  (Lokal)    │  │      Engine         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                    │              │
│         └────────────────┴────────────────────┘              │
│                  Alle Daten bleiben hier                     │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Nur Optional:    │
                    │  • Web-Recherche  │
                    │  • Bildersuche    │
                    │ (abschaltbar)     │
                    └───────────────────┘
```

### Vision

STRATGEN entwickelt sich zu einem **umfassenden KI-Strategie-Agenten**:
```
Heute:     Präsentations-Generator (Lokales LLM + RAG)
           ↓
Nächster:  Strategie-Assistent mit Recherche & Analyse
           ↓  
Ziel:      Autonomer Beratungs-Agent für Unternehmensstrategie
```

---

## 🚀 Projektstatus

Dieses Projekt wird **aktiv entwickelt**. Beiträge sind willkommen!

### ✅ Bereits verfügbar (v3.55)

| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **Deck-Generierung** | Vollständige PPTX mit Kapiteln, Agenda, Quellen | ✅ Stabil |
| **Lokale Wissensbasis** | RAG-System mit Qdrant (läuft lokal) | ✅ Stabil |
| **Lokales LLM** | Ollama-Integration (Mistral, Llama, etc.) | ✅ Stabil |
| **Deutsche Sprache** | Optimiert für deutsche Business-Präsentationen | ✅ Stabil |
| **Template-System** | Anpassbare PPTX-Vorlagen | ✅ Stabil |
| **Quellen-Management** | Automatische Quellenangaben mit URLs | ✅ Stabil |
| **Web-Interface** | React-Frontend | ✅ Stabil |
| **REST-API** | Für Integration | ✅ Stabil |

### 🔨 In Entwicklung

| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **Deep Research** | Optionale Web-Recherche (abschaltbar) | 🔨 In Arbeit |
| **Auto-Bilder** | Lokale Bildbibliothek-Unterstützung | 🔨 In Arbeit |
| **Layout-Optimierung** | Bessere Slide-Layouts | 🔨 In Arbeit |

### 📋 Roadmap

| Feature | Beschreibung | Priorität |
|---------|--------------|-----------|
| **Strategie-Analyse** | SWOT, Porter's Five Forces, etc. | 🔴 Hoch |
| **Wettbewerbs-Recherche** | Automatische Analyse | 🔴 Hoch |
| **Daten-Import** | Excel/CSV für Diagramme | 🟡 Mittel |
| **Interaktiver Modus** | Chat-basierte Verfeinerung | 🟡 Mittel |
| **Offline-Bilder** | Lokale Bilddatenbank | 🟡 Mittel |
| **Vollständiger Offline-Modus** | Null externe Verbindungen | 🟢 Geplant |

---

## ✨ Features im Detail

### 🔒 Datenschutz-First Design
- **Lokales LLM**: Alle KI-Verarbeitung auf deiner Hardware
- **Lokale Vektor-DB**: Wissensbasis verlässt nie deinen Server
- **Keine Telemetrie**: Null Datensammlung
- **Air-Gap fähig**: Kann ohne Internet laufen

### 🤖 KI-gestützte Inhalte
- Automatische Gliederung basierend auf Thema und Branche
- Kapitelstruktur mit Executive Summary
- Bullet Points, Analysen, Handlungsempfehlungen

### 📊 Lokale Wissensbasis (RAG)
- Upload von Firmendokumenten (PDF, DOCX, TXT)
- Vektorsuche mit Qdrant (lokal)
- Automatische Integration in Präsentationen

### 🎨 Corporate Design
- Anpassbare PPTX-Templates
- Firmenfarben, Logos, Schriftarten
- Konsistentes Layout über alle Slides

---

## 🚀 Schnellstart

### Voraussetzungen

- Python 3.11+
- Node.js 18+
- Docker (für Redis, Qdrant - alles lokal)
- Ollama (lokale LLM-Runtime)
- **Keine Cloud-Accounts erforderlich!**

### Installation
```bash
# Repository klonen
git clone https://github.com/sodaen/stratgen.git
cd stratgen

# Virtual Environment
python -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Lokale Services starten
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
docker run -d --name redis -p 6379:6379 redis

# Lokales LLM starten
ollama serve &
ollama pull mistral  # oder llama2, codellama, etc.

# Konfiguration
cp .env.example /etc/stratgen.env
# Einstellungen anpassen (standardmäßig alles lokal)

# STRATGEN starten
./start.sh
```

### Zugriff

- **Web-Interface**: http://localhost:3000
- **API**: http://localhost:8011
- **API-Docs**: http://localhost:8011/docs

---

## 🤝 Beitragen

Beiträge sind sehr willkommen!

1. **Fork** das Repository
2. **Branch erstellen** (`git checkout -b feature/TollesFeature`)
3. **Commit** (`git commit -m 'Füge TollesFeature hinzu'`)
4. **Push** (`git push origin feature/TollesFeature`)
5. **Pull Request** öffnen

Alle Beiträge müssen AGPL-3.0 lizenziert sein.

---

## 📁 Projektstruktur
```
stratgen/
├── backend/              # FastAPI Routes & API
├── frontend/             # React Web-Interface
├── services/             # Kern-Logik
│   ├── intelligent_deck_generator.py   # Haupt-Engine
│   ├── pptx_designer_v3.py            # PowerPoint Builder
│   └── knowledge.py                    # RAG & Vektorsuche
├── workers/              # Celery Background Tasks
├── templates/pptx/       # PowerPoint Vorlagen
└── data/                 # Laufzeit-Daten (lokal, gitignored)
```

---

## 📝 Lizenz

**Dual Licensing:**

| Option | Für wen | Bedingung |
|--------|---------|-----------|
| **AGPL-3.0** | Open Source, persönliche Nutzung | Änderungen müssen veröffentlicht werden |
| **Kommerziell** | Unternehmen, Closed-Source | Lizenz erforderlich |

Siehe [LICENSE](LICENSE) für Details.

---

## 👤 Autor

**SODAEN**

- GitHub: [@sodaen](https://github.com/sodaen)

---

<p align="center">
  <strong>⭐ Gib dem Repo einen Stern wenn es dir gefällt!</strong><br>
  🔒 Local-First • 🇩🇪 Made in Germany
</p>
