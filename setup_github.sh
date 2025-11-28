#!/usr/bin/env bash
# =============================================
# StratGen → GitHub Setup Script
# =============================================
# Dieses Script bereitet dein StratGen-Projekt
# für GitHub vor und macht den ersten Push.
#
# Verwendung:
#   chmod +x setup_github.sh
#   ./setup_github.sh
# =============================================

set -euo pipefail

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     StratGen → GitHub Setup Script         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# 1. Prüfungen
# ============================================

echo -e "${YELLOW}[1/7] Prüfe Voraussetzungen...${NC}"

# Git installiert?
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git ist nicht installiert!${NC}"
    echo "   Installiere mit: sudo apt install git"
    exit 1
fi
echo -e "${GREEN}  ✓ Git gefunden: $(git --version)${NC}"

# Im richtigen Verzeichnis?
if [[ ! -f "backend/api.py" ]]; then
    echo -e "${RED}❌ Dieses Script muss im StratGen-Hauptverzeichnis ausgeführt werden!${NC}"
    echo "   Aktuelles Verzeichnis: $(pwd)"
    echo "   Erwartet: Ein Ordner mit backend/api.py"
    exit 1
fi
echo -e "${GREEN}  ✓ StratGen-Projekt gefunden${NC}"

# SSH-Key vorhanden?
if [[ ! -f ~/.ssh/id_ed25519 ]] && [[ ! -f ~/.ssh/id_rsa ]]; then
    echo -e "${YELLOW}  ⚠ Kein SSH-Key gefunden. Erstelle einen...${NC}"
    read -p "    Deine E-Mail für den SSH-Key: " email
    ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
    eval "$(ssh-agent -s)" > /dev/null
    ssh-add ~/.ssh/id_ed25519
    echo ""
    echo -e "${YELLOW}  ════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  WICHTIG: Füge diesen Public Key zu GitHub hinzu:${NC}"
    echo -e "${YELLOW}  https://github.com/settings/keys${NC}"
    echo -e "${YELLOW}  ════════════════════════════════════════════${NC}"
    echo ""
    cat ~/.ssh/id_ed25519.pub
    echo ""
    read -p "  Drücke Enter wenn der Key auf GitHub hinzugefügt wurde..."
else
    echo -e "${GREEN}  ✓ SSH-Key vorhanden${NC}"
fi

# ============================================
# 2. GitHub-Repository URL abfragen
# ============================================

echo ""
echo -e "${YELLOW}[2/7] GitHub-Repository konfigurieren...${NC}"
echo ""
echo "  Erstelle zuerst ein PRIVATES Repository auf GitHub:"
echo "  https://github.com/new"
echo ""
echo "  - Name: stratgen"
echo "  - Visibility: Private"
echo "  - KEINE Initialisierung (kein README, keine .gitignore)"
echo ""
read -p "  Dein GitHub-Username: " github_user

REPO_URL="git@github.com:${github_user}/stratgen.git"
echo -e "${GREEN}  → Repository-URL: ${REPO_URL}${NC}"

# ============================================
# 3. .gitignore erstellen
# ============================================

echo ""
echo -e "${YELLOW}[3/7] Erstelle .gitignore...${NC}"

cat > .gitignore << 'GITIGNORE'
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

# Backup-Dateien
*.bak
*.bak.*
*.broken.*
*.userbak.*
*.autofix.*
*.SAFE.*
*.disabled
_backups/

# Secrets
.env
.env.local
.env.*.local
*.pem
*.key
secrets/

