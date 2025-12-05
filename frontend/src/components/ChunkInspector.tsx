import { useState, useEffect } from 'react'
import {
  Search, FileText, Hash, Calendar, Star, Copy, ExternalLink,
  ChevronDown, ChevronUp, X, Check, AlertCircle
} from 'lucide-react'

interface Chunk {
  id: string
  text: string
  source_file: string
  source_path: string
  quality_score: number
  chunk_index: number
  total_chunks: number
  indexed_at: string
  is_framework?: boolean
  content_hash?: string
}

interface ChunkInspectorProps {
  isOpen: boolean
  onClose: () => void
  initialQuery?: string
}

export default function ChunkInspector({ isOpen, onClose, initialQuery = '' }: ChunkInspectorProps) {
  const [query, setQuery] = useState(initialQuery)
  const [collection, setCollection] = useState('knowledge_base')
  const [results, setResults] = useState<Chunk[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedChunk, setSelectedChunk] = useState<Chunk | null>(null)
  const [searchStats, setSearchStats] = useState<any>(null)

  const collections = ['knowledge_base', 'design_templates', 'external_sources', 'generated_outputs']

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setLoading(true)
    try {
      const res = await fetch(
        `/api/knowledge/admin/search?query=${encodeURIComponent(query)}&collection=${collection}&limit=20`
      )
      const data = await res.json()
      
      if (data.ok) {
        setResults(data.results || [])
        setSearchStats({
          latency: data.latency_ms,
          total: data.results?.length || 0
        })
        
        // Log search für Analytics
        if (data.results?.length > 0) {
          const avgScore = data.results.reduce((a: number, r: any) => a + r.score, 0) / data.results.length
          fetch('/api/knowledge/analytics/log/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              score: avgScore,
              latency_ms: data.latency_ms,
              results: data.results.length,
              query_type: 'inspector'
            })
          })
        }
      }
    } catch (e) {
      console.error('Search failed:', e)
    }
    setLoading(false)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-dark-card rounded-2xl border border-dark-border w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-border">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-primary" />
            Chunk Inspector
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-dark-border rounded-lg transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-4 border-b border-dark-border">
          <div className="flex gap-3">
            <select
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              className="bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white"
            >
              {collections.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Suche in Chunks..."
              className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white placeholder-gray-500"
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors disabled:opacity-50"
            >
              {loading ? 'Suche...' : 'Suchen'}
            </button>
          </div>
          {searchStats && (
            <div className="flex gap-4 mt-2 text-sm text-gray-400">
              <span>{searchStats.total} Ergebnisse</span>
              <span>{searchStats.latency}ms</span>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="flex-1 overflow-hidden flex">
          {/* Results List */}
          <div className="w-1/2 border-r border-dark-border overflow-y-auto p-4 space-y-3">
            {results.length === 0 ? (
              <div className="text-center text-gray-500 py-12">
                {query ? 'Keine Ergebnisse' : 'Suche eingeben...'}
              </div>
            ) : (
              results.map((chunk: any, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedChunk(chunk)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedChunk?.id === chunk.id
                      ? 'bg-primary/20 border-primary'
                      : 'bg-dark-bg hover:bg-dark-border'
                  } border border-dark-border`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">{chunk.source || chunk.source_file}</span>
                    <span className={`text-sm font-mono ${
                      chunk.score >= 0.75 ? 'text-green-400' : 
                      chunk.score >= 0.5 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {chunk.score?.toFixed(3)}
                    </span>
                  </div>
                  <p className="text-white text-sm line-clamp-3">
                    {chunk.text?.slice(0, 200)}...
                  </p>
                </div>
              ))
            )}
          </div>

          {/* Chunk Detail */}
          <div className="w-1/2 overflow-y-auto p-4">
            {selectedChunk ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">Chunk Details</h3>
                  <button
                    onClick={() => copyToClipboard(selectedChunk.text || '')}
                    className="p-2 hover:bg-dark-border rounded-lg transition-colors"
                    title="Text kopieren"
                  >
                    <Copy className="w-4 h-4 text-gray-400" />
                  </button>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-dark-bg rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Source</div>
                    <div className="text-white text-sm truncate">
                      {selectedChunk.source_file || (selectedChunk as any).source}
                    </div>
                  </div>
                  <div className="bg-dark-bg rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Quality Score</div>
                    <div className={`text-sm font-bold ${
                      (selectedChunk.quality_score || (selectedChunk as any).score) >= 0.8 
                        ? 'text-green-400' : 'text-yellow-400'
                    }`}>
                      {(selectedChunk.quality_score || (selectedChunk as any).score)?.toFixed(3)}
                    </div>
                  </div>
                  <div className="bg-dark-bg rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Chunk Index</div>
                    <div className="text-white text-sm">
                      {selectedChunk.chunk_index !== undefined 
                        ? `${selectedChunk.chunk_index + 1} / ${selectedChunk.total_chunks}`
                        : 'N/A'}
                    </div>
                  </div>
                  <div className="bg-dark-bg rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Framework</div>
                    <div className="text-white text-sm">
                      {selectedChunk.is_framework ? (
                        <span className="text-green-400 flex items-center gap-1">
                          <Check className="w-4 h-4" /> Ja
                        </span>
                      ) : (
                        <span className="text-gray-400">Nein</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Full Text */}
                <div className="bg-dark-bg rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-2">Vollständiger Text</div>
                  <div className="text-white text-sm whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                    {selectedChunk.text || (selectedChunk as any).content}
                  </div>
                </div>

                {/* Content Hash */}
                {selectedChunk.content_hash && (
                  <div className="text-xs text-gray-500 flex items-center gap-2">
                    <Hash className="w-3 h-3" />
                    {selectedChunk.content_hash}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-12">
                Chunk auswählen für Details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
