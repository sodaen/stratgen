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
  // Current active session
  currentSessionId: string | null
  
  // All known sessions
  sessions: Record<string, Session>
  
  // Actions
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
        sessions: {
          ...state.sessions,
          [session.id]: session
        }
      })),
      
      removeSession: (id) => set((state) => {
        const { [id]: _, ...rest } = state.sessions
        return { 
          sessions: rest,
          currentSessionId: state.currentSessionId === id ? null : state.currentSessionId
        }
      }),
      
      loadSessionsFromBackend: async () => {
        try {
          const response = await fetch('/api/sessions/active')
          if (!response.ok) return
          
          const backendSessions = await response.json()
          const sessionsMap: Record<string, Session> = {}
          
          for (const s of backendSessions) {
            sessionsMap[s.id] = {
              id: s.id,
              name: s.config?.project_name || 'Unnamed',
              company: s.config?.company_name || '',
              status: s.status,
              phase: s.phase,
              progress: s.progress || 0,
              slidesGenerated: s.slides_generated || 0,
              totalSlides: s.total_slides || 10,
              createdAt: s.created_at,
              updatedAt: s.updated_at
            }
          }
          
          set({ sessions: sessionsMap })
        } catch (err) {
          console.error('Failed to load sessions:', err)
        }
      }
    }),
    {
      name: 'stratgen-sessions',
      partialize: (state) => ({ 
        currentSessionId: state.currentSessionId,
        sessions: state.sessions 
      })
    }
  )
)
