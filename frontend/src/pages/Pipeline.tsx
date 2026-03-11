import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, Layout, PenTool, MessageSquare, RefreshCw, Eye, Cpu, Download,
  Play, CheckCircle, Circle, Loader2, AlertCircle, Server, XCircle, ArrowRight
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { cn } from '../utils/helpers'
import { api } from '../services/api'

interface PipelinePhase {
  id: string; name: string; icon: React.ElementType
  status: 'pending' | 'running' | 'complete' | 'error'; duration?: number
}
interface ActiveSession {
  id: string; name: string; status: string; phase: string
  progress: number; slidesGenerated: number; totalSlides: number; startedAt: string
}

const pipelinePhases: Omit<PipelinePhase, 'status' | 'duration'>[] = [
  { id: 'analyze',   name: 'Analyse',   icon: Search },
  { id: 'structure', name: 'Struktur',  icon: Layout },
  { id: 'draft',     name: 'Entwurf',   icon: PenTool },
  { id: 'critique',  name: 'Kritik',    icon: MessageSquare },
  { id: 'revise',    name: 'Revision',  icon: RefreshCw },
  { id: 'visualize', name: 'Visuals',   icon: Eye },
  { id: 'render',    name: 'Rendering', icon: Cpu },
  { id: 'export',    name: 'Export',    icon: Download },
]

// Alle Backend-Phasennamen → UI-Phase-ID mappen
const phaseMapping: Record<string, string> = {
  pending:'analyze', initializing:'analyze', starting:'analyze', init:'analyze',
  analyze:'analyze', analysis:'analyze',
  structure:'structure', structuring:'structure', outline:'structure',
  draft:'draft', drafting:'draft', content:'draft', generate:'draft', generating:'draft',
  critique:'critique', review:'critique', reviewing:'critique',
  revise:'revise', revision:'revise', refine:'revise',
  visualize:'visualize', visual:'visualize', design:'visualize',
  render:'render', rendering:'render', build:'render',
  export:'export', exporting:'export',
  complete:'complete', completed:'complete', done:'complete',
}
const phaseOrder = ['analyze','structure','draft','critique','revise','visualize','render','export']
const mapPhase = (p: string) => phaseMapping[(p||'').toLowerCase()] || 'analyze'

function PhaseNode({ phase }: { phase: PipelinePhase }) {
  const Icon = phase.icon
  const statusStyles = {
    pending: 'bg-dark-border text-slate-500 border-dark-border',
    running: 'bg-blue-500/20 text-blue-400 border-blue-500 shadow-lg shadow-blue-500/20',
    complete: 'bg-green-500/20 text-green-400 border-green-500',
    error: 'bg-red-500/20 text-red-400 border-red-500',
  }
  const StatusIcon = { pending: Circle, running: Loader2, complete: CheckCircle, error: AlertCircle }[phase.status]
  return (
    <div className="flex flex-col items-center">
      <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
        className={cn("relative w-20 h-20 rounded-2xl border-2 flex flex-col items-center justify-center transition-all", statusStyles[phase.status])}>
        <Icon className={cn("w-6 h-6", phase.status === 'running' && "animate-pulse")} />
        <span className="text-xs mt-1 font-medium text-center leading-tight px-1">{phase.name}</span>
        <div className="absolute -top-2 -right-2">
          <StatusIcon className={cn("w-5 h-5", phase.status === 'running' && "animate-spin")} />
        </div>
      </motion.div>
    </div>
  )
}

function ConnectionLine({ status }: { status: 'pending' | 'complete' }) {
  return (
    <div className="flex-1 h-0.5 mx-2 relative">
      <div className="absolute inset-0 bg-dark-border rounded-full" />
      {status === 'complete' && (
        <motion.div initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: 0.5 }}
          className="absolute inset-0 bg-green-500 rounded-full origin-left" />
      )}
    </div>
  )
}

