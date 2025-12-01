import { useState, useEffect } from 'react'
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
  Clock
} from 'lucide-react'
import { cn } from '../utils/helpers'

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

function PhaseNode({ phase, isLast }: { phase: PipelinePhase; isLast: boolean }) {
  const Icon = phase.icon
  
  const statusStyles = {
    pending: 'bg-dark-border text-slate-500 border-dark-border',
    running: 'bg-blue-500/20 text-blue-400 border-blue-500 animate-pulse',
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
      {/* Node */}
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
        
        {/* Status indicator */}
        <div className="absolute -top-2 -right-2">
          <StatusIcon className={cn(
            "w-5 h-5",
            phase.status === 'running' && "animate-spin"
          )} />
        </div>
        
        {/* Duration */}
        {phase.duration && (
          <div className="absolute -bottom-6 text-xs text-slate-500">
            {phase.duration.toFixed(1)}s
          </div>
        )}
      </motion.div>
      
      {/* Worker info */}
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
  const [phases, setPhases] = useState<PipelinePhase[]>(
    pipelinePhases.map(p => ({ ...p, status: 'pending' as const }))
  )
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)
  const [workers, setWorkers] = useState<any[]>([])

  // Simulate pipeline progress (in real app, this comes from SSE)
  useEffect(() => {
    // Demo: simulate a running pipeline
    const demoSession: ActiveSession = {
      id: 'demo-123',
      name: 'KI-Strategie 2025',
      status: 'running',
      phase: 'draft',
      progress: 37.5,
      slidesGenerated: 3,
      totalSlides: 8,
      startedAt: new Date(Date.now() - 45000).toISOString()
    }
    setActiveSession(demoSession)
    
    // Set demo phase states
    setPhases([
      { ...pipelinePhases[0], status: 'complete', duration: 2.3, worker: 'Worker-1' },
      { ...pipelinePhases[1], status: 'complete', duration: 1.8, worker: 'Worker-1' },
      { ...pipelinePhases[2], status: 'running', worker: 'Worker-2' },
      { ...pipelinePhases[3], status: 'pending' },
      { ...pipelinePhases[4], status: 'pending' },
      { ...pipelinePhases[5], status: 'pending' },
      { ...pipelinePhases[6], status: 'pending' },
      { ...pipelinePhases[7], status: 'pending' },
    ])
    
    setWorkers([
      { name: 'Worker-1', queue: 'analysis', active: 2, status: 'online' },
      { name: 'Worker-2', queue: 'llm', active: 1, status: 'online' },
    ])
  }, [])

  const completedPhases = phases.filter(p => p.status === 'complete').length
  const totalDuration = phases.reduce((sum, p) => sum + (p.duration || 0), 0)

  return (
    <div className="space-y-6">
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
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 rounded-lg">
                <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                <span className="text-sm text-blue-400">Running</span>
              </div>
              <button className="p-2 rounded-lg bg-dark-border hover:bg-dark-bg text-slate-400 hover:text-white transition-colors">
                <Pause className="w-5 h-5" />
              </button>
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
              <p className="text-2xl font-bold text-white">~{((8 - completedPhases) * 2.5).toFixed(0)}s</p>
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
          <h2 className="text-lg font-semibold text-white mb-4">Active Workers</h2>
          <div className="space-y-3">
            {workers.map((worker) => (
              <div key={worker.name} className="flex items-center justify-between p-3 bg-dark-border rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
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
            ))}
          </div>
        </div>

        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Phase Details</h2>
          <div className="space-y-2">
            {phases.filter(p => p.status !== 'pending').map((phase) => {
              const Icon = phase.icon
              return (
                <div key={phase.id} className="flex items-center justify-between p-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-slate-300">{phase.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    {phase.duration && (
                      <span className="text-xs text-slate-500">{phase.duration.toFixed(1)}s</span>
                    )}
                    {phase.status === 'complete' && (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    )}
                    {phase.status === 'running' && (
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* No Active Session State */}
      {!activeSession && (
        <div className="bg-dark-card rounded-2xl border border-dark-border p-12 text-center">
          <Play className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Active Pipeline</h3>
          <p className="text-slate-500 mb-6">Start a new generation to see the pipeline in action</p>
          <button className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all">
            Start New Generation
          </button>
        </div>
      )}
    </div>
  )
}
