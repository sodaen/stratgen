const API_BASE = '/api'

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

  // Health & Status
  async getHealth() {
    return this.request<{ status: string }>('/health')
  }

  async getAgentStatus() {
    // Korrigiert: /agent/status enthält Ollama-Info
    return this.request<any>('/agent/status')
  }

  async getWorkersStatus() {
    // Fallback da Workers nicht implementiert
    return this.request<any>('/workers/status').catch(() => ({
      celery_available: false,
      worker_count: 0,
      queues: {}
    }))
  }

  async getOrchestratorStatus() {
    return this.request<any>('/orchestrator/status')
  }

  // System Management
  async restartSystem() {
    return this.request<any>('/system/restart', { method: 'POST' })
  }

  async restartService(service: string) {
    return this.request<any>('/system/restart/' + service, { method: 'POST' })
  }

  // Live Generation
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

  // Orchestrator
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

  // Workers/Tasks
  async submitTask(taskType: string, taskName: string, params: any) {
    return this.request<any>('/workers/tasks/submit', {
      method: 'POST',
      body: JSON.stringify({ task_type: taskType, task_name: taskName, params }),
    })
  }

  async getTaskStatus(taskId: string) {
    return this.request<any>('/workers/tasks/' + taskId)
  }

  // Files
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

  // Sessions
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

  // Analytics
  async getUsageStats() {
    return this.request<any>('/analytics/usage')
  }

  async getPerformanceStats() {
    return this.request<any>('/analytics/performance')
  }

  async getDailyUsage(days: number = 7) {
    return this.request<any[]>('/analytics/daily?days=' + days)
  }

  // Knowledge/RAG
  async getRAGStatus() {
    return this.request<any>('/knowledge/admin/status')
  }

  async searchKnowledge(query: string, limit: number = 5) {
    return this.request<any>(`/knowledge/admin/search?query=${encodeURIComponent(query)}&limit=${limit}`)
  }

  // Ollama
  async getOllamaModels() {
    return this.request<any>('/ollama/models')
  }
}

export const api = new ApiService()
