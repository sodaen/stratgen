const API_BASE = '/api'

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }
    
    return response.json()
  }

  // Health & Status
  async getHealth() {
    return this.request<{ ok: boolean }>('/health')
  }

  async getAgentStatus() {
    return this.request<any>('/agent/v3/status')
  }

  async getWorkersStatus() {
    return this.request<any>('/workers/status')
  }

  async getOrchestratorStatus() {
    return this.request<any>('/orchestrator/status')
  }

  // System Control
  async restartSystem() {
    return this.request<any>('/system/restart', { method: 'POST' })
  }

  async restartService(service: string) {
    return this.request<any>(`/system/restart/${service}`, { method: 'POST' })
  }

  // Generation
  async startGeneration(params: any) {
    return this.request<any>('/live/start', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async getSlides(generationId: string) {
    return this.request<any>(`/live/slides/${generationId}`)
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

  // Workers
  async submitTask(taskType: string, taskName: string, params: any) {
    return this.request<any>('/workers/tasks/submit', {
      method: 'POST',
      body: JSON.stringify({ task_type: taskType, task_name: taskName, params }),
    })
  }

  async getTaskStatus(taskId: string) {
    return this.request<any>(`/workers/tasks/${taskId}`)
  }

  // Files
  async listFiles(path: string = '') {
    return this.request<any>(`/files/list?path=${encodeURIComponent(path)}`)
  }

  async uploadFile(file: File, targetPath: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('path', targetPath)
    
    const response = await fetch(`${API_BASE}/files/upload`, {
      method: 'POST',
      body: formData,
    })
    return response.json()
  }

  async indexFiles() {
    return this.request<any>('/files/index', { method: 'POST' })
  }
}

export const api = new ApiService()
