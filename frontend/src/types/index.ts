export interface Slide {
  type: string
  title: string
  bullets: string[]
  notes?: string
  layout_hint?: string
}

export interface Project {
  id: string
  name: string
  topic: string
  slides: Slide[]
  created_at: string
  updated_at: string
}

export interface SystemStatus {
  api: boolean
  ollama: boolean
  redis: boolean
  celery: boolean
  servicesActive: number
  servicesTotal: number
}

export interface GenerationConfig {
  topic: string
  brief: string
  customer_name: string
  project_name: string
  industry: string
  audience: string
  deck_size: number
  temperature: number
  colors: {
    primary: string
    secondary: string
    accent: string
  }
  style: string
}

export interface PipelinePhase {
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  duration?: number
  worker?: string
}

export interface Worker {
  name: string
  concurrency: number
  active_tasks: number
  status: 'online' | 'offline'
}

export interface QueueStatus {
  name: string
  length: number
}
