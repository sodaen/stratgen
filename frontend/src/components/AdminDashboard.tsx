import React, { useState, useEffect } from 'react'
import { 
  Activity, Cpu, HardDrive, Database, Users, FileText, 
  TrendingUp, Clock, RefreshCw, Server, Brain, Zap
} from 'lucide-react'

interface SystemMetrics {
  system: {
    cpu_percent: number
    memory_percent: number
    memory_used_gb: number
    memory_total_gb: number
    disk_percent: number
    disk_free_gb: number
  }
  process: {
    memory_mb: number
    threads: number
  }
  knowledge: {
    total_chunks: number
  }
  activity: {
    sessions: number
    exports: number
  }
}

interface LearningStats {
  knowledge_files: number
  templates_learned: number
  learning_errors: number
}

interface GenerationStats {
  total_sessions: number
  total_slides: number
  avg_slides_per_session: number
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [learning, setLearning] = useState<LearningStats | null>(null)
  const [generation, setGeneration] = useState<GenerationStats | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [metricsRes, learningRes, genRes] = await Promise.all([
        fetch('/api/admin/metrics'),
        fetch('/api/admin/learning/stats'),
        fetch('/api/admin/generation/stats')
      ])
      
      const [metricsData, learningData, genData] = await Promise.all([
        metricsRes.json(),
        learningRes.json(),
        genRes.json()
      ])
      
      if (metricsData.ok) setMetrics(metricsData)
      if (learningData.ok) setLearning(learningData)
      if (genData.ok) setGeneration(genData)
    } catch (e) {
      console.error('Failed to fetch admin metrics:', e)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 30000)
    return () => clearInterval(interval)
  }, [])

  const MetricCard = ({ icon: Icon, label, value, subValue, color }: any) => (
    <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-xs text-gray-400">{label}</p>
          {subValue && <p className="text-xs text-gray-500">{subValue}</p>}
        </div>
      </div>
    </div>
  )

  const ProgressBar = ({ value, color }: { value: number; color: string }) => (
    <div className="w-full bg-dark-bg rounded-full h-2">
      <div 
        className={`h-2 rounded-full ${color}`} 
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  )

  if (loading && !metrics) {
    return <div className="animate-pulse bg-dark-card rounded-xl h-96" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-green-400" />
          Admin Dashboard
        </h2>
        <button
          onClick={fetchAll}
          className="p-2 rounded-lg bg-dark-card hover:bg-dark-border transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={Cpu}
          label="CPU Auslastung"
          value={`${metrics?.system.cpu_percent || 0}%`}
          color="bg-blue-600"
        />
        <MetricCard
          icon={Server}
          label="RAM Nutzung"
          value={`${metrics?.system.memory_percent || 0}%`}
          subValue={`${metrics?.system.memory_used_gb?.toFixed(1) || 0} / ${metrics?.system.memory_total_gb?.toFixed(1) || 0} GB`}
          color="bg-purple-600"
        />
        <MetricCard
          icon={HardDrive}
          label="Disk"
          value={`${metrics?.system.disk_percent || 0}%`}
          subValue={`${metrics?.system.disk_free_gb?.toFixed(0) || 0} GB frei`}
          color="bg-orange-600"
        />
        <MetricCard
          icon={Zap}
          label="Prozess RAM"
          value={`${metrics?.process.memory_mb || 0} MB`}
          subValue={`${metrics?.process.threads || 0} Threads`}
          color="bg-cyan-600"
        />
      </div>

      {/* Knowledge & Generation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Knowledge Stats */}
        <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            Knowledge & Learning
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Knowledge Chunks</span>
              <span className="text-white font-bold text-xl">
                {metrics?.knowledge.total_chunks?.toLocaleString() || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Knowledge Files</span>
              <span className="text-white font-medium">{learning?.knowledge_files || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Templates gelernt</span>
              <span className="text-white font-medium">{learning?.templates_learned || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Lern-Fehler</span>
              <span className={`font-medium ${learning?.learning_errors ? 'text-red-400' : 'text-green-400'}`}>
                {learning?.learning_errors || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Generation Stats */}
        <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            Generierung
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Sessions gesamt</span>
              <span className="text-white font-bold text-xl">{generation?.total_sessions || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Slides generiert</span>
              <span className="text-white font-medium">{generation?.total_slides || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Ø Slides/Session</span>
              <span className="text-white font-medium">{generation?.avg_slides_per_session || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Exports</span>
              <span className="text-white font-medium">{metrics?.activity.exports || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Resource Bars */}
      <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
        <h3 className="text-lg font-medium text-white mb-4">Ressourcen-Auslastung</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-400">CPU</span>
              <span className="text-white">{metrics?.system.cpu_percent || 0}%</span>
            </div>
            <ProgressBar 
              value={metrics?.system.cpu_percent || 0} 
              color={metrics?.system.cpu_percent > 80 ? 'bg-red-500' : 'bg-blue-500'} 
            />
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-400">RAM</span>
              <span className="text-white">{metrics?.system.memory_percent || 0}%</span>
            </div>
            <ProgressBar 
              value={metrics?.system.memory_percent || 0} 
              color={metrics?.system.memory_percent > 80 ? 'bg-red-500' : 'bg-purple-500'} 
            />
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-400">Disk</span>
              <span className="text-white">{metrics?.system.disk_percent || 0}%</span>
            </div>
            <ProgressBar 
              value={metrics?.system.disk_percent || 0} 
              color={metrics?.system.disk_percent > 90 ? 'bg-red-500' : 'bg-orange-500'} 
            />
          </div>
        </div>
      </div>
    </div>
  )
}
