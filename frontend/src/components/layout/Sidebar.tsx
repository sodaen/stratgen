import { NavLink } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LayoutDashboard, 
  Sparkles, 
  Wand2, 
  Edit3, 
  GitBranch, 
  Activity, 
  FolderOpen, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Power,
  BookOpen
, BarChart3 } from 'lucide-react'
import Logo from '../common/Logo'
import ThemeToggle from '../common/ThemeToggle'
import { useAppStore } from '../../stores/appStore'
import { cn } from '../../utils/helpers'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/knowledge', icon: BookOpen, label: 'Knowledge' },
  { path: '/generator', icon: Sparkles, label: 'Generator' },
  { path: '/wizard', icon: Wand2, label: 'Wizard' },
  { path: '/editor', icon: Edit3, label: 'Live Editor' },
  { divider: true },
  { path: '/pipeline', icon: GitBranch, label: 'Pipeline' },
  { path: '/health', icon: Activity, label: 'System Health' },
  { path: '/files', icon: FolderOpen, label: 'File Manager' },
  { divider: true },
  { path: '/settings', icon: Settings, label: 'Settings' },
  { path: '/admin', icon: BarChart3, label: 'Admin Dashboard' },
]

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, systemStatus } = useAppStore()

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? 80 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-0 h-screen bg-dark-card border-r border-dark-border flex flex-col z-50"
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between border-b border-dark-border">
        <Logo collapsed={sidebarCollapsed} />
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg hover:bg-dark-border transition-colors"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-slate-400" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item, index) => {
          if (item.divider) {
            return <div key={index} className="h-px bg-dark-border my-3" />
          }

          const Icon = item.icon!
          
          return (
            <NavLink
              key={item.path}
              to={item.path!}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200",
                isActive 
                  ? "bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-white border border-blue-500/30" 
                  : "text-slate-400 hover:text-white hover:bg-dark-border"
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                    className="text-sm font-medium whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-dark-border space-y-3">
        {/* System Status Mini */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={cn(
              "w-2 h-2 rounded-full",
              systemStatus.servicesActive >= systemStatus.servicesTotal * 0.9 
                ? "bg-green-500" 
                : systemStatus.servicesActive > 0 
                  ? "bg-yellow-500" 
                  : "bg-red-500"
            )} />
            {!sidebarCollapsed && (
              <span className="text-xs text-slate-500">
                {systemStatus.servicesActive}/{systemStatus.servicesTotal} Services
              </span>
            )}
          </div>
          <ThemeToggle />
        </div>

        {/* Version */}
        {!sidebarCollapsed && (
          <div className="text-center">
            <span className="text-xs text-slate-600">v3.8</span>
          </div>
        )}
      </div>
    </motion.aside>
  )
}