export default function Pipeline() {
  const navigate = useNavigate()
  const [phases, setPhases] = useState<PipelinePhase[]>(pipelinePhases.map(p => ({ ...p, status: 'pending' as const })))
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)
  const [workers, setWorkers] = useState<any[]>([])
  const [recentSessions, setRecentSessions] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const prevStatusRef = useRef<string>('')

  useEffect(() => {
    fetchAll()
    // Adaptives Polling: 1s wenn aktiv, 5s wenn kein laufender Job
    let cancelled = false
    const adaptivePoll = async () => {
      if (cancelled) return
      await fetchAll()
      if (cancelled) return
      // Intervall je nach Status
      const delay = prevStatusRef.current === 'running' ? 1000 : 5000
      pollingRef.current = setTimeout(adaptivePoll, delay) as any
    }
    pollingRef.current = setTimeout(adaptivePoll, 1000) as any
    return () => {
      cancelled = true
      if (pollingRef.current) clearTimeout(pollingRef.current)
    }
  }, [])

  // Auto-redirect zum Editor wenn fertig
  useEffect(() => {
    if (activeSession?.status === 'complete' && prevStatusRef.current === 'running') {
      setTimeout(() => navigate(`/editor?session=${activeSession.id}`), 2000)
    }
    if (activeSession) prevStatusRef.current = activeSession.status
  }, [activeSession?.status])

  const fetchAll = async () => {
    try {
      const response = await fetch('/api/sessions/active')
      if (!response.ok) return
      const sessions = await response.json()
      if (!sessions || sessions.length === 0) {
        setActiveSession(null)
        setRecentSessions([])
        setPhases(pipelinePhases.map(p => ({ ...p, status: 'pending' as const })))
        return
      }
      const sorted = [...sessions].sort((a, b) => {
        const aActive = ['running','starting','initializing'].includes(a.status)
        const bActive = ['running','starting','initializing'].includes(b.status)
        if (aActive && !bActive) return -1
        if (bActive && !aActive) return 1
        return new Date(b.updated_at||b.created_at).getTime() - new Date(a.updated_at||a.created_at).getTime()
      })
      const s = sorted[0]
      setRecentSessions(sorted.filter(x => x.status === 'complete').slice(0, 5))
      setActiveSession({
        id: s.id,
        name: s.config?.project_name || s.config?.company_name || 'Unbenanntes Projekt',
        status: s.status,
        phase: s.phase || 'pending',
        progress: s.progress || 0,
        slidesGenerated: s.slides_generated || 0,
        totalSlides: s.total_slides || 10,
        startedAt: s.created_at
      })
      updatePhases(s.phase, s.status)
    } catch { /* silent */ }
    try {
      const status = await api.getWorkersStatus()
      if (status?.worker_count > 0) setWorkers([{ name: 'Celery Worker', queue: 'default', active: status.worker_count, status: 'online' }])
    } catch { /* silent */ }
  }

  const updatePhases = (rawPhase: string, sessionStatus: string) => {
    const mapped = mapPhase(rawPhase)
    const currentIdx = phaseOrder.indexOf(mapped)
    setPhases(pipelinePhases.map(p => {
      const idx = phaseOrder.indexOf(p.id)
      if (sessionStatus === 'complete') return { ...p, status: 'complete' as const }
      if (sessionStatus === 'error') {
        if (idx < currentIdx) return { ...p, status: 'complete' as const }
        if (idx === currentIdx) return { ...p, status: 'error' as const }
        return { ...p, status: 'pending' as const }
      }
      if (currentIdx === -1) return { ...p, status: idx === 0 ? 'running' as const : 'pending' as const }
      if (idx < currentIdx) return { ...p, status: 'complete' as const }
      if (idx === currentIdx) return { ...p, status: 'running' as const }
      return { ...p, status: 'pending' as const }
    }))
  }

  const completedPhases = phases.filter(p => p.status === 'complete').length
  const isRunning = activeSession && ['running','starting','initializing'].includes(activeSession.status)

  return (
    <div className="space-y-6">
      {error && (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
          <AlertCircle className="w-5 h-5" /><span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto"><XCircle className="w-4 h-4" /></button>
        </div>
      )}

      {/* Active Session Card */}
      {activeSession ? (
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
          className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">{activeSession.name}</h2>
              <p className="text-sm text-slate-500">ID: {activeSession.id}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className={cn("flex items-center gap-2 px-3 py-1.5 rounded-lg border",
                isRunning ? "bg-blue-500/10 border-blue-500/20" :
                activeSession.status === 'complete' ? "bg-green-500/10 border-green-500/20" :
                "bg-red-500/10 border-red-500/20")}>
                {isRunning && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
                {activeSession.status === 'complete' && <CheckCircle className="w-4 h-4 text-green-400" />}
                {activeSession.status === 'error' && <AlertCircle className="w-4 h-4 text-red-400" />}
                <span className={cn("text-sm font-medium",
                  isRunning ? "text-blue-400" :
                  activeSession.status === 'complete' ? "text-green-400" : "text-red-400")}>
                  {isRunning ? 'Läuft...' : activeSession.status === 'complete' ? 'Fertig ✓' : activeSession.status}
                </span>
              </div>
              {activeSession.status === 'complete' && (
                <button onClick={() => navigate(`/editor?session=${activeSession.id}`)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white text-sm font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all">
                  Im Editor öffnen <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Progress */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-400">
                Phase: <span className="text-white font-medium capitalize">
                  {activeSession.phase === 'initializing' ? 'Initialisierung...' : activeSession.phase}
                </span>
              </span>
              <span className="text-white font-medium">{Math.round(activeSession.progress)}%</span>
            </div>
            <div className="h-2 bg-dark-border rounded-full overflow-hidden">
              <motion.div animate={{ width: `${activeSession.progress}%` }} transition={{ duration: 0.5 }}
                className={cn("h-full rounded-full",
                  activeSession.status === 'complete' ? "bg-gradient-to-r from-green-500 to-emerald-500"
                  : "bg-gradient-to-r from-blue-500 to-cyan-500")} />
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-dark-border rounded-xl">
              <p className="text-2xl font-bold text-white">{completedPhases}<span className="text-slate-500 text-base">/{phases.length}</span></p>
              <p className="text-xs text-slate-500">Phasen</p>
            </div>
            <div className="text-center p-3 bg-dark-border rounded-xl">
              <p className="text-2xl font-bold text-white">{activeSession.slidesGenerated}<span className="text-slate-500 text-base">/{activeSession.totalSlides}</span></p>
              <p className="text-xs text-slate-500">Slides</p>
            </div>
            <div className="text-center p-3 bg-dark-border rounded-xl">
              <p className="text-sm font-bold text-white capitalize truncate pt-1">
                {activeSession.status === 'complete' ? '✓ Fertig' : activeSession.phase || '–'}
              </p>
              <p className="text-xs text-slate-500">Aktuelle Phase</p>
            </div>
          </div>

          {activeSession.status === 'complete' && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="text-center text-sm text-green-400 mt-4">
              ✓ Generierung abgeschlossen – wird automatisch zum Editor weitergeleitet...
            </motion.p>
          )}
        </motion.div>
      ) : (
        <div className="bg-dark-card rounded-2xl border border-dark-border p-12 text-center">
          <Play className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Keine aktive Pipeline</h3>
          <p className="text-slate-500 mb-6">Starte eine neue Generierung um die Pipeline zu beobachten</p>
          <button onClick={() => navigate('/generator')}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-medium hover:shadow-lg transition-all">
            Neue Generierung starten
          </button>
        </div>
      )}

      {/* Pipeline Visualization */}
      <div className="bg-dark-card rounded-2xl border border-dark-border p-8">
        <h2 className="text-lg font-semibold text-white mb-8">Pipeline Flow</h2>
        <div className="flex items-center justify-between overflow-x-auto pb-8">
          {phases.map((phase, index) => (
            <div key={phase.id} className="flex items-center">
              <PhaseNode phase={phase} />
              {index < phases.length - 1 && <ConnectionLine status={phase.status === 'complete' ? 'complete' : 'pending'} />}
            </div>
          ))}
        </div>
        <div className="flex items-center justify-center gap-6 pt-4 border-t border-dark-border">
          {[['Ausstehend', Circle, 'text-slate-500'], ['Aktiv', Loader2, 'text-blue-400'], ['Fertig', CheckCircle, 'text-green-400'], ['Fehler', AlertCircle, 'text-red-400']].map(([label, Icon, color]: any) => (
            <div key={label} className="flex items-center gap-2">
              <Icon className={cn("w-4 h-4", color)} />
              <span className="text-xs text-slate-500">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Workers + Recent */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Workers</h2>
            <button onClick={fetchAll} className="p-2 rounded-lg hover:bg-dark-border text-slate-400 hover:text-white transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-dark-border rounded-xl">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <div className="flex-1">
                <p className="text-sm font-medium text-white">API Server</p>
                <p className="text-xs text-slate-500">Port 8011 · aktiv</p>
              </div>
              <Server className="w-4 h-4 text-green-400" />
            </div>
            {workers.map(w => (
              <div key={w.name} className="flex items-center gap-3 p-3 bg-dark-border rounded-xl">
                <div className={cn("w-2 h-2 rounded-full", w.status === 'online' ? "bg-green-500" : "bg-red-500")} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{w.name}</p>
                  <p className="text-xs text-slate-500">{w.active} aktive Tasks</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Letzte Generierungen</h2>
          <div className="space-y-2">
            {recentSessions.length === 0 ? (
              <p className="text-slate-500 text-sm text-center py-4">Noch keine abgeschlossenen Generierungen</p>
            ) : recentSessions.map(s => (
              <button key={s.id} onClick={() => navigate(`/editor?session=${s.id}`)}
                className="w-full flex items-center justify-between p-3 bg-dark-border rounded-xl hover:bg-slate-700/50 transition-colors group">
                <div className="text-left">
                  <p className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors">
                    {s.config?.project_name || s.config?.company_name || 'Unbenannt'}
                  </p>
                  <p className="text-xs text-slate-500">
                    {s.slides_generated || 0} Slides · {new Date(s.updated_at || s.created_at).toLocaleDateString('de-DE')}
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
