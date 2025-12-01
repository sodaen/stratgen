import { create } from 'zustand'

interface SystemStatus {
  api: boolean
  ollama: boolean
  redis: boolean
  celery: boolean
  servicesActive: number
  servicesTotal: number
}

interface AppState {
  systemStatus: SystemStatus
  isLoading: boolean
  sidebarCollapsed: boolean
  setSystemStatus: (status: SystemStatus) => void
  setLoading: (loading: boolean) => void
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>((set) => ({
  systemStatus: {
    api: false,
    ollama: false,
    redis: false,
    celery: false,
    servicesActive: 0,
    servicesTotal: 14,
  },
  isLoading: true,
  sidebarCollapsed: false,
  setSystemStatus: (status) => set({ systemStatus: status }),
  setLoading: (loading) => set({ isLoading: loading }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}))
