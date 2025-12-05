import { useState, useEffect } from 'react'
import { 
  Activity, Cpu, HardDrive, Database, FileText, 
  TrendingUp, RefreshCw, Brain, Zap
} from 'lucide-react'

interface Metrics {
  system: {
    cpu: { percent: number }
    memory: { percent: number; used_gb: number; total_gb: number }
    disk: { percent: number; free_gb: number }
    process: { memory_mb: number; threads: number }
  }
  knowledge: {
    corpus: { total_chunks: number; files?: { total: number } }
  }
  generation: {
    output: { total_sessions: number; total_slides: number; avg_slides_per_session: number; exports: number }
  }
  learning: {
    templates: { learned: number }
    feedback: { total: number }
  }
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      const res = await fetch('/api/admin/metrics/dashboard')
      const data = await res.json()
      if (data.ok) {
        setMetrics(data)
      }
    } catch (e) {
      console.error('Failed to fetch metrics:', e)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const sys = metrics?.system
  const know = metrics?.knowledge
  const gen = metrics?.generation
  const learn = metrics?.learning

  const MetricCard = ({ icon: Icon, label, value, subValue, color }: any) => (
    <div className="bg-dark-bg rounded-xl p-4 border border-dark-border">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-sm text-gray-400">{label}</p>
          {subValue && <p className="text-xs text-gray-500">{subValue}</p>}
        </div>
      </div>
    </div>
  )

  const ProgressBar = ({ label, value, color }: any) => (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-white font-medium">{value?.toFixed(0) || 0}%</span>
      </div>
      <div className="h-2 bg-dark-border rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${Math.min(value || 0, 100)}%` }}
        />
      </div>
    </div>
  )

  if (loading && !metrics) {
    return (
      <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
        <div className="flex items-center justify-center gap-2 text-gray-400">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Lade Metriken...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-500" />
          Admin Dashboard
        </h2>
        <button 
          onClick={fetchData}
          className="p-2 hover:bg-dark-border rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* System Gauges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-dark-bg rounded-xl p-4 border border-dark-border text-center">
          <div className="text-3xl font-bold text-blue-400">{sys?.cpu?.percent?.toFixed(0) || 0}%</div>
          <div className="text-sm text-gray-400">CPU Auslastung</div>
        </div>
        <div className="bg-dark-bg rounded-xl p-4 border border-dark-border text-center">
          <div className="text-3xl font-bold text-green-400">{sys?.memory?.percent?.toFixed(0) || 0}%</div>
          <div className="text-sm text-gray-400">RAM Nutzung</div>
          <div className="text-xs text-gray-500">{sys?.memory?.used_gb?.toFixed(1) || 0} / {sys?.memory?.total_gb?.toFixed(0) || 0} GB</div>
        </div>
        <div className="bg-dark-bg rounded-xl p-4 border border-dark-border text-center">
          <div className="text-3xl font-bold text-yellow-400">{sys?.disk?.percent?.toFixed(0) || 0}%</div>
          <div className="text-sm text-gray-400">Disk</div>
          <div className="text-xs text-gray-500">{sys?.disk?.free_gb?.toFixed(0) || 0} GB frei</div>
        </div>
        <div className="bg-dark-bg rounded-xl p-4 border border-dark-border text-center">
          <div className="text-3xl font-bold text-purple-400">{sys?.process?.memory_mb || 0} MB</div>
          <div className="text-sm text-gray-400">Prozess RAM</div>
          <div className="text-xs text-gray-500">{sys?.process?.threads || 0} Threads</div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Knowledge & Learning */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Knowledge & Learning
          </h3>
          <div className="space-y-3">
            <MetricCard 
              icon={Database} 
              label="Knowledge Chunks" 
              value={(know?.corpus?.total_chunks || 0).toLocaleString()}
              color="bg-purple-500"
            />
            <MetricCard 
              icon={FileText} 
              label="Knowledge Files" 
              value={(know?.corpus?.files?.total || 0).toLocaleString()}
              color="bg-blue-500"
            />
            <MetricCard 
              icon={TrendingUp} 
              label="Templates gelernt" 
              value={learn?.templates?.learned || 0}
              color="bg-green-500"
            />
          </div>
        </div>

        {/* Generation */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Generierung
          </h3>
          <div className="space-y-3">
            <MetricCard 
              icon={Activity} 
              label="Sessions gesamt" 
              value={gen?.output?.total_sessions || 0}
              color="bg-blue-500"
            />
            <MetricCard 
              icon={FileText} 
              label="Slides generiert" 
              value={(gen?.output?.total_slides || 0).toLocaleString()}
              color="bg-green-500"
            />
            <MetricCard 
              icon={TrendingUp} 
              label="Ø Slides/Session" 
              value={(gen?.output?.avg_slides_per_session || 0).toFixed(1)}
              color="bg-yellow-500"
            />
            <MetricCard 
              icon={HardDrive} 
              label="Exports" 
              value={gen?.output?.exports || 0}
              color="bg-purple-500"
            />
          </div>
        </div>

        {/* Resource Usage */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            Ressourcen-Auslastung
          </h3>
          <div className="space-y-4 bg-dark-bg rounded-xl p-4 border border-dark-border">
            <ProgressBar 
              label="CPU" 
              value={sys?.cpu?.percent} 
              color="bg-blue-500" 
            />
            <ProgressBar 
              label="RAM" 
              value={sys?.memory?.percent ?? 0} 
              color={(sys?.memory?.percent ?? 0) > 80 ? 'bg-red-500' : 'bg-green-500'}
            />
            <ProgressBar 
              label="Disk" 
              value={sys?.disk?.percent ?? 0} 
              color={(sys?.disk?.percent ?? 0) > 90 ? 'bg-red-500' : 'bg-yellow-500'}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
