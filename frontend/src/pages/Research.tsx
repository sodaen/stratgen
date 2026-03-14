import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, Play, Square, RefreshCw, ChevronDown, ChevronUp,
  Globe, CheckCircle, Clock, AlertCircle, Loader2, Database,
  ExternalLink, Star, BookOpen, Newspaper, GraduationCap
} from 'lucide-react'
import { cn } from '../utils/helpers'

const API_BASE = '/api'

interface ResearchResult {
  id: string
  title: string
  url: string
  snippet: string
  domain: string
  quality_score: number
  source_type: string
}

interface ResearchSession {
  session_id: string
  topic: string
  status: string
  progress: number
  queries: string[]
  queries_done: number
  result_count: number
  ingested: boolean
  ingest_count: number
  created_at: number
}

const SOURCE_ICONS: Record<string, any> = {
  wiki: BookOpen,
  news_article: Newspaper,
  academic: GraduationCap,
  web_page: Globe,
}

export default function Research() {
  const [topic, setTopic] = useState('')
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard')
  const [language, setLanguage] = useState<'de' | 'en'>('de')
  const [autoIngest, setAutoIngest] = useState(true)
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([])
  const [loadingQueries, setLoadingQueries] = useState(false)
  const [sessions, setSessions] = useState<ResearchSession[]>([])
  const [activeSession, setActiveSession] = useState<ResearchSession | null>(null)
  const [liveResults, setLiveResults] = useState<ResearchResult[]>([])
  const [running, setRunning] = useState(false)
  const [expandedSession, setExpandedSession] = useState<string | null>(null)
  const [sessionDetails, setSessionDetails] = useState<Record<string, ResearchResult[]>>({})
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    loadSessions()
    return () => { if (pollRef.current) clearTimeout(pollRef.current) }
  }, [])

  async function loadSessions() {
    try {
      const r = await fetch(`${API_BASE}/research/deep/sessions/list`)
      const d = await r.json()
      setSessions(d.sessions || [])
    } catch { /* silent */ }
  }

  async function suggestQueries() {
    if (!topic.trim()) return
    setLoadingQueries(true)
    try {
      const r = await fetch(`${API_BASE}/research/deep/queries/suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, depth, language }),
      })
      const d = await r.json()
      setSuggestedQueries(d.queries || [])
    } catch { /* silent */ }
    finally { setLoadingQueries(false) }
  }

  async function startResearch() {
    if (!topic.trim()) return
    setRunning(true)
    setLiveResults([])
    setActiveSession(null)

    try {
      const r = await fetch(`${API_BASE}/research/deep/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, depth, language, auto_ingest: autoIngest }),
      })
      const d = await r.json()
      if (!d.ok) throw new Error(d.detail || 'Fehler')

      const session: ResearchSession = {
        session_id: d.session_id,
        topic,
        status: 'running',
        progress: 0,
        queries: d.queries || [],
        queries_done: 0,
        result_count: 0,
        ingested: false,
        ingest_count: 0,
        created_at: Date.now() / 1000,
      }
      setActiveSession(session)
      pollSession(d.session_id)
    } catch (e: any) {
      setRunning(false)
    }
  }

  function pollSession(sessionId: string) {
    pollRef.current = setTimeout(async () => {
      try {
        const r = await fetch(`${API_BASE}/research/deep/${sessionId}`)
        const d = await r.json()

        setActiveSession(prev => prev ? { ...prev, ...d } : d)
        setLiveResults(d.results || [])

        if (d.status === 'running') {
          pollSession(sessionId)
        } else {
          setRunning(false)
          loadSessions()
        }
      } catch {
        setRunning(false)
      }
    }, 1500)
  }

  async function cancelSession() {
    if (!activeSession) return
    await fetch(`${API_BASE}/research/deep/${activeSession.session_id}/cancel`, { method: 'POST' })
    setRunning(false)
    if (pollRef.current) clearTimeout(pollRef.current)
    loadSessions()
  }

  async function ingestSession(sessionId: string) {
    await fetch(`${API_BASE}/research/deep/${sessionId}/ingest`, { method: 'POST' })
    loadSessions()
  }

  async function loadSessionDetails(sessionId: string) {
    if (sessionDetails[sessionId]) return
    try {
      const r = await fetch(`${API_BASE}/research/deep/${sessionId}`)
      const d = await r.json()
      setSessionDetails(prev => ({ ...prev, [sessionId]: d.results || [] }))
    } catch { /* silent */ }
  }

  function toggleSession(sessionId: string) {
    if (expandedSession === sessionId) {
      setExpandedSession(null)
    } else {
      setExpandedSession(sessionId)
      loadSessionDetails(sessionId)
    }
  }

  const qualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-slate-500'
  }

  const StatusIcon = ({ status }: { status: string }) => {
    if (status === 'running') return <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
    if (status === 'done') return <CheckCircle className="w-3.5 h-3.5 text-green-400" />
    if (status === 'failed') return <AlertCircle className="w-3.5 h-3.5 text-red-400" />
    if (status === 'cancelled') return <Square className="w-3.5 h-3.5 text-slate-500" />
    return <Clock className="w-3.5 h-3.5 text-slate-400" />
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Deep Research</h1>
        <p className="text-slate-400 mt-1">Web-Recherche → automatisch in Knowledge Base indexiert</p>
      </div>

      {/* Start Form */}
      <div className="bg-dark-card border border-dark-border rounded-2xl p-5 space-y-4">
        <div className="flex gap-3">
          <div className="flex-1">
            <input
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !running && startResearch()}
              placeholder="Thema der Recherche (z.B. KI im Gesundheitswesen)"
              className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <button
            onClick={suggestQueries}
            disabled={!topic.trim() || loadingQueries}
            className="px-4 py-3 bg-dark-border rounded-xl text-slate-400 hover:text-white transition-colors disabled:opacity-50 flex items-center gap-2 text-sm"
          >
            {loadingQueries ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Queries
          </button>
        </div>

        {/* Query Suggestions */}
        {suggestedQueries.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs text-slate-500">Vorgeschlagene Suchanfragen:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQueries.map((q, i) => (
                <span key={i} className="px-2.5 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-300">
                  {q}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Options */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Tiefe:</span>
            {(['quick', 'standard', 'deep'] as const).map(d => (
              <button
                key={d}
                onClick={() => setDepth(d)}
                className={cn(
                  'px-3 py-1 rounded-lg text-xs transition-all',
                  depth === d
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    : 'bg-dark-border text-slate-400 hover:text-white'
                )}
              >
                {d === 'quick' ? 'Schnell (3)' : d === 'standard' ? 'Standard (6)' : 'Tief (10)'}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Sprache:</span>
            {(['de', 'en'] as const).map(l => (
              <button
                key={l}
                onClick={() => setLanguage(l)}
                className={cn(
                  'px-3 py-1 rounded-lg text-xs transition-all',
                  language === l
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    : 'bg-dark-border text-slate-400 hover:text-white'
                )}
              >
                {l === 'de' ? '🇩🇪 Deutsch' : '🇬🇧 English'}
              </button>
            ))}
          </div>

          <label className="flex items-center gap-2 cursor-pointer ml-auto">
            <input
              type="checkbox"
              checked={autoIngest}
              onChange={e => setAutoIngest(e.target.checked)}
              className="rounded"
            />
            <span className="text-xs text-slate-400">Auto-Ingest in Knowledge Base</span>
          </label>
        </div>

        <button
          onClick={running ? cancelSession : startResearch}
          disabled={!topic.trim() && !running}
          className={cn(
            'w-full py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-all',
            running
              ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30'
              : 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {running ? (
            <><Square className="w-4 h-4" /> Abbrechen</>
          ) : (
            <><Play className="w-4 h-4" /> Recherche starten</>
          )}
        </button>
      </div>

      {/* Live Session */}
      {activeSession && (
        <div className="bg-dark-card border border-blue-500/30 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <StatusIcon status={activeSession.status} />
              <span className="text-sm font-medium text-white">{activeSession.topic}</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span>{activeSession.result_count} Ergebnisse</span>
              <span>{activeSession.progress}%</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="h-1.5 bg-dark-border rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
              animate={{ width: `${activeSession.progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          {/* Queries Status */}
          {activeSession.queries.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {activeSession.queries.map((q, i) => (
                <span key={i} className={cn(
                  'px-2 py-0.5 rounded-md text-xs',
                  i < activeSession.queries_done
                    ? 'bg-green-500/15 text-green-400'
                    : i === activeSession.queries_done && running
                      ? 'bg-blue-500/15 text-blue-400'
                      : 'bg-dark-border text-slate-500'
                )}>
                  {q.length > 30 ? q.slice(0, 30) + '…' : q}
                </span>
              ))}
            </div>
          )}

          {/* Live Results */}
          {liveResults.length > 0 && (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {liveResults.map(r => {
                const SrcIcon = SOURCE_ICONS[r.source_type] || Globe
                return (
                  <div key={r.id} className="flex items-start gap-3 p-2.5 bg-dark-border/50 rounded-lg">
                    <SrcIcon className="w-3.5 h-3.5 text-slate-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-white truncate">{r.title}</p>
                      <p className="text-xs text-slate-500 truncate">{r.domain}</p>
                    </div>
                    <span className={cn('text-xs font-mono', qualityColor(r.quality_score))}>
                      {(r.quality_score * 100).toFixed(0)}
                    </span>
                    <a href={r.url} target="_blank" rel="noopener noreferrer"
                      className="text-slate-600 hover:text-slate-300 transition-colors flex-shrink-0">
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )
              })}
            </div>
          )}

          {/* Ingest Status */}
          {activeSession.ingested && (
            <div className="flex items-center gap-2 text-green-400 text-xs">
              <Database className="w-3.5 h-3.5" />
              {activeSession.ingest_count} Einträge in Knowledge Base indexiert
            </div>
          )}
        </div>
      )}

      {/* Previous Sessions */}
      {sessions.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-400">Frühere Recherchen</h2>
          {sessions.map(s => (
            <div key={s.session_id} className="bg-dark-card border border-dark-border rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSession(s.session_id)}
                className="w-full flex items-center gap-3 p-4 hover:bg-dark-border/30 transition-colors text-left"
              >
                <StatusIcon status={s.status} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{s.topic}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {s.result_count} Ergebnisse · {new Date(s.created_at * 1000).toLocaleDateString('de-DE')}
                    {s.ingested && <span className="ml-2 text-green-400">· ✓ indexiert</span>}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {s.status === 'done' && !s.ingested && (
                    <button
                      onClick={e => { e.stopPropagation(); ingestSession(s.session_id) }}
                      className="px-2.5 py-1 bg-blue-500/15 text-blue-400 rounded-lg text-xs hover:bg-blue-500/25 transition-colors flex items-center gap-1"
                    >
                      <Database className="w-3 h-3" />
                      Ingest
                    </button>
                  )}
                  {expandedSession === s.session_id
                    ? <ChevronUp className="w-4 h-4 text-slate-500" />
                    : <ChevronDown className="w-4 h-4 text-slate-500" />
                  }
                </div>
              </button>

              <AnimatePresence>
                {expandedSession === s.session_id && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    exit={{ height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="border-t border-dark-border p-4 space-y-2 max-h-72 overflow-y-auto">
                      {(sessionDetails[s.session_id] || []).length === 0 ? (
                        <div className="flex items-center justify-center py-4">
                          <Loader2 className="w-4 h-4 text-slate-500 animate-spin" />
                        </div>
                      ) : (
                        sessionDetails[s.session_id].map(r => {
                          const SrcIcon = SOURCE_ICONS[r.source_type] || Globe
                          return (
                            <div key={r.id} className="flex items-start gap-3 p-2 hover:bg-dark-border/30 rounded-lg">
                              <SrcIcon className="w-3.5 h-3.5 text-slate-500 mt-0.5 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs text-white">{r.title}</p>
                                <p className="text-xs text-slate-600 truncate">{r.snippet?.slice(0, 120)}…</p>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <span className={cn('text-xs', qualityColor(r.quality_score))}>
                                  <Star className="w-3 h-3 inline mr-0.5" />
                                  {(r.quality_score * 100).toFixed(0)}%
                                </span>
                                <a href={r.url} target="_blank" rel="noopener noreferrer"
                                  className="text-slate-600 hover:text-slate-300">
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </div>
                            </div>
                          )
                        })
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
