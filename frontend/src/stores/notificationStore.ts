import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  title: string
  message: string
  timestamp: number
  read: boolean
}

interface NotificationStore {
  notifications: Notification[]
  unreadCount: number
  soundEnabled: boolean
  notifyOnComplete: boolean
  notifyOnError: boolean
  
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  removeNotification: (id: string) => void
  clearAll: () => void
  setSettings: (settings: Partial<Pick<NotificationStore, 'soundEnabled' | 'notifyOnComplete' | 'notifyOnError'>>) => void
}

const playSound = (type: 'success' | 'error' | 'info' | 'warning') => {
  // Simple beep using Web Audio API
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    oscillator.frequency.value = type === 'error' ? 200 : type === 'success' ? 800 : 500
    oscillator.type = 'sine'
    gainNode.gain.value = 0.1
    
    oscillator.start()
    oscillator.stop(audioContext.currentTime + 0.15)
  } catch (e) {
    // Audio not supported
  }
}

export const useNotificationStore = create<NotificationStore>()(
  persist(
    (set, get) => ({
      notifications: [],
      unreadCount: 0,
      soundEnabled: false,
      notifyOnComplete: true,
      notifyOnError: true,
      
      addNotification: (notification) => {
        const state = get()
        
        // Check if we should show this notification
        if (notification.type === 'success' && !state.notifyOnComplete) return
        if (notification.type === 'error' && !state.notifyOnError) return
        
        const newNotification: Notification = {
          ...notification,
          id: `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: Date.now(),
          read: false,
        }
        
        // Play sound if enabled
        if (state.soundEnabled) {
          playSound(notification.type)
        }
        
        // Show browser notification if permitted
        if (Notification.permission === 'granted') {
          new Notification(notification.title, {
            body: notification.message,
            icon: '/favicon.ico'
          })
        }
        
        set((state) => ({
          notifications: [newNotification, ...state.notifications].slice(0, 50), // Keep last 50
          unreadCount: state.unreadCount + 1,
        }))
      },
      
      markAsRead: (id) => set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      })),
      
      markAllAsRead: () => set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, read: true })),
        unreadCount: 0,
      })),
      
      removeNotification: (id) => set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
        unreadCount: state.notifications.find(n => n.id === id && !n.read) 
          ? state.unreadCount - 1 
          : state.unreadCount,
      })),
      
      clearAll: () => set({ notifications: [], unreadCount: 0 }),
      
      setSettings: (settings) => set(settings),
    }),
    {
      name: 'stratgen-notifications',
    }
  )
)

// Helper to add notifications from anywhere
export const notify = {
  success: (title: string, message: string) => 
    useNotificationStore.getState().addNotification({ type: 'success', title, message }),
  error: (title: string, message: string) => 
    useNotificationStore.getState().addNotification({ type: 'error', title, message }),
  info: (title: string, message: string) => 
    useNotificationStore.getState().addNotification({ type: 'info', title, message }),
  warning: (title: string, message: string) => 
    useNotificationStore.getState().addNotification({ type: 'warning', title, message }),
}
