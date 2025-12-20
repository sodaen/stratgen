# STRATGEN FRONTEND ANALYSE v3.37

## ÜBERSICHT

**Frontend-Stack:** React 18 + TypeScript + Vite + TailwindCSS + Zustand
**Dateien:** 25 TSX + 9 TS = 34 Dateien
**Letzte Analyse:** $(date +%Y-%m-%d)

---

## SEITEN & STATUS

### 1. Dashboard.tsx ✅ FUNKTIONIERT
**Route:** `/`
**API-Calls:**
- `GET /api/orchestrator/status` → Features laden
- `GET /api/analytics/usage` → Statistiken
- Sessions aus Store

**Status:** Funktioniert, nutzt Sessions korrekt

---

### 2. Generator.tsx ⚠️ TEILWEISE
**Route:** `/generator`
**API-Calls:**
- `POST /api/sessions/create` → Session erstellen
- `POST /api/sessions/{id}/start` → Generation starten
- `GET /api/sessions/{id}/status` → Polling
- `GET /api/sessions/{id}/slides` → Slides holen
- `GET /api/export/{format}/{id}` → Export

**Problem:** Nutzt alte Session-API, nicht den neuen `/api/generate/intelligent`
**TODO:** 
- [ ] Neuen Intelligent-Generator als Option hinzufügen
- [ ] Briefing-Felder erweitern (topic, objective, industry)

---

### 3. Wizard.tsx ⚠️ TEILWEISE
**Route:** `/wizard`
**API-Calls:**
- Gleiche wie Generator (Session-basiert)
- Polling für Progress

**Problem:** Nutzt alte Session-API
**TODO:**
- [ ] Option für Intelligent-Generator
- [ ] Bessere Briefing-Qualitäts-Berechnung

---

### 4. Editor.tsx ❓ ZU PRÜFEN
**Route:** `/editor`
**API-Calls:**
- Session-Slides laden
- Slide-Updates speichern

**TODO:** Vollständig analysieren

---

### 5. Pipeline.tsx ✅ FUNKTIONIERT
**Route:** `/pipeline`
**API-Calls:**
- `GET /api/sessions/active` → Aktive Sessions
- Session-Status Polling

**Status:** Zeigt Pipeline-Phasen an

---

### 6. Health.tsx ✅ FUNKTIONIERT
**Route:** `/health`
**API-Calls:**
- `GET /api/unified/status` → System-Status
- `POST /api/system/restart/{service}` → Service neustarten

**Komponenten:**
- RAGStatus (Qdrant/Knowledge)
- ServiceCards für jeden Service

**Status:** Funktioniert gut

---

### 7. Files.tsx ✅ FUNKTIONIERT
**Route:** `/files`
**API-Calls:**
- `GET /api/files/list?path=` → Dateien auflisten
- `POST /api/files/upload` → Upload
- `POST /api/files/index` → Indexieren
- `GET /api/files/storage` → Speicher-Info

**Status:** Funktioniert

---

### 8. Settings.tsx ✅ FUNKTIONIERT
**Route:** `/settings`
**Features:**
- Theme Toggle (Dark/Light)
- Notification Settings
- System Preferences

**Status:** Nutzt Stores, kein Backend nötig

---

### 9. Knowledge.tsx ✅ FUNKTIONIERT
**Route:** `/knowledge`
**Komponenten:**
- AdminDashboard
- KnowledgeChat
- RAGStatus

**API-Calls (via Komponenten):**
- `GET /api/knowledge/admin/status`
- `GET /api/knowledge/admin/collections`
- `POST /api/rag/chat`

**Status:** Funktioniert

---

### 10. AdminDashboard.tsx ✅ FUNKTIONIERT
**Route:** `/admin`
**API-Calls:**
- `GET /api/admin/metrics/dashboard`
- `GET /api/unified/status`

**Status:** Funktioniert

---

## API SERVICE (api.ts)

