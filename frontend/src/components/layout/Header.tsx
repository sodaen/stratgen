import { Bell, Search, User } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import StatusBadge from '../common/StatusBadge'

interface HeaderProps {
  title: string
  subtitle?: string
}

export default function Header({ title, subtitle }: HeaderProps) {
  const { systemStatus } = useAppStore()

  return (
    <header className="h-16 bg-dark-card/50 backdrop-blur-xl border-b border-dark-border px-6 flex items-center justify-between sticky top-0 z-40">
      <div>
        <h1 className="text-xl font-semibold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search... (⌘K)"
            className="w-64 pl-10 pr-4 py-2 bg-dark-border rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>

        {/* Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-dark-border rounded-lg">
          <StatusBadge 
            status={systemStatus.api ? 'online' : 'offline'} 
            pulse={false}
          />
          <span className="text-xs text-slate-400">
            {systemStatus.api ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Notifications */}
        <button className="p-2 rounded-lg hover:bg-dark-border transition-colors relative">
          <Bell className="w-5 h-5 text-slate-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full" />
        </button>

        {/* User */}
        <button className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <User className="w-4 h-4 text-white" />
        </button>
      </div>
    </header>
  )
}
