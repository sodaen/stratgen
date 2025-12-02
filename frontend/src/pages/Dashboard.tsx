import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Sparkles, 
  TrendingUp, 
  Clock, 
  CheckCircle,
  Play,
  FileText,
  BarChart3,
  Zap,
  ArrowRight,
  Loader2,
  AlertCircle,
  FolderOpen
} from 'lucide-react'
import { useSessionStore } from '../stores/sessionStore'
import { cn } from '../utils/helpers'

interface DashboardStats {
  totalProjects: number
  completedToday: number
  avgGenerationTime: string
  slidesGenerated: number
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { sessions, currentSessionId, loadSessionsFromBackend, setCurrentSession } = useSessionStore()
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    completedToday: 0,
    avgGenerationTime: '~45s',
    slidesGenerated: 0
  })
  const [features, setFeatures] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // Load sessions from backend
      await loadSessionsFromBackend()
      
      // Load orchestrator status for features
      const statusRes = await fetch('/api/orchestrator/status')
      if (statusRes.ok) {
        const data = await statusRes.json()
        setFeatures(data.features || {})
      }
      
      // Load analytics
      const analyticsRes = await fetch('/api/analytics/usage')
      if (analyticsRes.ok) {
        const data = await analyticsRes.json()
        setStats(prev => ({
          ...prev,
          totalProjects: data.total_generations || Object.keys(sessions).length,
          slidesGenerated: data.total_slides || 0
        }))
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Calculate stats from sessions
  const sessionList = Object.values(sessions)
  const completedSessions = sessionList.filter(s => s.status === 'complete')
  const runningSessions = sessionList.filter(s => s.status === 'running')
  const recentSessions = sessionList
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, 5)

  const totalSlides = sessionList.reduce((sum, s) => sum + (s.slidesGenerated || 0), 0)

  const openSession = (sessionId: string) => {
    setCurrentSession(sessionId)
    navigate(`/editor?session=${sessionId}`)
  }

  const quickActions = [
    { 
      title: 'New Presentation', 
      description: 'Start with the wizard',
      icon: Sparkles, 
      color: 'from-blue-500 to-cyan-500',
      onClick: () => navigate('/wizard')
    },
    { 
      title: 'Quick Generate', 
      description: 'Fast generation mode',
      icon: Zap, 
      color: 'from-purple-500 to-pink-500',
      onClick: () => navigate('/generator')
    },
    { 
      title: 'View Pipeline', 
      description: 'Monitor progress',
      icon: BarChart3, 
      color: 'from-green-500 to-emerald-500',
      onClick: () => navigate('/pipeline')
    },
    { 
      title: 'Manage Files', 
      description: 'Knowledge & templates',
      icon: FolderOpen, 
      color: 'from-orange-500 to-amber-500',
      onClick: () => navigate('/files')
    },
  ]

  const statCards = [
    { label: 'Total Projects', value: sessionList.length, icon: FileText, color: 'text-blue-400' },
    { label: 'Completed', value: completedSessions.length, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Running', value: runningSessions.length, icon: Play, color: 'text-yellow-400' },
    { label: 'Total Slides', value: totalSlides, icon: TrendingUp, color: 'text-purple-400' },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'bg-green-500'
      case 'running': return 'bg-blue-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-slate-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return CheckCircle
      case 'running': return Loader2
      case 'error': return AlertCircle
      default: return Clock
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-dark-card rounded-2xl border border-dark-border p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">{stat.label}</p>
                  <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <div className={cn("p-3 rounded-xl bg-dark-border", stat.color)}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {quickActions.map((action, index) => {
          const Icon = action.icon
          return (
            <motion.button
              key={action.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.1 }}
              onClick={action.onClick}
              className={cn(
                "p-6 rounded-2xl bg-gradient-to-br text-left transition-all hover:scale-[1.02] hover:shadow-lg",
                action.color
              )}
            >
              <Icon className="w-8 h-8 text-white mb-3" />
              <h3 className="text-lg font-semibold text-white">{action.title}</h3>
              <p className="text-sm text-white/70 mt-1">{action.description}</p>
            </motion.button>
          )
        })}
      </div>

      {/* Recent Projects */}
      <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Recent Projects</h2>
          <button 
            onClick={() => navigate('/files')}
            className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            View all <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {recentSessions.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-500">No projects yet</p>
            <button 
              onClick={() => navigate('/wizard')}
              className="mt-4 px-6 py-2 bg-blue-500 rounded-lg text-white text-sm hover:bg-blue-600 transition-colors"
            >
              Create your first presentation
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {recentSessions.map((session) => {
              const StatusIcon = getStatusIcon(session.status)
              return (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between p-4 bg-dark-border rounded-xl hover:bg-dark-bg transition-colors cursor-pointer"
                  onClick={() => openSession(session.id)}
                >
                  <div className="flex items-center gap-4">
                    <div className={cn("w-2 h-2 rounded-full", getStatusColor(session.status))} />
                    <div>
                      <h3 className="font-medium text-white">{session.name || 'Unnamed Project'}</h3>
                      <p className="text-sm text-slate-500">
                        {session.company} • {session.slidesGenerated}/{session.totalSlides} slides
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-slate-400 capitalize">{session.status}</p>
                      <p className="text-xs text-slate-600">
                        {new Date(session.updatedAt).toLocaleDateString('de-DE')}
                      </p>
                    </div>
                    <StatusIcon className={cn(
                      "w-5 h-5",
                      session.status === 'running' && "text-blue-400 animate-spin",
                      session.status === 'complete' && "text-green-400",
                      session.status === 'error' && "text-red-400"
                    )} />
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>

      {/* Features Status */}
      <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Available Features</h2>
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-3">
          {Object.entries(features).map(([name, enabled]) => (
            <div 
              key={name}
              className={cn(
                "p-3 rounded-xl text-center",
                enabled ? "bg-green-500/10 border border-green-500/30" : "bg-dark-border"
              )}
            >
              <div className={cn(
                "w-2 h-2 rounded-full mx-auto mb-2",
                enabled ? "bg-green-500" : "bg-slate-600"
              )} />
              <p className="text-xs text-slate-400 capitalize">
                {name.replace(/_/g, ' ')}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
