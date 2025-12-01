import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { 
  Search,
  FileText,
  Layout,
  PenTool,
  MessageSquare,
  RefreshCw,
  Eye,
  Cpu,
  Download,
  Play,
  Pause,
  CheckCircle,
  Circle,
  Loader2,
  AlertCircle,
  Server,
  Clock,
  XCircle
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { cn } from '../utils/helpers'
import { api } from '../services/api'

interface PipelinePhase {
  id: string
  name: string
  icon: React.ElementType
  status: 'pending' | 'running' | 'complete' | 'error'
  duration?: number
  worker?: string
}

interface ActiveSession {
  id: string
  name: string
  status: string
  phase: string
  progress: number
  slidesGenerated: number
  totalSlides: number
  startedAt: string
}

const pipelinePhases: Omit<PipelinePhase, 'status' | 'duration' | 'worker'>[] = [
  { id: 'analyze', name: 'Analyze', icon: Search },
  { id: 'structure', name: 'Structure', icon: Layout },
  { id: 'draft', name: 'Draft', icon: PenTool },
  { id: 'critique', name: 'Critique', icon: MessageSquare },
  { id: 'revise', name: 'Revise', icon: RefreshCw },
  { id: 'visualize', name: 'Visualize', icon: Eye },
  { id: 'render', name: 'Render', icon: Cpu },
  { id: 'export', name: 'Export', icon: Download },
]

const phaseOrder = ['analyze', 'structure', 'draft', 'critique', 'revise', 'visualize', 'render', 'export']

function PhaseNode({ phase, isLast }: { phase: PipelinePhase; isLast: boolean }) {
  const Icon = phase.icon
  
  const statusStyles = {
    pending: 'bg-dark-border text-slate-500 border-dark-border',
    running: 'bg-blue-500/20 text-blue-400 border-blue-500',
    complete: 'bg-green-500/20 text-green-400 border-green-500',
    error: 'bg-red-500/20 text-red-400 border-red-500',
  }
  
  const statusIcons = {
    pending: Circle,
    running: Loader2,
    complete: CheckCircle,
    error: AlertCircle,
  }
  
  const StatusIcon = statusIcons[phase.status]
  
  return (
    <div className="flex flex-col items-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={cn(
          "relative w-20 h-20 rounded-2xl border-2 flex flex-col items-center justify-center transition-all",
          statusStyles[phase.status]
        )}
      >
        <Icon className={cn("w-6 h-6", phase.status === 'running' && "animate-pulse")} />
        <span className="text-xs mt-1 font-medium">{phase.name}</span>
        
        <div className="absolute -top-2 -right-2">
          <StatusIcon className={cn(
            "w-5 h-5",
            phase.status === 'running' && "animate-spin"
          )} />
        </div>
        
        {phase.duration !== undefined && phase.duration > 0 && (
          <div className="absolute -bottom-6 text-xs text-slate-500">
            {phase.duration.toFixed(1)}s
          </div>
        )}
      </motion.div>
      
      {phase.worker && (
        <div className="mt-8 text-xs text-slate-600 flex items-center gap-1">
          <Server className="w-3 h-3" />
          {phase.worker}
        </div>
      )}
    </div>
  )
}

function ConnectionLine({ status }: { status: 'pending' | 'complete' }) {
  return (
    <div className="flex-1 h-0.5 mx-2 relative">
      <div className="absolute inset-0 bg-dark-border rounded-full" />
      {status === 'complete' && (
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.5 }}
          className="absolute inset-0 bg-green-500 rounded-full origin-left"
        />
      )}
    </div>
  )
}

