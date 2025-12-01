type SSECallback = (event: any) => void

export class SSEService {
  private eventSource: EventSource | null = null
  private callbacks: Map<string, SSECallback[]> = new Map()

  connect(generationId: string) {
    if (this.eventSource) {
      this.disconnect()
    }

    this.eventSource = new EventSource(`/api/live/stream/${generationId}`)

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit('message', data)
        
        if (data.type) {
          this.emit(data.type, data)
        }
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }

    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      this.emit('error', error)
    }

    this.eventSource.onopen = () => {
      this.emit('open', {})
    }
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }

  on(event: string, callback: SSECallback) {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, [])
    }
    this.callbacks.get(event)!.push(callback)
  }

  off(event: string, callback: SSECallback) {
    const callbacks = this.callbacks.get(event)
    if (callbacks) {
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.callbacks.get(event)
    if (callbacks) {
      callbacks.forEach(cb => cb(data))
    }
  }
}

export const sseService = new SSEService()
