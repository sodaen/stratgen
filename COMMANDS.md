# StratGen - Wichtige Befehle

## 🚀 System starten
```bash
~/stratgen/scripts/startup_all.sh
```

## 🛑 System stoppen
```bash
~/stratgen/scripts/shutdown_all.sh
```

## 🔄 Git Sync (sofort, ohne auf Timer warten)
```bash
~/stratgen/scripts/auto_sync_staging.sh
```

## 📦 Staging → Main mergen
```bash
~/stratgen/scripts/merge_to_main.sh
```

---

## 📊 Status prüfen

### API Health
```bash
curl http://localhost:8011/health
```

### Git Status
```bash
cd ~/stratgen && git status
```

### Sync Timer Status
```bash
sudo systemctl status stratgen-sync.timer
```

### Logs anschauen
```bash
tail -f ~/stratgen/logs/api.log
tail -f ~/stratgen/logs/sync.log
```

---

## 🔧 Einzelne Services

### StratGen API
```bash
# Starten (Entwicklungsmodus mit auto-reload)
cd ~/stratgen && source .venv/bin/activate
uvicorn backend.api:app --host 0.0.0.0 --port 8011 --reload

# Starten (Hintergrund)
nohup uvicorn backend.api:app --host 0.0.0.0 --port 8011 > logs/api.log 2>&1 &

# Stoppen
pkill -f "uvicorn backend.api:app"
```

### Ollama (LLM)
```bash
# Starten
ollama serve

# Modell laden
ollama pull mistral

# Testen
curl http://localhost:11434/api/tags
```

### Qdrant (Vector DB)
```bash
# Mit Docker
docker run -p 6333:6333 qdrant/qdrant

# Testen
curl http://localhost:6333/health
```

---

## 🌿 Git Workflow

### Aktuellen Branch sehen
```bash
git branch --show-current
```

### Zu staging wechseln (Entwicklung)
```bash
git checkout staging
```

### Zu main wechseln (Stable)
```bash
git checkout main
```

### Änderungen von GitHub holen
```bash
git pull origin staging
```

### Lokale Änderungen verwerfen
```bash
git checkout -- .
```

### Auf älteren Stand zurücksetzen
```bash
# Letzte 10 Commits anzeigen
git log --oneline -10

# Auf bestimmten Commit zurücksetzen (VORSICHT!)
git reset --hard <commit-hash>

# Zurück zum letzten stabilen main
git checkout main
git reset --hard origin/main
```

---

## 🔗 URLs

| Service | URL |
|---------|-----|
| API Docs (Swagger) | http://localhost:8011/docs |
| API Docs (ReDoc) | http://localhost:8011/redoc |
| Health Check | http://localhost:8011/health |
| Ollama | http://localhost:11434 |
| Qdrant | http://localhost:6333 |
| GitHub | https://github.com/danielploetz-glitch/stratgen |

---

## 📁 Wichtige Pfade

| Was | Pfad |
|-----|------|
| Projekt-Root | `~/stratgen/` |
| Backend (API) | `~/stratgen/backend/` |
| Services (Business Logic) | `~/stratgen/services/` |
| Scripts | `~/stratgen/scripts/` |
| Logs | `~/stratgen/logs/` |
| Daten | `~/stratgen/data/` |
| Knowledge Base | `~/stratgen/data/knowledge/` |
| Exports (PPTX) | `~/stratgen/data/exports/` |

---

## 🆘 Fehlerbehebung

### API startet nicht
```bash
# Logs prüfen
tail -50 ~/stratgen/logs/api.log

# Port bereits belegt?
lsof -i :8011

# Prozess killen falls nötig
kill -9 $(lsof -t -i :8011)
```

### Git Push schlägt fehl
```bash
# SSH testen
ssh -T git@github.com

# Remote prüfen
git remote -v

# Force push (VORSICHT - nur wenn nötig)
git push -f origin staging
```

### Sync funktioniert nicht
```bash
# Timer Status
sudo systemctl status stratgen-sync.timer

# Timer neu starten
sudo systemctl restart stratgen-sync.timer

# Manuell syncen
~/stratgen/scripts/auto_sync_staging.sh
```
