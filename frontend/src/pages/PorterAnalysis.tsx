import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Zap, Shield, Users, ShoppingCart, Package,
  Loader2, RefreshCw, ChevronDown, ChevronUp,
  BarChart2, Download, Sparkles
} from 'lucide-react'
import { cn } from '../utils/helpers'

const API_BASE = '/api'

interface Force {
  key: string
  label: string
  icon: any
  color: string
  description: string
}

const FORCES: Force[] = [
  {
    key: 'rivalry',
    label: 'Wettbewerb in der Branche',
    icon: Zap,
    color: 'red',
    description: 'Intensität des Wettbewerbs zwischen bestehenden Unternehmen',
  },
  {
    key: 'new_entrants',
    label: 'Bedrohung durch neue Anbieter',
    icon: Users,
    color: 'orange',
    description: 'Wie einfach können neue Wettbewerber in den Markt eintreten?',
  },
  {
    key: 'substitutes',
    label: 'Bedrohung durch Substitute',
    icon: RefreshCw,
    color: 'yellow',
    description: 'Wie leicht können Kunden auf alternative Produkte wechseln?',
  },
  {
    key: 'buyer_power',
    label: 'Verhandlungsmacht der Käufer',
    icon: ShoppingCart,
    color: 'blue',
    description: 'Einfluss der Käufer auf Preise und Konditionen',
  },
  {
    key: 'supplier_power',
    label: 'Verhandlungsmacht der Lieferanten',
    icon: Package,
    color: 'purple',
    description: 'Einfluss der Lieferanten auf Kosten und Verfügbarkeit',
  },
]

const COLOR_MAP: Record<string, string> = {
  red:    'from-red-500/20 to-red-600/10 border-red-500/30 text-red-400',
  orange: 'from-orange-500/20 to-orange-600/10 border-orange-500/30 text-orange-400',
  yellow: 'from-yellow-500/20 to-yellow-600/10 border-yellow-500/30 text-yellow-400',
  blue:   'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400',
  purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400',
}

const SCORE_COLOR = (s: number) => {
  if (s >= 8) return 'bg-red-500'
  if (s >= 6) return 'bg-orange-500'
  if (s >= 4) return 'bg-yellow-500'
  return 'bg-green-500'
}

interface ForceResult {
  score: number        // 1–10
  intensity: string    // niedrig | mittel | hoch
  key_factors: string[]
  implications: string
  raw?: string
}

type AnalysisResult = Record<string, ForceResult> & {
  overall_attractiveness?: string
  strategic_recommendations?: string[]
}

