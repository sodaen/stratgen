import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Session {
  id: string
  name: string
  company: string
  status: 'created' | 'running' | 'complete' | 'error'
  phase: string
  progress: number
  slidesGenerated: number
  totalSlides: number
  createdAt: string
  updatedAt: string
}

interface SessionStore {
  currentSessionId: string | null
  sessions: Record<string, Session>
  setCurrentSession: (id: string | null) => void
  updateSession: (id: string, data: Partial<Session>) => void
  addSession: (session: Session) => void
  removeSession: (id: string) => void
  loadSessionsFromBackend: () => Promise<void>
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set, get) => ({
      currentSessionId: null,
      sessions: {},
      
      setCurrentSession: (id) => set({ currentSessionId: id }),
      
      updateSession: (id, data) => set((state) => ({
        sessions: {
          ...state.sessions,
          [id]: { ...state.sessions[id], ...data }
        }
      })),
      
      addSession: (session) => set((state) => ({
        sessions: { ...state.sessions, [session.id]: session }
      })),
      
      removeSession: (id) => set((state) => {
        const newSessions = { ...state.sessions }
        delete newSessions[id]
        return { 
          sessions: newSessions,
          currentSessionId: state.currentSessionId === id ? null : state.currentSessionId
        }
      }),
      
      loadSessionsFromBackend: async () => {
        try {
          const response = await fetch('/api/sessions/active')
          if (!response.ok) return
          
          const backendSessions = await response.json()
          if (!backendSessions || backendSessions.length === 0) return

          const sessionsMap: Record<string, Session> = {}
          
          for (const s of backendSessions) {
            sessionsMap[s.id] = {
              id: s.id,
              name: s.config?.project_name || s.config?.company_name || 'Unbenannt',
              company: s.config?.company_name || '',
              status: s.status,
              phase: s.phase || 'pending',
              progress: s.progress || 0,
              slidesGenerated: s.slides_generated || 0,
              totalSlides: s.total_slides || 10,
              createdAt: s.created_at || new Date().toISOString(),
              updatedAt: s.updated_at || s.created_at || new Date().toISOString()
            }
          }
          
          // Backend-Stand hat immer Vorrang (überschreibt localStorage)
          set((state) => ({
            sessions: { ...state.sessions, ...sessionsMap }
          }))
        } catch (err) {
          console.error('Failed to load sessions:', err)
        }
      }
    }),
    {
      name: 'stratgen-sessions'
    }
  )
)
