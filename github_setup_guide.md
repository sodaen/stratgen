# StratGen → GitHub: Vollständige Setup-Anleitung

## Übersicht

Diese Anleitung bringt dein StratGen-Projekt auf GitHub und richtet einen Workflow ein, mit dem wir effizient zusammenarbeiten können.

---

## Teil 1: GitHub-Repository erstellen

### 1.1 Auf GitHub (im Browser)

1. Gehe zu: https://github.com/new
2. Fülle aus:
   - **Repository name:** `stratgen`
   - **Description:** `KI-gestützter Strategie-Präsentationsgenerator`
   - **Visibility:** `Private` ✅
   - **Initialize:** NICHTS auswählen (kein README, keine .gitignore)
3. Klick: **Create repository**
4. Kopiere die URL (sollte so aussehen): `git@github.com:DEIN-USERNAME/stratgen.git`

---

## Teil 2: Lokales System vorbereiten

### 2.1 Git installieren (falls nicht vorhanden)

```bash
# Prüfen ob Git installiert ist
git --version

# Falls nicht installiert:
sudo apt update && sudo apt install git -y
```

### 2.2 Git konfigurieren

```bash
# Deine Identität setzen (wichtig für Commits)
git config --global user.name "Dein Name"
git config --global user.email "deine-email@example.com"

# Empfohlene Einstellungen
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.autocrlf input
```

### 2.3 SSH-Key für GitHub einrichten

```bash
# 1. Prüfen ob bereits ein Key existiert
ls -la ~/.ssh/

# 2. Falls nicht, neuen Key erstellen
ssh-keygen -t ed25519 -C "deine-email@example.com"
# → Enter drücken für Standardpfad
# → Passwort optional (Enter für keins)

# 3. SSH-Agent starten und Key hinzufügen
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 4. Public Key kopieren
cat ~/.ssh/id_ed25519.pub
# → Diesen Text kopieren!
```

### 2.4 SSH-Key zu GitHub hinzufügen

1. Gehe zu: https://github.com/settings/keys
2. Klick: **New SSH key**
3. **Title:** `Ubuntu StratGen Server`
4. **Key:** Den kopierten Public Key einfügen
5. Klick: **Add SSH key**

### 2.5 Verbindung testen

```bash
ssh -T git@github.com
# Erwartete Antwort: "Hi USERNAME! You've successfully authenticated..."
```

---

## Teil 3: StratGen-Projekt vorbereiten

### 3.1 In dein Projektverzeichnis wechseln

```bash
# Anpassen an deinen tatsächlichen Pfad!
cd /pfad/zu/stratgen
```

### 3.2 .gitignore erstellen

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
.eggs/
dist/
build/
*.egg
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Backup-Dateien (davon hast du viele!)
*.bak
*.bak.*
*.broken.*
*.userbak.*
*.autofix.*
*.SAFE.*
*.disabled

# Umgebung & Secrets
.env
.env.local
.env.*.local
*.pem
*.key
secrets/

# Daten (lokal behalten, nicht committen)
data/
!data/.gitkeep
static/images/
!static/images/.gitkeep

# Exports (generierte Dateien)
*.pptx
*.pdf
exports/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Temporäre Dateien
tmp/
temp/
*.tmp
EOF
```

### 3.3 Leere Ordner-Platzhalter erstellen

```bash
# Git trackt keine leeren Ordner, daher .gitkeep Dateien
mkdir -p data static/images
touch data/.gitkeep static/images/.gitkeep
```

### 3.4 Backup-Dateien aufräumen (optional aber empfohlen)

```bash
# Zeige alle Backup-Dateien
find . -name "*.bak*" -o -name "*.broken.*" | head -20

# Backup-Dateien in separaten Ordner verschieben (nicht löschen!)
mkdir -p _backups
find . -name "*.bak*" -exec mv {} _backups/ \;
find . -name "*.broken.*" -exec mv {} _backups/ \;
find . -name "*.userbak.*" -exec mv {} _backups/ \;

# _backups wird durch .gitignore ignoriert
echo "_backups/" >> .gitignore
```

---

## Teil 4: Git-Repository initialisieren & pushen

### 4.1 Repository initialisieren

```bash
# Im Projektverzeichnis
cd /pfad/zu/stratgen

# Git initialisieren
git init

# Remote hinzufügen (DEIN-USERNAME ersetzen!)
git remote add origin git@github.com:DEIN-USERNAME/stratgen.git
```

### 4.2 Ersten Commit erstellen

```bash
# Alle Dateien zur Staging Area hinzufügen
git add .

# Status prüfen (sollte viele Dateien zeigen)
git status

# Ersten Commit erstellen
git commit -m "Initial commit: StratGen MVP

- FastAPI Backend mit Auto-Discovery
- RAG Pipeline (SBERT + Qdrant)
- Agent Orchestration (v1, v2)
- PPTX Export
- Services Layer (Generator, NLG, Providers)
- Knowledge Management
"
```

### 4.3 Zu GitHub pushen

```bash
# Hauptbranch pushen
git push -u origin main