export default function PorterAnalysis() {
  const [topic, setTopic] = useState('')
  const [industry, setIndustry] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [exportDone, setExportDone] = useState(false)

  async function runAnalysis() {
    if (!topic.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setExportDone(false)

    try {
      const r = await fetch(`${API_BASE}/strategy/porter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          industry: industry || topic,
          customer_name: topic,
        }),
      })
      const d = await r.json()
      if (!d.ok && !d.forces) throw new Error(d.error || d.detail || 'Analyse fehlgeschlagen')
      setResult(d.forces || d)
      // Ersten aufklappen
      setExpanded(FORCES[0].key)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function exportSlides() {
    if (!result) return
    setExporting(true)
    try {
      const r = await fetch(`${API_BASE}/strategy/gen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          industry,
          include_porter: true,
          porter_data: result,
          deck_size: 8,
        }),
      })
      const d = await r.json()
      if (d.ok) setExportDone(true)
    } catch { /* silent */ }
    finally { setExporting(false) }
  }

  const overallScore = result
    ? Math.round(
        FORCES.reduce((sum, f) => sum + ((result[f.key] as ForceResult)?.score ?? 5), 0) / FORCES.length
      )
    : 0

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Porter's Five Forces</h1>
        <p className="text-slate-400 mt-1">Strategische Branchenanalyse via KI + RAG</p>
      </div>

      {/* Input */}
      <div className="bg-dark-card border border-dark-border rounded-2xl p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Unternehmen / Thema</label>
            <input
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !loading && runAnalysis()}
              placeholder="z.B. Tesla, SAP, lokales Einzelhandelsunternehmen"
              className="w-full px-3 py-2.5 bg-dark-border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Branche (optional)</label>
            <input
              value={industry}
              onChange={e => setIndustry(e.target.value)}
              placeholder="z.B. Elektromobilität, ERP-Software, Lebensmittel"
              className="w-full px-3 py-2.5 bg-dark-border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
        </div>

        <button
          onClick={runAnalysis}
          disabled={loading || !topic.trim()}
          className={cn(
            'w-full py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-all',
            loading || !topic.trim()
              ? 'bg-dark-border text-slate-500'
              : 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25'
          )}
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Analyse läuft…</>
          ) : (
            <><Sparkles className="w-4 h-4" /> Analyse starten</>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {/* Overall Score */}
          <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <BarChart2 className="w-5 h-5 text-blue-400" />
                <h2 className="text-white font-semibold">Gesamtbewertung: {topic}</h2>
              </div>
              <div className="flex items-center gap-3">
                <div className={cn(
                  'px-3 py-1 rounded-full text-sm font-bold',
                  overallScore >= 7 ? 'bg-red-500/20 text-red-400' :
                  overallScore >= 5 ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-green-500/20 text-green-400'
                )}>
                  {overallScore}/10 Wettbewerbsdruck
                </div>
                <button
                  onClick={exportSlides}
                  disabled={exporting || exportDone}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all',
                    exportDone
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-dark-border text-slate-400 hover:text-white'
                  )}
                >
                  {exporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                  {exportDone ? 'Exportiert!' : 'Als Slides'}
                </button>
              </div>
            </div>

            {/* Radar / Score bars */}
            <div className="space-y-3">
              {FORCES.map(force => {
                const data = result[force.key] as ForceResult
                const score = data?.score ?? 5
                return (
                  <div key={force.key} className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 w-48 truncate">{force.label}</span>
                    <div className="flex-1 h-2 bg-dark-border rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${score * 10}%` }}
                        transition={{ duration: 0.6, delay: FORCES.indexOf(force) * 0.1 }}
                        className={cn('h-full rounded-full', SCORE_COLOR(score))}
                      />
                    </div>
                    <span className="text-xs font-mono text-slate-400 w-8 text-right">{score}/10</span>
                  </div>
                )
              })}
            </div>

            {result.overall_attractiveness && (
              <p className="mt-4 text-sm text-slate-300 bg-dark-border/50 rounded-lg px-3 py-2">
                {result.overall_attractiveness}
              </p>
            )}
          </div>

          {/* Individual Forces */}
          {FORCES.map(force => {
            const data = result[force.key] as ForceResult
            if (!data) return null
            const Icon = force.icon
            const isOpen = expanded === force.key
            const colors = COLOR_MAP[force.color]

            return (
              <div key={force.key} className="bg-dark-card border border-dark-border rounded-2xl overflow-hidden">
                <button
                  onClick={() => setExpanded(isOpen ? null : force.key)}
                  className="w-full flex items-center gap-4 p-4 hover:bg-dark-border/20 transition-colors text-left"
                >
                  <div className={cn(
                    'w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br border',
                    colors
                  )}>
                    <Icon className="w-5 h-5" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white">{force.label}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{force.description}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'px-2.5 py-1 rounded-lg text-xs font-bold',
                      data.score >= 7 ? 'bg-red-500/20 text-red-400' :
                      data.score >= 5 ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    )}>
                      {data.score}/10
                    </div>
                    <span className="text-xs text-slate-500 capitalize">{data.intensity}</span>
                    {isOpen
                      ? <ChevronUp className="w-4 h-4 text-slate-500" />
                      : <ChevronDown className="w-4 h-4 text-slate-500" />
                    }
                  </div>
                </button>

                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 'auto' }}
                      exit={{ height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="border-t border-dark-border p-4 space-y-4">
                        {/* Key Factors */}
                        {data.key_factors?.length > 0 && (
                          <div>
                            <h4 className="text-xs font-medium text-slate-400 mb-2">Schlüsselfaktoren</h4>
                            <ul className="space-y-1.5">
                              {data.key_factors.map((f, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                                  <span className="text-blue-400 mt-0.5 flex-shrink-0">•</span>
                                  {f}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Implications */}
                        {data.implications && (
                          <div>
                            <h4 className="text-xs font-medium text-slate-400 mb-2">Strategische Implikation</h4>
                            <p className="text-sm text-slate-300 bg-dark-border/40 rounded-lg px-3 py-2">
                              {data.implications}
                            </p>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}

          {/* Strategic Recommendations */}
          {result.strategic_recommendations && result.strategic_recommendations.length > 0 && (
            <div className="bg-dark-card border border-blue-500/20 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-semibold text-white">Strategische Handlungsempfehlungen</h3>
              </div>
              <ul className="space-y-2">
                {result.strategic_recommendations.map((r, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
