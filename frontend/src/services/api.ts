const API_BASE = '/api'

// Typen für konsolidierten Status
interface UnifiedStatus {
  ok: boolean
  timestamp: number
  response_ms: number
  services: {
    api: { status: string; response_ms: number }
    ollama: { status: string; model: string; model_loaded: boolean }
    qdrant: { status: string; collections: number; total_chunks: number }
    redis: { status: string }
    celery: { status: string; worker_count: number; queues: Record<string, number> }
  }
  features: Record<string, boolean>
  features_available: number
  features_total: number
  agent: { version: string; intelligence: boolean }
  knowledge: { total_chunks: number; collections: Record<string, any>; metrics: any }
  system: {
    cpu_percent: number
    memory_percent: number
    memory_used_gb: number
    memory_total_gb: number
    disk_percent: number
    disk_free_gb: number
  }
  workers: any
}

// Typen für Intelligent Generator
interface IntelligentGeneratorParams {
  topic: string
  objective?: string
  customer?: string
  industry?: string
  target_audience?: string
  slide_count?: number
  auto_images?: boolean
}

interface IntelligentGeneratorResponse {
  ok: boolean
  slides_count?: number
  duration_seconds?: number
  llm_calls?: number
  output_path?: string
  size_kb?: number
  error?: string
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = API_BASE + endpoint
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })
    
    if (!response.ok) {
      throw new Error('API Error: ' + response.status)
    }
    
    return response.json()
  }

  // ==================== KONSOLIDIERTER STATUS ====================
  
  async getUnifiedStatus(): Promise<UnifiedStatus> {
    return this.request<UnifiedStatus>('/unified/status')
  }

  async getUnifiedHealth() {
    return this.request<any>('/unified/health')
  }

  // ==================== LEGACY STATUS ====================
  
  async getHealth() {
    return this.request<{ status: string }>('/health')
  }

  async getAgentStatus() {
    try {
      const unified = await this.getUnifiedStatus()
      return {
        version: unified.agent.version,
        ollama: {
          ok: unified.services.ollama.status === 'online',
          model: unified.services.ollama.model,
          model_loaded: unified.services.ollama.model_loaded
        },
        features: unified.features
      }
    } catch {
      return this.request<any>('/agent/status')
    }
  }

  async getWorkersStatus() {
    try {
      const unified = await this.getUnifiedStatus()
      return {
        celery_available: unified.services.redis.status === 'online',
        worker_count: unified.services.celery.worker_count,
        queues: unified.services.celery.queues
      }
    } catch {
      return { celery_available: false, worker_count: 0, queues: {} }
    }
  }

  async getOrchestratorStatus() {
    return this.request<any>('/orchestrator/status')
  }

  // ==================== SYSTEM ====================

  async restartSystem() {
    return this.request<any>('/system/restart', { method: 'POST' })
  }

  async restartService(service: string) {
    return this.request<any>('/system/restart/' + service, { method: 'POST' })
  }

  // ==================== INTELLIGENT GENERATOR (NEU) ====================

  async generateIntelligent(params: IntelligentGeneratorParams): Promise<IntelligentGeneratorResponse> {
    return this.request<IntelligentGeneratorResponse>('/generate/intelligent', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async getTemplates() {
    return this.request<{
      templates: Array<{ id: string; name: string; slides: string }>
    }>('/generate/templates')
  }

  async downloadPresentation(outputPath: string): Promise<Blob> {
    const response = await fetch(API_BASE + '/files/download?path=' + encodeURIComponent(outputPath))
    if (!response.ok) {
      throw new Error('Download failed')
    }
    return response.blob()
  }

  // ==================== LIVE GENERATION ====================

  async startGeneration(params: any) {
    return this.request<any>('/live/start', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async getSlides(generationId: string) {
    return this.request<any>('/live/slides/' + generationId)
  }

  async getGenerationProgress(generationId: string) {
    return this.request<any>('/live/progress/' + generationId)
  }

  // ==================== ORCHESTRATOR ====================

  async analyzeOrchestrated(params: any) {
    return this.request<any>('/orchestrator/analyze', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async runFullPipeline(params: any) {
    return this.request<any>('/orchestrator/full-pipeline', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  // ==================== TASKS ====================

  async submitTask(taskType: string, taskName: string, params: any) {
    return this.request<any>('/workers/tasks/submit', {
      method: 'POST',
      body: JSON.stringify({ task_type: taskType, task_name: taskName, params }),
    })
  }

  async getTaskStatus(taskId: string) {
    return this.request<any>('/workers/tasks/' + taskId)
  }

  // ==================== FILES ====================

  async listFiles(path: string = '') {
    return this.request<any>('/files/list?path=' + encodeURIComponent(path))
  }

  async uploadFile(file: File, targetPath: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('path', targetPath)
    
    const response = await fetch(API_BASE + '/files/upload', {
      method: 'POST',
      body: formData,
    })
    return response.json()
  }

  async indexFiles() {
    return this.request<any>('/files/index', { method: 'POST' })
  }

  async getStorageInfo() {
    return this.request<any>('/files/storage')
  }

  // ==================== SESSIONS ====================

  async getActiveSessions() {
    return this.request<any[]>('/sessions/active')
  }

  async createSession(config: any) {
    return this.request<any>('/sessions/create', {
      method: 'POST',
      body: JSON.stringify({ config })
    })
  }

  async getSessionStatus(sessionId: string) {
    return this.request<any>('/sessions/' + sessionId + '/status')
  }

  async startSession(sessionId: string) {
    return this.request<any>('/sessions/' + sessionId + '/start', {
      method: 'POST'
    })
  }

  async uploadToSession(sessionId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(API_BASE + '/sessions/' + sessionId + '/upload', {
      method: 'POST',
      body: formData,
    })
    return response.json()
  }

  // ==================== ANALYTICS ====================

  async getUsageStats() {
    return this.request<any>('/analytics/usage')
  }

  async getPerformanceStats() {
    return this.request<any>('/analytics/performance')
  }

  async getDailyUsage(days: number = 7) {
    return this.request<any[]>('/analytics/daily?days=' + days)
  }

  // ==================== KNOWLEDGE/RAG ====================

  async getRAGStatus() {
    return this.request<any>('/knowledge/admin/status')
  }

  async searchKnowledge(query: string, limit: number = 5) {
    return this.request<any>(`/knowledge/admin/search?query=${encodeURIComponent(query)}&limit=${limit}`)
  }

  // ==================== OLLAMA ====================

  async getOllamaModels() {
    return this.request<any>('/ollama/models')
  }

  // ==================== ADMIN METRICS ====================

  async getAdminDashboard() {
    return this.request<any>('/admin/metrics/dashboard')
  }

  async getSourcesStatus() {
    return this.request<any>('/generator/v2/sources/status').catch(() => ({ ok: false }))
  }

  async getSourcesMetrics() {
    return this.request<any>('/admin/metrics/sources').catch(() => ({ ok: false }))
  }
}

// ==================== CHAT ====================

  async getChatSessions() {
    return this.request<any>('/chat/sessions')
  }

  async newChatSession() {
    return this.request<any>('/chat/sessions/new', { method: 'POST' })
  }

  async getChatHistory(sessionId: string) {
    return this.request<any>(`/chat/${sessionId}/history`)
  }

  async sendChatMessage(sessionId: string, message: string) {
    return this.request<any>(`/chat/${sessionId}/message`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    })
  }

  async sendChatFeedback(sessionId: string, rating: 'up' | 'down', messageId?: string) {
    return this.request<any>(`/chat/${sessionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ rating, message_id: messageId }),
    })
  }

  async deleteChat(sessionId: string) {
    return this.request<any>(`/chat/${sessionId}`, { method: 'DELETE' })
  }

  // ==================== DATA IMPORT ====================

  async uploadDataFile(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const r = await fetch(API_BASE + '/data-import/upload', { method: 'POST', body: formData })
    return r.json()
  }

  async generateDataChart(params: {
    import_id: string
    chart_type: string
    label_column: string
    value_columns: string[]
    title?: string
  }) {
    return this.request<any>('/data-import/chart', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async listDataImports() {
    return this.request<any>('/data-import/list')
  }

  // ==================== OFFLINE ====================

  async getOfflineStatus() {
    return this.request<any>('/offline/status')
  }

  async enableOffline() {
    return this.request<any>('/offline/enable', { method: 'POST' })
  }

  async disableOffline() {
    return this.request<any>('/offline/disable', { method: 'POST' })
  }

  async getOfflineHealth() {
    return this.request<any>('/offline/health')
  }

  // ==================== DEEP RESEARCH ====================

  async startResearch(params: {
    topic: string
    customer_name?: string
    depth?: 'quick' | 'standard' | 'deep'
    language?: string
    auto_ingest?: boolean
  }) {
    return this.request<any>('/research/deep/start', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async getResearchSession(sessionId: string) {
    return this.request<any>(`/research/deep/${sessionId}`)
  }

  async listResearchSessions() {
    return this.request<any>('/research/deep/sessions/list')
  }

  async ingestResearchSession(sessionId: string) {
    return this.request<any>(`/research/deep/${sessionId}/ingest`, { method: 'POST' })
  }

  async cancelResearchSession(sessionId: string) {
    return this.request<any>(`/research/deep/${sessionId}/cancel`, { method: 'POST' })
  }

  async suggestResearchQueries(topic: string, depth = 'standard', language = 'de') {
    return this.request<any>('/research/deep/queries/suggest', {
      method: 'POST',
      body: JSON.stringify({ topic, depth, language }),
    })

export const api = new ApiService()
