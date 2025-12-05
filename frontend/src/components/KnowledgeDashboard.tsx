import { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ComposedChart
} from 'recharts'
import {
  Database, Search, TrendingUp, Clock, FileText, RefreshCw, 
  Zap, Target, Activity, BookOpen, Star, AlertTriangle,
  CheckCircle, XCircle, BarChart2, PieChartIcon, Filter
} from 'lucide-react'

// Types
interface DashboardData {
  overview: any
  search: any
  optimization: any
  ingestion: any
  quality: any
  learning: any
}

const COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e']
const QUALITY_COLORS = { high: '#22c55e', medium: '#eab308', low: '#ef4444' }

// Tab Configuration
const TABS = [
  { id: 'overview', label: 'Overview', icon: Database },
  { id: 'search', label: 'Search Performance', icon: Search },
  { id: 'optimization', label: 'Score-Optimierung', icon: TrendingUp },
  { id: 'ingestion', label: 'Ingestion Monitor', icon: FileText },
  { id: 'quality', label: 'Material Quality', icon: Star },
  { id: 'learning', label: 'Self-Learning', icon: BookOpen },
]

export default function KnowledgeDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [timeRange, setTimeRange] = useState(24)

  const fetchData = async () => {
    try {
      const res = await fetch(`/api/knowledge/analytics/dashboard/all?hours=${timeRange}`)
      const json = await res.json()
      if (json.ok) {
        setData(json)
      }
    } catch (e) {
      console.error('Failed to fetch analytics:', e)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [timeRange])

  // Components
  const MetricCard = ({ icon: Icon, label, value, subValue, color, trend }: any) => (
    <div className="bg-dark-card rounded-xl p-4 border border-dark-border hover:border-primary/50 transition-all">
      <div className="flex items-center gap-3">
        <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-sm text-gray-400">{label}</p>
          {subValue && <p className="text-xs text-primary">{subValue}</p>}
        </div>
        {trend !== undefined && (
          <div className={`text-sm font-medium ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  )

  const ScoreIndicator = ({ score, label }: { score: number, label: string }) => {
    const color = score >= 0.75 ? 'text-green-400' : score >= 0.5 ? 'text-yellow-400' : 'text-red-400'
    const bg = score >= 0.75 ? 'bg-green-400/20' : score >= 0.5 ? 'bg-yellow-400/20' : 'bg-red-400/20'
    return (
      <div className={`${bg} rounded-lg p-3 text-center`}>
        <div className={`text-3xl font-bold ${color}`}>{score.toFixed(2)}</div>
        <div className="text-sm text-gray-400">{label}</div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-primary" />
        <span className="ml-3 text-gray-400">Lade Analytics...</span>
      </div>
    )
  }

  // ============================================================
  // DASHBOARD 1: OVERVIEW
  // ============================================================
  const renderOverview = () => {
    const o = data?.overview
    if (!o) return null

    const pieData = o.collections || []
    const trendData = o.trend_data || []
    const qualityDist = o.quality_distribution?.buckets || []

    return (
      <div className="space-y-6">
        {/* Top Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Database}
            label="Total Chunks"
            value={o.total_chunks?.value?.toLocaleString() || 0}
            trend={o.total_chunks?.trend_percent}
            color="bg-indigo-600"
          />
          <MetricCard
            icon={FileText}
            label="Collections"
            value={pieData.length}
            subValue="Aktive Collections"
            color="bg-violet-600"
          />
          <MetricCard
            icon={Star}
            label="Avg Quality"
            value={o.quality_distribution?.avg?.toFixed(2) || '0.00'}
            subValue={`Median: ${o.quality_distribution?.median?.toFixed(2) || '0.00'}`}
            color="bg-purple-600"
          />
          <MetricCard
            icon={Clock}
            label="Letzte Ingestion"
            value={o.last_ingestion?.ts?.slice(11, 16) || 'N/A'}
            subValue={o.last_ingestion?.source?.slice(0, 30) || ''}
            color="bg-fuchsia-600"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chunks per Collection - Pie */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <PieChartIcon className="w-5 h-5 text-primary" />
              Chunks per Collection
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }) => `${name.split('_')[0]}: ${value}`}
                >
                  {pieData.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Quality Score Distribution - Histogram */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-primary" />
              Quality Score Distribution
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={qualityDist}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="range" tick={{ fill: '#888' }} />
                <YAxis tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trend Line */}
        {trendData.length > 0 && (
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Chunks Trend
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="time" tick={{ fill: '#888' }} />
                <YAxis tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Area type="monotone" dataKey="chunks" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    )
  }

  // ============================================================
  // DASHBOARD 2: SEARCH PERFORMANCE
  // ============================================================
  const renderSearch = () => {
    const s = data?.search
    if (!s) return null

    return (
      <div className="space-y-6">
        {/* Top Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Search}
            label="Total Searches"
            value={s.total_searches}
            color="bg-indigo-600"
          />
          <MetricCard
            icon={Target}
            label="Avg Score"
            value={s.avg_score?.toFixed(3) || '0.000'}
            subValue={s.avg_score >= 0.75 ? '✓ Ziel erreicht' : '↑ Ziel: 0.75'}
            color="bg-violet-600"
          />
          <MetricCard
            icon={Clock}
            label="P50 Latency"
            value={`${s.latency_percentiles?.p50 || 0}ms`}
            subValue={`P95: ${s.latency_percentiles?.p95 || 0}ms`}
            color="bg-purple-600"
          />
          <MetricCard
            icon={Zap}
            label="P99 Latency"
            value={`${s.latency_percentiles?.p99 || 0}ms`}
            color="bg-fuchsia-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Score Trend */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Score Trend</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={s.score_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="hour" tick={{ fill: '#888' }} />
                <YAxis domain={[0, 1]} tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Line type="monotone" dataKey="avg_score" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Score Distribution */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Score Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={s.score_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="range" tick={{ fill: '#888' }} />
                <YAxis tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Searches per Hour */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Searches per Hour</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={s.searches_per_hour || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="hour" tick={{ fill: '#888' }} />
                <YAxis tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Recent Searches */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Searches</h3>
            <div className="space-y-2 max-h-[250px] overflow-y-auto">
              {(s.recent || []).slice(-10).reverse().map((search: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 bg-dark-bg rounded">
                  <span className="text-white truncate flex-1">{search.query}</span>
                  <span className={`ml-2 font-mono ${search.score >= 0.75 ? 'text-green-400' : 'text-yellow-400'}`}>
                    {search.score.toFixed(2)}
                  </span>
                  <span className="ml-2 text-gray-500 text-sm">{search.latency_ms}ms</span>
                </div>
              ))}
              {(!s.recent || s.recent.length === 0) && (
                <p className="text-gray-500 text-center py-8">Keine Suchen aufgezeichnet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================
  // DASHBOARD 3: SCORE OPTIMIZATION
  // ============================================================
  const renderOptimization = () => {
    const o = data?.optimization
    if (!o) return null

    const comparison = o.rerank_comparison || {}

    return (
      <div className="space-y-6">
        {/* Re-Ranking Comparison */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Re-Ranking Vergleich</h3>
          <div className="grid grid-cols-3 gap-8">
            <ScoreIndicator score={comparison.before_avg || 0} label="Vor Re-Ranking" />
            <div className="flex flex-col items-center justify-center">
              <div className={`text-4xl font-bold ${(comparison.improvement || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {comparison.improvement >= 0 ? '+' : ''}{((comparison.improvement || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400">Verbesserung</div>
              <div className="text-sm text-gray-500 mt-1">{comparison.samples || 0} Samples</div>
            </div>
            <ScoreIndicator score={comparison.after_avg || 0} label="Nach Re-Ranking" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Score by Query Type */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Score by Query Type</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={o.score_by_type || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis type="number" domain={[0, 1]} tick={{ fill: '#888' }} />
                <YAxis type="category" dataKey="type" tick={{ fill: '#888' }} width={100} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Bar dataKey="avg_score" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Improvement Trend */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Score Improvement Trend</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={o.improvement_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="date" tick={{ fill: '#888' }} />
                <YAxis domain={[0, 1]} tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Line type="monotone" dataKey="avg_score" stroke="#22c55e" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================
  // DASHBOARD 4: INGESTION MONITOR
  // ============================================================
  const renderIngestion = () => {
    const i = data?.ingestion
    if (!i) return null

    return (
      <div className="space-y-6">
        {/* Top Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={FileText}
            label="Files Processed"
            value={i.total_files}
            color="bg-indigo-600"
          />
          <MetricCard
            icon={CheckCircle}
            label="Chunks Created"
            value={i.chunks_created?.toLocaleString()}
            color="bg-green-600"
          />
          <MetricCard
            icon={XCircle}
            label="Chunks Rejected"
            value={i.chunks_rejected?.toLocaleString()}
            color="bg-red-600"
          />
          <MetricCard
            icon={Target}
            label="Success Rate"
            value={`${i.success_rate}%`}
            color="bg-violet-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Ingestions - Stacked Bar */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Daily Ingestions</h3>
            <ResponsiveContainer width="100%" height={250}>
              <ComposedChart data={i.daily_ingestions || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="date" tick={{ fill: '#888' }} />
                <YAxis tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Bar dataKey="created" stackId="a" fill="#22c55e" name="Created" />
                <Bar dataKey="rejected" stackId="a" fill="#ef4444" name="Rejected" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Rejection Reasons - Pie */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Rejection Reasons</h3>
            {(i.rejection_reasons || []).length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={i.rejection_reasons}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="count"
                    label={({ reason, count }) => `${reason}: ${count}`}
                  >
                    {(i.rejection_reasons || []).map((_: any, idx: number) => (
                      <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-gray-500">
                Keine Rejections
              </div>
            )}
          </div>

          {/* Duration Trend */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border lg:col-span-2">
            <h3 className="text-lg font-semibold text-white mb-4">Ingestion Duration</h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={i.duration_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="time" tick={{ fill: '#888' }} />
                <YAxis tick={{ fill: '#888' }} />
                <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                <Area type="monotone" dataKey="duration_ms" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================
  // DASHBOARD 5: MATERIAL QUALITY
  // ============================================================
  const renderQuality = () => {
    const q = data?.quality
    if (!q) return null

    return (
      <div className="space-y-6">
        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={FileText}
            label="Total Sources"
            value={q.total_sources}
            color="bg-indigo-600"
          />
          <MetricCard
            icon={Star}
            label="Avg Quality"
            value={q.avg_quality_overall?.toFixed(3)}
            color="bg-violet-600"
          />
          <MetricCard
            icon={Activity}
            label="Most Used"
            value={q.most_used_chunks?.length || 0}
            subValue="Chunks tracked"
            color="bg-purple-600"
          />
          <MetricCard
            icon={AlertTriangle}
            label="Unused Chunks"
            value={`${q.unused_chunks?.percent || 0}%`}
            subValue={`${q.unused_chunks?.count || 0} chunks`}
            color="bg-amber-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quality by Source - Table */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Quality by Source</h3>
            <div className="overflow-y-auto max-h-[300px]">
              <table className="w-full">
                <thead className="text-left text-gray-400 border-b border-dark-border">
                  <tr>
                    <th className="pb-2">Source</th>
                    <th className="pb-2 text-right">Score</th>
                    <th className="pb-2 text-right">Chunks</th>
                  </tr>
                </thead>
                <tbody>
                  {(q.quality_by_source || []).slice(0, 15).map((src: any, i: number) => (
                    <tr key={i} className="border-b border-dark-border/50">
                      <td className="py-2 text-white truncate max-w-[200px]">{src.source}</td>
                      <td className={`py-2 text-right font-mono ${src.avg_score >= 0.8 ? 'text-green-400' : 'text-yellow-400'}`}>
                        {src.avg_score.toFixed(2)}
                      </td>
                      <td className="py-2 text-right text-gray-400">{src.chunks}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Content Freshness */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Content Freshness</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={q.freshness || []}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="count"
                  label={({ period, count }) => `${period}: ${count}`}
                >
                  {(q.freshness || []).map((_: any, idx: number) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Most Used Chunks */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border lg:col-span-2">
            <h3 className="text-lg font-semibold text-white mb-4">Most Used Chunks (Top 10)</h3>
            {(q.most_used_chunks || []).length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {q.most_used_chunks.map((chunk: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-dark-bg rounded-lg">
                    <div>
                      <span className="text-white">{chunk.source}</span>
                      <span className="ml-2 text-xs text-gray-500">ID: {chunk.id.slice(0, 8)}...</span>
                    </div>
                    <span className="text-primary font-bold">{chunk.count}x</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">Noch keine Nutzungsdaten</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ============================================================
  // DASHBOARD 6: SELF-LEARNING
  // ============================================================
  const renderLearning = () => {
    const l = data?.learning
    if (!l) return null

    return (
      <div className="space-y-6">
        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={BookOpen}
            label="Generated Outputs"
            value={l.generated_outputs?.total || 0}
            subValue="Indexed for learning"
            color="bg-indigo-600"
          />
          <MetricCard
            icon={Star}
            label="Feedback Total"
            value={l.feedback_stats?.total || 0}
            color="bg-violet-600"
          />
          <MetricCard
            icon={CheckCircle}
            label="Positive"
            value={l.feedback_stats?.positive || 0}
            color="bg-green-600"
          />
          <MetricCard
            icon={XCircle}
            label="Negative"
            value={l.feedback_stats?.negative || 0}
            color="bg-red-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Feedback Distribution */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Feedback Distribution</h3>
            {(l.feedback_distribution || []).length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={l.feedback_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="score" tick={{ fill: '#888' }} />
                  <YAxis tick={{ fill: '#888' }} />
                  <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                  <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-gray-500">
                Noch kein Feedback
              </div>
            )}
          </div>

          {/* Learning Trend */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Learning Improvement Trend</h3>
            {(l.learning_trend || []).length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={l.learning_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="date" tick={{ fill: '#888' }} />
                  <YAxis tick={{ fill: '#888' }} />
                  <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #333' }} />
                  <Line type="monotone" dataKey="avg_score" stroke="#22c55e" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-gray-500">
                Noch keine Trend-Daten
              </div>
            )}
          </div>

          {/* Best Templates */}
          <div className="bg-dark-card rounded-xl p-6 border border-dark-border lg:col-span-2">
            <h3 className="text-lg font-semibold text-white mb-4">Best Performing Templates</h3>
            {(l.best_templates || []).length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {l.best_templates.map((tmpl: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-dark-bg rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-gray-600">#{i + 1}</span>
                      <div>
                        <span className="text-white">{tmpl.template}</span>
                        <span className="ml-2 text-xs text-gray-500">{tmpl.chunks} chunks</span>
                      </div>
                    </div>
                    <span className={`font-bold ${tmpl.avg_score >= 0.8 ? 'text-green-400' : 'text-yellow-400'}`}>
                      {tmpl.avg_score.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">Keine Template-Daten</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Main Render
  const renderContent = () => {
    switch (activeTab) {
      case 'overview': return renderOverview()
      case 'search': return renderSearch()
      case 'optimization': return renderOptimization()
      case 'ingestion': return renderIngestion()
      case 'quality': return renderQuality()
      case 'learning': return renderLearning()
      default: return renderOverview()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Analytics</h1>
          <p className="text-gray-400">Vollständiges Monitoring des Knowledge Systems</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="bg-dark-card border border-dark-border rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value={1}>1 Stunde</option>
            <option value={24}>24 Stunden</option>
            <option value={168}>7 Tage</option>
            <option value={720}>30 Tage</option>
          </select>
          <button
            onClick={fetchData}
            className="p-2 bg-dark-card border border-dark-border rounded-lg hover:border-primary transition-colors"
            title="Aktualisieren"
          >
            <RefreshCw className={`w-5 h-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-dark-border pb-4">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-primary text-white'
                : 'bg-dark-card text-gray-400 hover:text-white hover:bg-dark-border'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      {renderContent()}
    </div>
  )
}
