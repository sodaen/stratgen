import { useState } from 'react'
import {
  RefreshCw, Trash2, Database, Search, Play, AlertTriangle,
  CheckCircle, XCircle, Loader2, FolderOpen
} from 'lucide-react'

interface ControlsProps {
  onRefresh: () => void
}

export default function KnowledgeControls({ onRefresh }: ControlsProps) {
  const [loading, setLoading] = useState<string | null>(null)
  const [result, setResult] = useState<{ type: 'success' | 'error', message: string } | null>(null)

  const showResult = (type: 'success' | 'error', message: string) => {
    setResult({ type, message })
    setTimeout(() => setResult(null), 5000)
  }

  const handleReindex = async (collection: string) => {
    if (!confirm(`Möchtest du die Collection "${collection}" wirklich neu indexieren? Das kann einige Minuten dauern.`)) {
      return
    }
    
    setLoading(`reindex-${collection}`)
    try {
      const endpoint = collection === 'knowledge_base' 
        ? '/api/knowledge/admin/ingest/knowledge'
        : '/api/knowledge/admin/ingest/templates'
      
      const res = await fetch(endpoint, { method: 'POST' })
      const data = await res.json()
      
      if (data.ok) {
        showResult('success', `${collection} neu indexiert: ${data.chunks_created || 0} Chunks`)
        onRefresh()
      } else {
        showResult('error', data.error || 'Fehler beim Indexieren')
      }
    } catch (e) {
      showResult('error', 'Verbindungsfehler')
    }
    setLoading(null)
  }

  const handleClearCollection = async (collection: string) => {
    if (!confirm(`WARNUNG: Möchtest du wirklich alle Chunks aus "${collection}" löschen? Diese Aktion kann nicht rückgängig gemacht werden!`)) {
      return
    }
    
    setLoading(`clear-${collection}`)
    try {
      const res = await fetch(`/api/knowledge/admin/collections/${collection}/clear`, { method: 'POST' })
      const data = await res.json()
      
      if (data.ok) {
        showResult('success', `${collection} geleert`)
        onRefresh()
      } else {
        showResult('error', data.error || 'Fehler beim Leeren')
      }
    } catch (e) {
      showResult('error', 'Verbindungsfehler')
    }
    setLoading(null)
  }

  const handleFullRebuild = async () => {
    if (!confirm('WARNUNG: Dies löscht ALLE Collections und indexiert alles neu. Fortfahren?')) {
      return
    }
    
    setLoading('rebuild')
    try {
      const res = await fetch('/api/knowledge/admin/rebuild', { method: 'POST' })
      const data = await res.json()
      
      if (data.ok) {
        showResult('success', 'Rebuild gestartet - prüfe Logs für Status')
        onRefresh()
      } else {
        showResult('error', data.error || 'Rebuild fehlgeschlagen')
      }
    } catch (e) {
      showResult('error', 'Verbindungsfehler')
    }
    setLoading(null)
  }

  const handleTestSearch = async () => {
    setLoading('test')
    try {
      const queries = [
        'Marketing Strategie',
        'Go-to-Market Framework',
        'B2B SaaS',
        'Content Marketing',
        'KPI Benchmarks'
      ]
      
      const results = []
      for (const query of queries) {
        const res = await fetch(`/api/knowledge/admin/search/rerank?query=${encodeURIComponent(query)}&use_llm=false&limit=3`)
        const data = await res.json()
        if (data.ok) {
          results.push({
            query,
            score: data.scores?.final_avg || 0,
            latency: data.latency?.total_ms || 0
          })
        }
      }
      
      const avgScore = results.reduce((a, r) => a + r.score, 0) / results.length
      const avgLatency = results.reduce((a, r) => a + r.latency, 0) / results.length
      
      showResult('success', `Test abgeschlossen: Ø Score ${avgScore.toFixed(3)}, Ø Latenz ${Math.round(avgLatency)}ms`)
    } catch (e) {
      showResult('error', 'Test fehlgeschlagen')
    }
    setLoading(null)
  }

  const collections = [
    { name: 'knowledge_base', label: 'Knowledge Base', icon: Database },
    { name: 'design_templates', label: 'Design Templates', icon: FolderOpen },
  ]

  return (
    <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <RefreshCw className="w-5 h-5 text-primary" />
        Manual Controls
      </h3>

      {/* Result Message */}
      {result && (
        <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
          result.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
          {result.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {result.message}
        </div>
      )}

      {/* Collection Controls */}
      <div className="space-y-4">
        {collections.map(({ name, label, icon: Icon }) => (
          <div key={name} className="flex items-center justify-between p-3 bg-dark-bg rounded-lg">
            <div className="flex items-center gap-3">
              <Icon className="w-5 h-5 text-primary" />
              <span className="text-white">{label}</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleReindex(name)}
                disabled={loading !== null}
                className="px-3 py-1.5 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors disabled:opacity-50 flex items-center gap-1"
              >
                {loading === `reindex-${name}` ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Re-Index
              </button>
              <button
                onClick={() => handleClearCollection(name)}
                disabled={loading !== null}
                className="px-3 py-1.5 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50 flex items-center gap-1"
              >
                {loading === `clear-${name}` ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Clear
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Global Actions */}
      <div className="mt-6 pt-4 border-t border-dark-border flex flex-wrap gap-3">
        <button
          onClick={handleTestSearch}
          disabled={loading !== null}
          className="px-4 py-2 bg-violet-500/20 text-violet-400 rounded-lg hover:bg-violet-500/30 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {loading === 'test' ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          Test Search (5 Queries)
        </button>
        
        <button
          onClick={handleFullRebuild}
          disabled={loading !== null}
          className="px-4 py-2 bg-amber-500/20 text-amber-400 rounded-lg hover:bg-amber-500/30 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {loading === 'rebuild' ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <AlertTriangle className="w-4 h-4" />
          )}
          Full Rebuild
        </button>
      </div>

      <p className="mt-4 text-xs text-gray-500">
        ⚠️ Clear und Rebuild sind destruktive Aktionen und können nicht rückgängig gemacht werden.
      </p>
    </div>
  )
}