### Vorhandene Methoden:
✅ getUnifiedStatus()
✅ getHealth()
✅ getAgentStatus()
✅ getWorkersStatus()
✅ getOrchestratorStatus()
✅ restartSystem()
✅ restartService()
✅ startGeneration() → /live/start
✅ getSlides()
✅ getGenerationProgress()
✅ analyzeOrchestrated()
✅ runFullPipeline()
✅ submitTask()
✅ getTaskStatus()
✅ listFiles()
✅ uploadFile()
✅ indexFiles()
✅ getStorageInfo()
✅ getActiveSessions()
✅ createSession()
✅ getSessionStatus()
✅ startSession()
✅ uploadToSession()
✅ getUsageStats()
✅ getPerformanceStats()
✅ getDailyUsage()
✅ getRAGStatus()
✅ searchKnowledge()
✅ getOllamaModels()
✅ getAdminDashboard()
✅ getSourcesStatus()
✅ getSourcesMetrics()

### FEHLENDE Methoden:
❌ generateIntelligent() → POST /api/generate/intelligent
❌ getTemplates() → GET /api/generate/templates

---

## STORES

### sessionStore.ts ✅
- Sessions verwalten
- loadSessionsFromBackend()
- addSession(), setCurrentSession()

### themeStore.ts ✅
- Dark/Light Mode

### settingsStore.ts ✅
- LLM Model, Temperature
- Auto-Save, Notifications

### notificationStore.ts ✅
- Toast Notifications

### appStore.ts ✅
- Global App State

---

## KOMPONENTEN

### Layout/
- Layout.tsx ✅ - Main Layout
- Sidebar.tsx ✅ - Navigation
- Header.tsx ✅ - Top Bar

### Common/
- Logo.tsx ✅
- StatusBadge.tsx ✅
- ThemeToggle.tsx ✅

### Knowledge/
- KnowledgeDashboard.tsx ✅ - Analytics
- KnowledgeChat.tsx ✅ - RAG Chat
- KnowledgeControls.tsx ✅ - Admin Controls
- ChunkInspector.tsx ✅ - Chunk Details
- RAGStatus.tsx ✅ - Qdrant Status

### Admin/
- AdminDashboard.tsx ✅
- NotificationDropdown.tsx ✅

---

## AKTIONSPLAN

### Phase 1: API Service erweitern
1. [ ] generateIntelligent() Methode hinzufügen
2. [ ] getTemplates() Methode hinzufügen

### Phase 2: Generator.tsx erweitern
1. [ ] Toggle für "Intelligent Mode" vs "Session Mode"
2. [ ] Erweiterte Briefing-Felder
3. [ ] Research-Integration anzeigen

### Phase 3: Wizard.tsx erweitern
1. [ ] Gleiche Intelligent-Mode Option
2. [ ] Bessere Vorschau

### Phase 4: Testen
1. [ ] Alle Seiten durchklicken
2. [ ] API-Calls in DevTools prüfen
3. [ ] Error Handling verbessern

---

## BACKEND-ENDPOINTS ÜBERSICHT

### Sessions
- POST /api/sessions/create ✅
- GET /api/sessions/active ✅
- GET /api/sessions/{id}/status ✅
- POST /api/sessions/{id}/start ✅
- GET /api/sessions/{id}/slides ✅
- POST /api/sessions/{id}/upload ✅

### Generate (NEU)
- POST /api/generate/intelligent ✅ (Backend vorhanden, Frontend fehlt)
- GET /api/generate/templates ✅ (Backend vorhanden, Frontend fehlt)

### Export
- GET /api/export/{format}/{session_id} ✅

### System
- GET /api/health ✅
- GET /api/unified/status ✅
- POST /api/system/restart ✅
- POST /api/system/restart/{service} ✅

### Knowledge/RAG
- GET /api/knowledge/admin/status ✅
- GET /api/knowledge/admin/collections ✅
- GET /api/knowledge/admin/search ✅
- POST /api/rag/chat ✅

### Analytics
- GET /api/analytics/usage ✅
- GET /api/analytics/performance ✅
- GET /api/analytics/daily ✅

### Files
- GET /api/files/list ✅
- POST /api/files/upload ✅
- POST /api/files/index ✅
- GET /api/files/storage ✅

### Orchestrator
- GET /api/orchestrator/status ✅
- POST /api/orchestrator/analyze ✅
- POST /api/orchestrator/full-pipeline ✅

### Admin
- GET /api/admin/metrics/dashboard ✅