# Daten (lokal)
data/
!data/.gitkeep
static/images/*
!static/images/.gitkeep
exports/
uploads/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Temp
tmp/
temp/
*.tmp
GITIGNORE

echo -e "${GREEN}  ✓ .gitignore erstellt${NC}"

# ============================================
# 4. Backup-Dateien verschieben
# ============================================

echo ""
echo -e "${YELLOW}[4/7] Räume Backup-Dateien auf...${NC}"

backup_count=$(find . -name "*.bak*" -o -name "*.broken.*" 2>/dev/null | wc -l)

if [[ $backup_count -gt 0 ]]; then
    mkdir -p _backups
    find . -name "*.bak*" -exec mv {} _backups/ \; 2>/dev/null || true
    find . -name "*.broken.*" -exec mv {} _backups/ \; 2>/dev/null || true
    find . -name "*.userbak.*" -exec mv {} _backups/ \; 2>/dev/null || true
    echo -e "${GREEN}  ✓ ${backup_count} Backup-Dateien nach _backups/ verschoben${NC}"
else
    echo -e "${GREEN}  ✓ Keine Backup-Dateien gefunden${NC}"
fi

# ============================================
# 5. Platzhalter-Dateien erstellen
# ============================================

echo ""
echo -e "${YELLOW}[5/7] Erstelle Platzhalter-Dateien...${NC}"

mkdir -p data static/images
touch data/.gitkeep static/images/.gitkeep

# .env.example erstellen falls nicht vorhanden
if [[ ! -f ".env.example" ]]; then
    cat > .env.example << 'ENVEXAMPLE'
# StratGen Konfiguration
APP_ENV=prod
LOG_LEVEL=info

# LLM (lokal)
LLM_PROVIDER=ollama
OLLAMA_HOST=http://127.0.0.1:11434
LLM_MODEL=mistral

# Vector DB
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=stratgen_docs

# Optional: Externe APIs
# STATISTA_API_KEY=
# BRANDWATCH_API_KEY=
# TALKWALKER_API_KEY=
ENVEXAMPLE
    echo -e "${GREEN}  ✓ .env.example erstellt${NC}"
fi

echo -e "${GREEN}  ✓ Platzhalter erstellt${NC}"

# ============================================
# 6. Git initialisieren
# ============================================

echo ""
echo -e "${YELLOW}[6/7] Initialisiere Git-Repository...${NC}"

# Git-Konfiguration prüfen
if [[ -z "$(git config --global user.name)" ]]; then
    read -p "  Dein Name für Git-Commits: " git_name
    git config --global user.name "$git_name"
fi

if [[ -z "$(git config --global user.email)" ]]; then
    read -p "  Deine E-Mail für Git-Commits: " git_email
    git config --global user.email "$git_email"
fi

# Git initialisieren (falls noch nicht geschehen)
if [[ ! -d ".git" ]]; then
    git init
    echo -e "${GREEN}  ✓ Git-Repository initialisiert${NC}"
else
    echo -e "${GREEN}  ✓ Git-Repository existiert bereits${NC}"
fi

# Remote setzen
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
echo -e "${GREEN}  ✓ Remote gesetzt: ${REPO_URL}${NC}"

# ============================================
# 7. Commit & Push
# ============================================

echo ""
echo -e "${YELLOW}[7/7] Erstelle Commit und Push zu GitHub...${NC}"

# Alle Dateien hinzufügen
git add .

# Commit erstellen
git commit -m "Initial commit: StratGen MVP

- FastAPI Backend mit Auto-Discovery
- RAG Pipeline (SBERT + Qdrant)
- Agent Orchestration (v1, v2)
- PPTX Export
- Services Layer (Generator, NLG, Providers)
- Knowledge Management
- Lokaler Betrieb für maximalen Datenschutz
" || echo "  (Keine Änderungen zum Committen)"

# Branch auf main setzen
git branch -M main

# Push
echo ""
echo -e "${BLUE}  Pushe zu GitHub...${NC}"
if git push -u origin main; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            ✓ ERFOLGREICH!                  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Dein Repository ist jetzt auf GitHub:"
    echo -e "  ${BLUE}https://github.com/${github_user}/stratgen${NC}"
    echo ""
    echo -e "  Nächste Schritte:"
    echo -e "  1. Öffne das Repository im Browser"
    echo -e "  2. Teile den Repository-Namen mit Claude"
    echo -e "  3. Starte mit der Entwicklung!"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Push fehlgeschlagen!${NC}"
    echo ""
    echo "  Mögliche Ursachen:"
    echo "  - SSH-Key nicht auf GitHub hinzugefügt"
    echo "  - Repository existiert nicht"
    echo "  - Keine Internetverbindung"
    echo ""
    echo "  Teste die Verbindung mit:"
    echo "    ssh -T git@github.com"
    echo ""
    exit 1
fi
