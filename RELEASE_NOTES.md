# StratGen – Release v3.56.0 (Sprint 1–4)

**Branch:** `staging` → `main`  
**Datum:** 2026-03-11  
**Status:** Produktionsbereit

---

## Was ist neu

### Sprint 1 – Echte LLM-Integration
Alle Analyse-Endpunkte nutzen jetzt echte LLM-Calls statt Platzhalter.

**Strategy API** (`/strategy/*`)
- `POST /strategy/swot` – SWOT-Analyse via Ollama/OpenAI + RAG-Kontext
- `POST /strategy/porter` – Porter's Five Forces mit Scoring 1–10
- `POST /strategy/gen` – Vollständige Strategie-Präsentation (8/14/22 Slides)
- JSON-Parsing mit Fallback, Persistierung in `data/strategies/`

**Competitor API** (`/competitors/*`)
- `POST /competitors/matrix` – LLM-Scoring 1–10 statt Fake-Symbolen
- `POST /competitors/profile` – Deep-Dive Einzelprofil mit Gegenmaßnahmen

**Self-Learning**
- `get_embedding()` Bug behoben (war falsch eingerückt → IndentationError)
- `on_export_complete()` vollständig implementiert: indexiert jeden PPTX-Export in Qdrant
- Export-Hook in `api_export_bridge.py` nach jedem PPTX-Write

**Performance**
- World Bank API: TTL-Cache verhindert 8.640 HTTP-Calls/Tag bei Status-Polls
- Pipeline-Polling: adaptiv 1s (aktiv) / 5s (idle)

---

### Sprint 2 – Auto Images + Layout-Optimierung
**Auto Images**
- `resolve_for_slide()` wird jetzt bei jedem PPTX-Export aufgerufen
- Passende Bilder aus der Library werden automatisch rechts oben eingefügt
- `enable_images=True` in allen Export-Pfaden

**Image Store**
- Auto-Tagging beim Upload: Dateiname → Keywords automatisch
- `.gitignore` absichert `images/library/` und `images/index.json`

**PPTX Designer v2 – 8 neue Layout-Typen**

| Typ | Layout |
|-----|--------|
| `agenda` | Nummerierte Punkte mit farbigen Badges |
| `cta` / `next_steps` | Box-Layout mit nummerierten Schritten |
| `kpi` / `metrics` | Große Zahlen + Labels |
| `swot` | 2×2-Matrix mit Quadrantenfarben |
| `timeline` / `roadmap` | Horizontale Zeitlinie, abwechselnd oben/unten |
| `image` / `visual` | Bild-dominant mit Caption |
| `comparison` | Two-Column-Alias |
| `statement` | Quote-Alias |

- `_hex_to_rgb` Bug behoben (G-Kanal war doppelt → alle Farben falsch)

---

### Sprint 3 – Data Import + Interactive Chat

**Data Import API** (`/data-import/*`)
- `POST /data-import/upload` – CSV/XLSX hochladen, Spalten automatisch erkennen
- `POST /data-import/chart` – matplotlib Chart generieren (bar/line/pie)
- `POST /data-import/to-slide` – One-Shot: Datei → fertiger Slide-Dict
- Trennzeichen-Erkennung, Wide/Long-Format, Unicode-sicher

**Chat API** (`/chat/*`)
- `POST /chat/{session_id}/message` – Multi-Turn Chat mit RAG-Kontext
- `POST /chat/{session_id}/message/stream` – SSE Token-Streaming
- `POST /chat/{session_id}/feedback` – Thumbs up/down → Self-Learning
- Gesprächshistorie persistent pro Session gespeichert
- System-Kontext aus Session (Firma, Projekt, Branche)

---

### Sprint 4 – Offline Mode

**Zentrales Offline-Modul** (`services/offline.py`)
- `is_offline()` – prüft ENV oder Runtime-Override
- `guard(service_name)` – Decorator für externe Calls
- `set_offline(bool)` – Runtime-Toggle ohne Neustart

**Offline API** (`/offline/*`)
- `GET /offline/status` – aktueller Modus + Service-Liste
- `POST /offline/enable|disable` – Laufzeit-Umschalten
- `GET /offline/health` – Live-Ping aller externen Services

**Guards** in `data_services`, `strategy_api`, `competitor_api`, `chat_api`

**Deploy-Helper** (`scripts/deploy_wait.sh`)
- Wartet nach `systemctl restart` bis Backend auf Port 8011 antwortet
- Timeout konfigurierbar (default 60s)

---

## Breaking Changes
Keine. Alle bestehenden Endpoints bleiben kompatibel.

## Migration
```bash
# .env ergänzen (optional):
STRATGEN_OFFLINE=false
LLM_PROVIDER=ollama
LLM_MODEL=mistral
```

## Neue Abhängigkeiten
Keine neuen pip-Pakete erforderlich. `openpyxl` und `matplotlib` waren bereits installiert.

---

## Merge-Befehl
```bash
git checkout main
git merge staging --no-ff -m "release: v0.2.0 – Sprint 1-4 (LLM, Images, Chat, Offline)"
git push origin main
git tag v0.2.0
git push origin v0.2.0
```
