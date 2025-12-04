import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Server, 
  Cpu, 
  Database, 
  Workflow,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { api } from '../services/api'
import { cn } from '../utils/helpers'
import RAGStatus from '../components/RAGStatus'

interface ServiceCardProps {
  name: string
  icon: React.ElementType
  status: 'online' | 'warning' | 'offline' | 'loading'
  details: string
  onRestart: () => void
}

function ServiceCard({ name, icon: Icon, status, details, onRestart }: ServiceCardProps) {
  const [isRestarting, setIsRestarting] = useState(false)

  const handleRestart = async () => {
    setIsRestarting(true)
    await onRestart()
    setTimeout(() => setIsRestarting(false), 2000)
  }

  const statusColors = {
    online: 'border-green-500/30 bg-green-500/5',
    warning: 'border-yellow-500/30 bg-yellow-500/5',
    offline: 'border-red-500/30 bg-red-500/5',
    loading: 'border-slate-500/30 bg-slate-500/5',
  }

  const statusIcons = {
    online: <CheckCircle className="w-5 h-5 text-green-500" />,
    warning: <AlertCircle className="w-5 h-5 text-yellow-500" />,
    offline: <XCircle className="w-5 h-5 text-red-500" />,
    loading: <Loader2 className="w-5 h-5 text-slate-500 animate-spin" />,
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "bg-dark-card rounded-2xl p-6 border-2 transition-all",
        statusColors[status]
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-dark-border">
            <Icon className="w-6 h-6 text-slate-300" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{name}</h3>
            <p className="text-sm text-slate-500">{details}</p>
          </div>
        </div>
        {statusIcons[status]}
      </div>

      <div className="mt-4 pt-4 border-t border-dark-border flex items-center justify-between">
        <span className={cn(
          "text-sm font-medium capitalize",
          status === 'online' && "text-green-400",
          status === 'warning' && "text-yellow-400",
          status === 'offline' && "text-red-400",
          status === 'loading' && "text-slate-400"
        )}>
          {status}
        </span>
        <button
          onClick={handleRestart}
          disabled={isRestarting}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all",
            "bg-dark-border hover:bg-dark-bg text-slate-400 hover:text-white",
            isRestarting && "opacity-50 cursor-not-allowed"
          )}
        >
          <RefreshCw className={cn("w-4 h-4", isRestarting && "animate-spin")} />
          {isRestarting ? 'Restarting...' : 'Restart'}
        </button>
      </div>
    </motion.div>
  )
}

export default function Health() {
  const [services, setServices] = useState<any>({
    api: { status: 'loading', details: 'Checking...' },
    ollama: { status: 'loading', details: 'Checking...' },
    redis: { status: 'loading', details: 'Checking...' },
    celery: { status: 'loading', details: 'Checking...' },
  })
  const [features, setFeatures] = useState<any[]>([])
  const [queues, setQueues] = useState<any>({})

  useEffect(() => {
    fetchStatus()
  }, [])

  const fetchStatus = async () => {
    try {
      const [agentStatus, workersStatus, orchestratorStatus] = await Promise.all([
        api.getAgentStatus().catch(() => null),
        api.getWorkersStatus().catch(() => null),
        api.getOrchestratorStatus().catch(() => null),
      ])

      setServices({
        api: {
          status: agentStatus ? 'online' : 'offline',
          details: agentStatus ? `Version ${agentStatus.version}` : 'Not responding'
        },
        ollama: {
          status: agentStatus?.ollama?.ok ? 'online' : 'offline',
          details: agentStatus?.ollama?.ok ? agentStatus.ollama.model : 'Not connected'
        },
        redis: {
          status: workersStatus?.celery_available ? 'online' : 'offline',
          details: workersStatus?.celery_available ? 'Connected' : 'Not connected'
        },
        celery: {
          status: workersStatus?.worker_count > 0 ? 'online' : 'offline',
          details: workersStatus?.worker_count > 0 
            ? `${workersStatus.worker_count} workers active` 
            : 'No workers'
        },
      })

      if (orchestratorStatus?.features) {
        setFeatures(Object.entries(orchestratorStatus.features).map(([name, active]) => ({
          name,
          active
        })))
      }

      if (workersStatus?.queues) {
        setQueues(workersStatus.queues)
      }
    } catch (error) {
      console.error('Failed to fetch status:', error)
    }
  }

  const handleRestart = async (service: string) => {
    try {
      await api.restartService(service)
      setTimeout(fetchStatus, 3000)
    } catch (error) {
      console.error('Failed to restart:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Services Grid */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <ServiceCard
            name="API Server"
            icon={Server}
            status={services.api.status}
            details={services.api.details}
            onRestart={() => handleRestart('api')}
          />
          <ServiceCard
            name="Ollama LLM"
            icon={Cpu}
            status={services.ollama.status}
            details={services.ollama.details}
            onRestart={() => handleRestart('ollama')}
          />
          <ServiceCard
            name="Redis"
            icon={Database}
            status={services.redis.status}
            details={services.redis.details}
            onRestart={() => handleRestart('redis')}
          />
          <ServiceCard
            name="Celery Workers"
            icon={Workflow}
            status={services.celery.status}
            details={services.celery.details}
            onRestart={() => handleRestart('celery')}
          />
        </div>
      </div>

      {/* RAG Knowledge System */}
      <div className="mb-8">
        <RAGStatus />
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Features</h2>
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {features.map((feature) => (
              <div 
                key={feature.name}
                className="flex items-center gap-2"
              >
                <div className={cn(
                  "w-3 h-3 rounded-full",
                  feature.active ? "bg-green-500" : "bg-red-500"
                )} />
                <span className="text-sm text-slate-400 capitalize">
                  {feature.name.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Queues */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Queue Status</h2>
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(queues).map(([name, length]) => (
              <div key={name} className="text-center">
                <div className="text-2xl font-bold text-white">{length as number}</div>
                <div className="text-xs text-slate-500 mt-1">{name}</div>
                <div className="mt-2 h-1 bg-dark-border rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: `${Math.min((length as number) * 10, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <div className="flex justify-center">
        <button
          onClick={fetchStatus}
          className="flex items-center gap-2 px-6 py-3 bg-dark-card rounded-xl border border-dark-border hover:bg-dark-border transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Status
        </button>
      </div>
    </div>
  )
}