export default function Pipeline() {
  const navigate = useNavigate()
  const [phases, setPhases] = useState<PipelinePhase[]>(
    pipelinePhases.map(p => ({ ...p, status: 'pending' as const }))
  )
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)
  const [workers, setWorkers] = useState<any[]>([])
  const [eventSource, setEventSource] = useState<EventSource | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch active sessions on mount
  useEffect(() => {
    const fetchActiveSessions = async () => {
      try {
        const sessions = await api.getActiveSessions?.() || []
        if (sessions.length > 0) {
          const session = sessions[0]
          setActiveSession({
            id: session.id,
            name: session.config?.project_name || 'Unnamed Project',
            status: session.status,
            phase: session.phase,
            progress: session.progress || 0,
            slidesGenerated: session.slides_generated || 0,
            totalSlides: session.total_slides || 10,
            startedAt: session.created_at
          })
          
          // Connect to SSE if session is running
          if (session.status === 'running') {
            connectToSSE(session.id)
          }
        }
      } catch (err) {
        console.log('No active sessions')
      }
    }
    
    fetchActiveSessions()
    
    // Also fetch worker status
    fetchWorkerStatus()
    
    return () => {
      if (eventSource) {
        eventSource.close()
      }
    }
  }, [])

  const fetchWorkerStatus = async () => {
    try {
      const status = await api.getWorkersStatus()
      if (status?.workers) {
        setWorkers(Object.entries(status.workers).map(([name, info]: [string, any]) => ({
          name,
          queue: info.queues?.join(', ') || 'default',
          active: info.active || 0,
          status: 'online'
        })))
      }
    } catch (err) {
      console.error('Failed to fetch worker status:', err)
    }
  }

  const connectToSSE = useCallback((generationId: string) => {
    if (eventSource) {
      eventSource.close()
    }

    const es = new EventSource(`/api/live/stream/${generationId}`)
    
    es.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleSSEEvent(data)
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }

    es.onerror = (err) => {
      console.error('SSE error:', err)
      setIsConnected(false)
      setError('Connection lost. Reconnecting...')
      
      // Reconnect after 3 seconds
      setTimeout(() => {
        if (activeSession?.status === 'running') {
          connectToSSE(generationId)
        }
      }, 3000)
    }

    setEventSource(es)
  }, [eventSource, activeSession])

  const handleSSEEvent = (data: any) => {
    console.log('SSE Event:', data)
    
    switch (data.type) {
      case 'phase_start':
        updatePhaseStatus(data.phase, 'running')
        break
        
      case 'phase_complete':
        updatePhaseStatus(data.phase, 'complete', data.duration)
        break
        
      case 'phase_error':
        updatePhaseStatus(data.phase, 'error')
        setError(data.error || 'An error occurred')
        break
        
      case 'slide_generated':
        setActiveSession(prev => prev ? {
          ...prev,
          slidesGenerated: (prev.slidesGenerated || 0) + 1
        } : null)
        break
        
      case 'progress':
        setActiveSession(prev => prev ? {
          ...prev,
          progress: data.progress,
          phase: data.phase
        } : null)
        break
        
      case 'complete':
        setActiveSession(prev => prev ? {
          ...prev,
          status: 'complete',
          progress: 100
        } : null)
        setPhases(prev => prev.map(p => ({ ...p, status: 'complete' as const })))
        break
        
      case 'error':
        setActiveSession(prev => prev ? {
          ...prev,
          status: 'error'
        } : null)
        setError(data.error || 'Generation failed')
        break
    }
  }

  const updatePhaseStatus = (phaseId: string, status: 'running' | 'complete' | 'error', duration?: number) => {
    setPhases(prev => prev.map(p => {
      if (p.id === phaseId) {
        return { ...p, status, duration }
      }
      // Mark previous phases as complete
      const currentIndex = phaseOrder.indexOf(phaseId)
      const thisIndex = phaseOrder.indexOf(p.id)
      if (thisIndex < currentIndex && p.status !== 'complete') {
        return { ...p, status: 'complete' as const }
      }
      return p
    }))
  }

  const handleStopGeneration = async () => {
    if (eventSource) {
      eventSource.close()
      setEventSource(null)
    }
    setIsConnected(false)
    setActiveSession(prev => prev ? { ...prev, status: 'stopped' } : null)
  }

  const completedPhases = phases.filter(p => p.status === 'complete').length
  const totalDuration = phases.reduce((sum, p) => sum + (p.duration || 0), 0)

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      {activeSession && (
        <div className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-lg text-sm",
          isConnected ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"
        )}>
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500 animate-pulse" : "bg-yellow-500"
          )} />
          {isConnected ? "Live connected to generation stream" : "Connecting to stream..."}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400"
        >
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button 
            onClick={() => setError(null)}
            className="ml-auto p-1 hover:bg-red-500/20 rounded"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </motion.div>
      )}

      {/* Active Session Info */}
      {activeSession && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-card rounded-2xl border border-dark-border p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">{activeSession.name}</h2>
              <p className="text-sm text-slate-500">Session: {activeSession.id}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-lg",
                activeSession.status === 'running' ? "bg-blue-500/20" :
                activeSession.status === 'complete' ? "bg-green-500/20" :
                activeSession.status === 'error' ? "bg-red-500/20" :
                "bg-slate-500/20"
              )}>
                {activeSession.status === 'running' && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
                {activeSession.status === 'complete' && <CheckCircle className="w-4 h-4 text-green-400" />}
                {activeSession.status === 'error' && <AlertCircle className="w-4 h-4 text-red-400" />}
                <span className={cn(
                  "text-sm capitalize",
                  activeSession.status === 'running' ? "text-blue-400" :
                  activeSession.status === 'complete' ? "text-green-400" :
                  activeSession.status === 'error' ? "text-red-400" :
                  "text-slate-400"
                )}>
                  {activeSession.status}
                </span>
              </div>
              {activeSession.status === 'running' && (
                <button 
                  onClick={handleStopGeneration}
                  className="p-2 rounded-lg bg-dark-border hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                >
                  <Pause className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-400">Overall Progress</span>
              <span className="text-white font-medium">{activeSession.progress.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-dark-border rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${activeSession.progress}%` }}
                transition={{ duration: 0.5 }}
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
              />
            </div>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 bg-dark-border rounded-xl">
              <p className="text-2xl font-bold text-white">{completedPhases}/{phases.length}</p>
              <p className="text-xs text-slate-500">Phases</p>
            </div>
            <div className="text-center p-3 bg-dark-border rounded-xl">
              <p className="text-2xl font-bold text-white">{activeSession.slidesGenerated}/{activeSession.totalSlides}</p>
              <p className="text-xs text-slate-500">Slides</p>
            </div>
            <div className="text-center p-3 bg-dark-border rounded-xl">
              <p className="text-2xl font-bold text-white">{totalDuration.toFixed(1)}s</p>
              <p className="text-xs text-slate-500">Elapsed</p>
            </div>
            <div className="text-center p-3 bg-dark-border rounded-xl">
              <p className="text-2xl font-bold text-white">
                {activeSession.status === 'complete' ? '0s' : `~${Math.max(0, (8 - completedPhases) * 2.5).toFixed(0)}s`}
              </p>
              <p className="text-xs text-slate-500">ETA</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Pipeline Visualization */}
      <div className="bg-dark-card rounded-2xl border border-dark-border p-8">
        <h2 className="text-lg font-semibold text-white mb-8">Pipeline Flow</h2>
        
        <div className="flex items-center justify-between overflow-x-auto pb-8">
          {phases.map((phase, index) => (
            <div key={phase.id} className="flex items-center">
              <PhaseNode phase={phase} isLast={index === phases.length - 1} />
              {index < phases.length - 1 && (
                <ConnectionLine 
                  status={phase.status === 'complete' ? 'complete' : 'pending'} 
                />
              )}
            </div>
          ))}
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-center gap-6 pt-4 border-t border-dark-border">
          <div className="flex items-center gap-2">
            <Circle className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-500">Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-slate-500">Running</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-xs text-slate-500">Complete</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-xs text-slate-500">Error</span>
          </div>
        </div>
      </div>

      {/* Workers Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Active Workers</h2>
            <button 
              onClick={fetchWorkerStatus}
              className="p-2 rounded-lg hover:bg-dark-border text-slate-400 hover:text-white transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3">
            {workers.length === 0 ? (
              <p className="text-slate-500 text-sm text-center py-4">No workers detected</p>
            ) : (
              workers.map((worker) => (
                <div key={worker.name} className="flex items-center justify-between p-3 bg-dark-border rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      worker.status === 'online' ? "bg-green-500" : "bg-red-500"
                    )} />
                    <div>
                      <p className="text-sm font-medium text-white">{worker.name}</p>
                      <p className="text-xs text-slate-500">Queue: {worker.queue}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-white">{worker.active} tasks</p>
                    <p className="text-xs text-slate-500">active</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Phase Details</h2>
          <div className="space-y-2">
            {phases.filter(p => p.status !== 'pending').length === 0 ? (
              <p className="text-slate-500 text-sm text-center py-4">No phases started yet</p>
            ) : (
              phases.filter(p => p.status !== 'pending').map((phase) => {
                const Icon = phase.icon
                return (
                  <div key={phase.id} className="flex items-center justify-between p-2">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-slate-400" />
                      <span className="text-sm text-slate-300">{phase.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      {phase.duration !== undefined && phase.duration > 0 && (
                        <span className="text-xs text-slate-500">{phase.duration.toFixed(1)}s</span>
                      )}
                      {phase.status === 'complete' && (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      )}
                      {phase.status === 'running' && (
                        <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                      )}
                      {phase.status === 'error' && (
                        <AlertCircle className="w-4 h-4 text-red-400" />
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>

      {/* No Active Session State */}
      {!activeSession && (
        <div className="bg-dark-card rounded-2xl border border-dark-border p-12 text-center">
          <Play className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Active Pipeline</h3>
          <p className="text-slate-500 mb-6">Start a new generation to see the pipeline in action</p>
          <button 
            onClick={() => navigate('/generator')}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all"
          >
            Start New Generation
          </button>
        </div>
      )}
    </div>
  )
}