# Falls Fehler "src refspec main does not match any":
git branch -M main
git push -u origin main
```

---

## Teil 5: Zusammenarbeit mit Claude einrichten

### 5.1 So teilst du Code mit mir

**Option A: Einzelne Datei zeigen**
```bash
# Datei-Inhalt kopieren
cat backend/api.py
# → In Chat einfügen
```

**Option B: Diff zeigen (Änderungen seit letztem Commit)**
```bash
git diff backend/api.py
# → In Chat einfügen
```

**Option C: Komplettes Verzeichnis als Baum**
```bash
find backend -name "*.py" -not -name "*.bak*" | head -30
# → In Chat einfügen
```

### 5.2 So übernimmst du meine Änderungen

**Option A: Komplette Datei ersetzen**
```bash
# Ich gebe dir eine Datei, du speicherst sie:
cat > backend/neue_datei.py << 'EOF'
# ... mein Code ...
EOF
```

**Option B: Patch anwenden**
```bash
# Ich gebe dir einen Patch, du speicherst ihn:
cat > fix.patch << 'EOF'
... mein Patch ...
EOF

# Patch anwenden
git apply fix.patch
```

**Option C: Datei herunterladen**
- Ich stelle Dateien hier in `/mnt/user-data/outputs/` bereit
- Du lädst sie herunter und kopierst sie ins Projekt

### 5.3 Standard-Workflow für unsere Sessions

```
1. Du: "Ich möchte Feature X implementieren"
   → Zeigst mir relevante aktuelle Dateien

2. Ich: Analysiere und generiere Code
   → Gebe dir komplette Dateien oder Patches

3. Du: Übernimmst die Änderungen
   git add .
   git commit -m "Feature X: Beschreibung"
   git push

4. Du: Testest lokal
   ./scripts/smoke_agent.sh
   
5. Bei Problemen → Zeigst mir Fehler → Ich fixe
```

---

## Teil 6: Projekt-Struktur (Empfohlen)

Nach dem Aufräumen sollte dein Repo so aussehen:

```
stratgen/
├── .github/
│   └── workflows/         # CI/CD (später)
├── backend/
│   ├── __init__.py
│   ├── api.py             # Haupt-App
│   ├── *_api.py           # Router-Module
│   ├── middleware/
│   ├── routers/
│   └── schemas/
├── services/
│   ├── __init__.py
│   ├── generator.py       # Slide-Generierung
│   ├── llm.py             # LLM-Abstraktion
│   ├── rag_pipeline.py    # RAG
│   ├── nlg/               # NLG-Module
│   └── providers/         # Statista, etc.
├── scripts/
│   ├── smoke_agent.sh
│   └── ...
├── data/                  # .gitignore'd
│   └── .gitkeep
├── static/
│   └── images/
│       └── .gitkeep
├── systemd/               # Service-Configs
├── .env.example           # Template für Secrets
├── .gitignore
├── README.md
├── requirements.txt
└── pyproject.toml         # Optional: Poetry/PDM
```

---

## Teil 7: Umgebungsvariablen (Secrets)

### 7.1 .env.example erstellen (wird committed)

```bash
cat > .env.example << 'EOF'
# === StratGen Konfiguration ===

# App
APP_ENV=prod
LOG_LEVEL=info

# LLM (lokal mit Ollama)
LLM_PROVIDER=ollama
OLLAMA_HOST=http://127.0.0.1:11434
LLM_MODEL=mistral

# Vector DB
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=stratgen_docs

# Embeddings
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# === Optionale externe APIs ===
# (nur wenn du externe Datenquellen nutzen willst)

# STATISTA_API_KEY=
# BRANDWATCH_API_KEY=
# TALKWALKER_API_KEY=

# === Interne URLs ===
STRATGEN_INTERNAL_URL=http://127.0.0.1:8011
STRATGEN_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
```

### 7.2 Echte .env erstellen (wird NICHT committed)

```bash
cp .env.example .env
# Dann .env bearbeiten mit echten Werten
```

---

## Teil 8: Schnell-Check

Führe diese Befehle aus, um zu prüfen ob alles funktioniert:

```bash
# 1. Git-Status
git status
# → Sollte "nothing to commit, working tree clean" zeigen

# 2. Remote prüfen
git remote -v
# → Sollte origin mit github.com zeigen

# 3. Letzter Commit
git log --oneline -3

# 4. Auf GitHub prüfen
# → https://github.com/DEIN-USERNAME/stratgen
# → Sollte alle Dateien zeigen
```

---

## Nächste Schritte

Sobald dein Repo auf GitHub ist:

1. **Schick mir den Repository-Namen** (z.B. `meinuser/stratgen`)
2. **Zeig mir eine Datei** die du als erstes verbessern willst
3. Wir starten mit dem ersten Feature!

**Vorschläge für erste Verbesserungen:**
- [ ] Statista-API echte Implementation
- [ ] Claude/Anthropic als LLM-Provider
- [ ] Bessere PPTX-Templates
- [ ] Datei-Upload & automatische Erkennung

---

## Fehlerbehebung

### "Permission denied (publickey)"
```bash
# SSH-Key nochmal zum Agent hinzufügen
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### "remote origin already exists"
```bash
git remote remove origin
git remote add origin git@github.com:DEIN-USERNAME/stratgen.git
```

### "Updates were rejected"
```bash
# Falls GitHub schon Dateien hat (sollte nicht passieren)
git pull origin main --allow-unrelated-histories
git push origin main
```
