import { Search, User } from 'lucide-react'
import NotificationDropdown from '../NotificationDropdown'

interface HeaderProps {
  title?: string
}

export default function Header({ title }: HeaderProps) {
  return (
    <header className="h-16 bg-dark-bg border-b border-dark-border flex items-center justify-between px-6">
      {/* Left: Title or Search */}
      <div className="flex items-center gap-4">
        {title ? (
          <h1 className="text-xl font-semibold text-white">{title}</h1>
        ) : (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search..."
              className="w-64 pl-10 pr-4 py-2 bg-dark-card border border-dark-border rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        )}
      </div>
      
      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <NotificationDropdown />
        
        {/* User */}
        <button className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <User className="w-4 h-4 text-white" />
        </button>
      </div>
    </header>
  )
}
