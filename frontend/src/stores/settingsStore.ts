import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Settings {
  // Appearance
  theme: 'dark' | 'light'
  accentColor: string
  compactMode: boolean
  animations: boolean
  
  // Generation Defaults
  defaultSlides: number
  defaultTemperature: number
  defaultStyle: string
  autoSave: boolean
  
  // LLM Settings
  llmModel: string
  maxTokens: number
  timeout: number
  
  // Notifications
  notifyOnComplete: boolean
  notifyOnError: boolean
  soundEnabled: boolean
}

interface SettingsStore extends Settings {
  setSettings: (settings: Partial<Settings>) => void
  resetToDefaults: () => void
  syncWithBackend: () => Promise<void>
}

const defaultSettings: Settings = {
  theme: 'dark',
  accentColor: 'blue',
  compactMode: false,
  animations: true,
  defaultSlides: 10,
  defaultTemperature: 0.7,
  defaultStyle: 'corporate',
  autoSave: true,
  llmModel: 'mistral:latest',
  maxTokens: 4096,
  timeout: 120,
  notifyOnComplete: true,
  notifyOnError: true,
  soundEnabled: false,
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      ...defaultSettings,
      
      setSettings: (newSettings) => {
        set(newSettings)
        // Sync notification settings
        if ('notifyOnComplete' in newSettings || 'notifyOnError' in newSettings || 'soundEnabled' in newSettings) {
          import('./notificationStore').then(({ useNotificationStore }) => {
            useNotificationStore.getState().setSettings({
              notifyOnComplete: newSettings.notifyOnComplete ?? get().notifyOnComplete,
              notifyOnError: newSettings.notifyOnError ?? get().notifyOnError,
              soundEnabled: newSettings.soundEnabled ?? get().soundEnabled,
            })
          })
        }
      },
      
      resetToDefaults: () => set(defaultSettings),
      
      syncWithBackend: async () => {
        const state = get()
        try {
          // Sync LLM settings
          await fetch('/api/settings/llm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              model: state.llmModel,
              max_tokens: state.maxTokens,
              timeout: state.timeout,
            })
          })
          
          // Sync generation defaults
          await fetch('/api/settings/generation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              default_slides: state.defaultSlides,
              temperature: state.defaultTemperature,
              style: state.defaultStyle,
              auto_save: state.autoSave,
            })
          })
        } catch (e) {
          console.error('Failed to sync settings with backend:', e)
        }
      }
    }),
    {
      name: 'stratgen-settings-v2',
    }
  )
)
