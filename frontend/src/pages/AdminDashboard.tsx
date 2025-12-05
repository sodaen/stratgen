import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Activity, Cpu, HardDrive, Database, Server, Clock,
  TrendingUp, TrendingDown, Zap, Brain, Users, FileText,
  AlertTriangle, CheckCircle, XCircle, RefreshCw, BarChart3,
  Layers, MessageSquare, BookOpen, GitBranch
} from 'lucide-react'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts'

interface DashboardData {
  system: any
  services: any
  knowledge: any
  generation: any
  learning: any
  history: any[]
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/metrics/dashboard')
      const json = await res.json()
      if (json.ok) {
        setData(json)
        setLastUpdate(new Date())
      }
    } catch (e) {
      console.error('Failed to fetch metrics:', e)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchData()
    if (autoRefresh) {
      const interval = setInterval(fetchData, 30000) // 30s refresh
      return () => clearInterval(interval)
    }
  }, [fetchData, autoRefresh])

  // Format helpers
  const formatBytes = (gb: number) => `${gb.toFixed(1)} GB`
  const formatPercent = (p: number) => `${p.toFixed(1)}%`
  const formatMs = (ms: number) => `${ms.toFixed(0)}ms`
  const formatNumber = (n: number) => n?.toLocaleString() || '0'

  // Gauge component
  const Gauge = ({ value, max = 100, color, label }: any) => {
    const percent = Math.min((value / max) * 100, 100)
    const circumference = 2 * Math.PI * 40
    const strokeDashoffset = circumference - (percent / 100) * circumference
    
    return (
      <div className="relative w-24 h-24">
        <svg className="w-full h-full transform -rotate-90">
          <circle cx="48" cy="48" r="40" stroke="#1e293b" strokeWidth="8" fill="none" />
          <circle
            cx="48" cy="48" r="40"
            stroke={color}
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-bold text-white">{value.toFixed(0)}%</span>
          <span className="text-xs text-gray-400">{label}</span>
        </div>
      </div>
    )
  }

  // Service status badge
  const ServiceBadge = ({ name, status, details }: any) => {
    const isOnline = status === 'online'
    return (
      <div className={`flex items-center gap-3 p-3 rounded-lg border ${
        isOnline ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'
      }`}>
        <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
        <div className="flex-1">
          <div className="font-medium text-white">{name}</div>
          <div className="text-xs text-gray-400">{details}</div>
        </div>
        {isOnline ? (
          <CheckCircle className="w-5 h-5 text-green-500" />
        ) : (
          <XCircle className="w-5 h-5 text-red-500" />
        )}
      </div>
    )
  }

  // Stat card
  const StatCard = ({ icon: Icon, label, value, subValue, trend, color = 'blue' }: any) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-dark-card rounded-xl p-4 border border-dark-border"
    >
      <div className="flex items-start justify-between">
        <div className={`p-2 rounded-lg bg-${color}-500/10`}>
          <Icon className={`w-5 h-5 text-${color}-500`} />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-xs ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm text-gray-400">{label}</div>
        {subValue && <div className="text-xs text-gray-500 mt-1">{subValue}</div>}
      </div>
    </motion.div>
  )

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null
    return (
      <div className="bg-dark-card border border-dark-border rounded-lg p-3 shadow-xl">
        <p className="text-gray-400 text-xs mb-1">{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} className="text-white font-medium" style={{ color: p.color }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
          </p>
        ))}
      </div>
    )
  }

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    )
  }

  const sys = data?.system
  const svc = data?.services || {}
  const know = data?.knowledge || {}
  const gen = data?.generation || {}
  const learn = data?.learning || {}
  const history = data?.history || []

  // Prepare chart data
  const historyData = history.map((h: any) => ({
    time: new Date(h.timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
    cpu: h.cpu,
    memory: h.memory,
    api_ms: h.api_ms > 0 ? h.api_ms : null
  }))

  const knowledgeDistribution = Object.entries(know?.corpus?.collections || {}).map(([name, info]: any) => ({
    name: name.replace('stratgen_', ''),
    value: info.points
  }))

  const feedbackData = learn?.feedback ? [
    { name: 'Positiv', value: learn.feedback.positive, color: '#10B981' },
    { name: 'Neutral', value: learn.feedback.neutral, color: '#F59E0B' },
    { name: 'Negativ', value: learn.feedback.negative, color: '#EF4444' }
  ] : []

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <BarChart3 className="w-7 h-7 text-blue-500" />
            Admin Dashboard
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            System-Metriken, Quality Scores & Analytics
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded bg-dark-bg border-dark-border"
            />
            Auto-Refresh
          </label>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-dark-card hover:bg-dark-border rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {lastUpdate && (
            <span className="text-xs text-gray-500">
              Aktualisiert: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* System Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-dark-card rounded-xl p-6 border border-dark-border flex items-center justify-around"
        >
          <Gauge value={sys?.cpu?.percent || 0} color="#3B82F6" label="CPU" />
          <div className="text-sm text-gray-400">
            <div>{sys?.cpu?.cores} Cores</div>
            <div>Load: {sys?.cpu?.load_1m?.toFixed(2)}</div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-dark-card rounded-xl p-6 border border-dark-border flex items-center justify-around"
        >
          <Gauge 
            value={sys?.memory?.percent || 0} 
            color={sys?.memory?.percent > 80 ? '#EF4444' : '#10B981'} 
            label="RAM" 
          />
          <div className="text-sm text-gray-400">
            <div>{formatBytes(sys?.memory?.used_gb || 0)}</div>
            <div>/ {formatBytes(sys?.memory?.total_gb || 0)}</div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-dark-card rounded-xl p-6 border border-dark-border flex items-center justify-around"
        >
          <Gauge 
            value={sys?.disk?.percent || 0} 
            color={sys?.disk?.percent > 90 ? '#EF4444' : '#F59E0B'} 
            label="Disk" 
          />
          <div className="text-sm text-gray-400">
            <div>{formatBytes(sys?.disk?.free_gb || 0)} frei</div>
            <div>/ {formatBytes(sys?.disk?.total_gb || 0)}</div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="bg-dark-card rounded-xl p-6 border border-dark-border flex items-center justify-around"
        >
          <Gauge value={(sys?.process?.memory_mb || 0) / 10} max={100} color="#8B5CF6" label="Process" />
          <div className="text-sm text-gray-400">
            <div>{sys?.process?.memory_mb} MB</div>
            <div>{sys?.process?.threads} Threads</div>
          </div>
        </motion.div>
      </div>

      {/* Services Status */}
      <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-blue-500" />
          Service Status
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <ServiceBadge
            name="API Server"
            status={svc.api?.status}
            details={svc.api?.response_ms ? `${svc.api.response_ms}ms` : 'Offline'}
          />
          <ServiceBadge
            name="Ollama LLM"
            status={svc.ollama?.status}
            details={svc.ollama?.model_count ? `${svc.ollama.model_count} Models` : 'Offline'}
          />
          <ServiceBadge
            name="Qdrant"
            status={svc.qdrant?.status}
            details={svc.qdrant?.total_points ? `${formatNumber(svc.qdrant.total_points)} Points` : 'Offline'}
          />
          <ServiceBadge
            name="Redis"
            status={svc.redis?.status}
            details={svc.redis?.used_memory_mb ? `${svc.redis.used_memory_mb} MB` : 'Offline'}
          />
          <ServiceBadge
            name="Celery"
            status={svc.celery?.status}
            details={svc.celery?.workers ? `${svc.celery.workers} Workers` : 'No workers'}
          />
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System History Chart */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-500" />
            System-Auslastung (24h)
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={historyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cpu" name="CPU" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.2} />
                <Area type="monotone" dataKey="memory" name="RAM" stroke="#10B981" fill="#10B981" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Knowledge Distribution */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-purple-500" />
            Knowledge Verteilung
          </h2>
          <div className="h-64 flex items-center justify-center">
            {knowledgeDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={knowledgeDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${formatNumber(value)}`}
                  >
                    {knowledgeDistribution.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500">Keine Daten</p>
            )}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard
          icon={Layers}
          label="Knowledge Chunks"
          value={formatNumber(know?.corpus?.total_chunks || 0)}
          color="purple"
        />
        <StatCard
          icon={FileText}
          label="Sessions"
          value={formatNumber(gen?.output?.total_sessions || 0)}
          color="blue"
        />
        <StatCard
          icon={GitBranch}
          label="Slides generiert"
          value={formatNumber(gen?.output?.total_slides || 0)}
          color="green"
        />
        <StatCard
          icon={BookOpen}
          label="Templates"
          value={formatNumber(learn?.templates?.learned || 0)}
          color="yellow"
        />
        <StatCard
          icon={MessageSquare}
          label="Feedbacks"
          value={formatNumber(learn?.feedback?.total || 0)}
          subValue={`${learn?.feedback?.satisfaction_rate || 0}% positiv`}
          color="pink"
        />
        <StatCard
          icon={Zap}
          label="Exports"
          value={formatNumber(gen?.output?.exports || 0)}
          color="orange"
        />
      </div>

      {/* Quality & Feedback Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* RAG Quality */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-500" />
            RAG Quality
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Ø Top-Score</span>
              <span className="text-white font-bold text-xl">
                {know?.retrieval?.avg_top_score?.toFixed(2) || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Hit-Rate (&gt;0.6)</span>
              <span className="text-white font-bold">
                {know?.retrieval?.hit_rate || 0}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Ø Latenz</span>
              <span className="text-white font-bold">
                {know?.retrieval?.avg_latency_ms?.toFixed(0) || 0}ms
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Suchen (24h)</span>
              <span className="text-white font-bold">
                {know?.retrieval?.searches_24h || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Feedback Distribution */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-pink-500" />
            Feedback Verteilung
          </h2>
          <div className="h-48">
            {feedbackData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={feedbackData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                    dataKey="value"
                  >
                    {feedbackData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                Noch keine Feedbacks
              </div>
            )}
          </div>
        </div>

        {/* Generation Performance */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-500" />
            Generation Performance
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Ø Slides/Session</span>
              <span className="text-white font-bold text-xl">
                {gen?.output?.avg_slides_per_session || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Ø Quality Score</span>
              <span className="text-white font-bold">
                {gen?.quality?.avg_quality_score || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Ø Duration</span>
              <span className="text-white font-bold">
                {gen?.performance?.avg_duration_ms ? `${(gen.performance.avg_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Generierungen (7d)</span>
              <span className="text-white font-bold">
                {gen?.quality?.generations_7d || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-gray-400" />
          Letzte Sessions
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-dark-border">
                <th className="pb-3">Session ID</th>
                <th className="pb-3">Slides</th>
                <th className="pb-3">Erstellt</th>
              </tr>
            </thead>
            <tbody>
              {(gen?.output?.recent_sessions || []).slice(0, 5).map((s: any, i: number) => (
                <tr key={i} className="border-b border-dark-border/50">
                  <td className="py-3 font-mono text-sm text-gray-300">{s.id?.slice(0, 12)}...</td>
                  <td className="py-3 text-white">{s.slides}</td>
                  <td className="py-3 text-gray-400 text-sm">
                    {s.created ? new Date(s.created).toLocaleString('de-DE') : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
