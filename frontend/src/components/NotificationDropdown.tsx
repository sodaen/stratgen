import { useState, useRef, useEffect } from 'react'
import { Bell, X, Check, CheckCheck, Trash2, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'
import { useNotificationStore, Notification as AppNotification } from '../stores/notificationStore'
import { motion, AnimatePresence } from 'framer-motion'

const typeIcons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
}

const typeColors = {
  success: 'text-green-500',
  error: 'text-red-500',
  info: 'text-blue-500',
  warning: 'text-yellow-500',
}

const typeBgColors = {
  success: 'bg-green-500/10',
  error: 'bg-red-500/10',
  info: 'bg-blue-500/10',
  warning: 'bg-yellow-500/10',
}

function formatTime(timestamp: number): string {
  const diff = Date.now() - timestamp
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return 'Gerade eben'
  if (minutes < 60) return `vor ${minutes} Min`
  if (hours < 24) return `vor ${hours} Std`
  return `vor ${days} Tagen`
}

function NotificationItem({ notification }: { notification: AppNotification; onClose: () => void }) {
  const { markAsRead, removeNotification } = useNotificationStore()
  const Icon = typeIcons[notification.type]
  
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className={`p-3 rounded-lg ${typeBgColors[notification.type]} ${!notification.read ? 'border-l-2 border-l-blue-500' : ''}`}
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${typeColors[notification.type]} flex-shrink-0 mt-0.5`} />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-white text-sm">{notification.title}</p>
          <p className="text-gray-400 text-xs mt-0.5 line-clamp-2">{notification.message}</p>
          <p className="text-gray-500 text-xs mt-1">{formatTime(notification.timestamp)}</p>
        </div>
        <div className="flex items-center gap-1">
          {!notification.read && (
            <button
              onClick={() => markAsRead(notification.id)}
              className="p-1 hover:bg-dark-border rounded transition-colors"
              title="Als gelesen markieren"
            >
              <Check className="w-3.5 h-3.5 text-gray-400" />
            </button>
          )}
          <button
            onClick={() => removeNotification(notification.id)}
            className="p-1 hover:bg-dark-border rounded transition-colors"
            title="Löschen"
          >
            <X className="w-3.5 h-3.5 text-gray-400" />
          </button>
        </div>
      </div>
    </motion.div>
  )
}

export default function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { notifications, unreadCount, markAllAsRead, clearAll } = useNotificationStore()
  
  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])
  
  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-lg hover:bg-dark-border transition-colors relative"
      >
        <Bell className="w-5 h-5 text-slate-400" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-blue-500 rounded-full text-xs text-white flex items-center justify-center font-medium">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute right-0 top-full mt-2 w-96 bg-dark-card border border-dark-border rounded-xl shadow-2xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 border-b border-dark-border flex items-center justify-between">
              <h3 className="font-semibold text-white">Benachrichtigungen</h3>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  >
                    <CheckCheck className="w-3.5 h-3.5" />
                    Alle gelesen
                  </button>
                )}
                {notifications.length > 0 && (
                  <button
                    onClick={clearAll}
                    className="text-xs text-gray-400 hover:text-red-400 flex items-center gap-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Leeren
                  </button>
                )}
              </div>
            </div>
            
            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Keine Benachrichtigungen</p>
                </div>
              ) : (
                <div className="p-2 space-y-2">
                  <AnimatePresence>
                    {notifications.map((notification) => (
                      <NotificationItem
                        key={notification.id}
                        notification={notification}
                        onClose={() => setIsOpen(false)}
                      />
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
