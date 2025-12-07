import React, { useState, useEffect } from 'react'
import { Database, Brain, Eye, Search, FileText, FolderOpen, RefreshCw } from 'lucide-react'

interface RAGStats {
  ok: boolean
  collections: Record<string, { points: number; status: string }>
  total_chunks?: number
  metrics?: any
  // Optional legacy fields
  rag?: {
    qdrant: boolean
    embedder: boolean
    vision: boolean
  }
  directories?: Record<string, { files: number; size_mb: number; path: string }>
}

export default function RAGStatus() {
  const [stats, setStats] = useState<RAGStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)

  const fetchStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/knowledge/admin/status')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (data.ok) {
        setStats(data)
      } else {
        setError('Failed to load status')
      }
    } catch (e: any) {
      console.error('Failed to fetch RAG status:', e)
      setError(e.message || 'Connection failed')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const res = await fetch(`/api/knowledge/admin/search?query=${encodeURIComponent(searchQuery)}&limit=5`)
      const data = await res.json()
      if (data.ok) {
        setSearchResults(data.results || [])
      }
    } catch (e) {
      console.error('Search failed:', e)
    }
    setSearching(false)
  }

  if (loading && !stats) {
    return <div className="animate-pulse bg-dark-card rounded-lg p-6 h-64" />
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6">
        <p className="text-red-400">Error: {error}</p>
        <button onClick={fetchStats} className="mt-2 text-sm text-red-300 hover:text-white">
          Retry
        </button>
      </div>
    )
  }

  const totalChunks = stats?.total_chunks || 
    (stats?.collections ? Object.values(stats.collections).reduce((sum, c) => sum + c.points, 0) : 0)

  // Derive RAG status from what we have
  const ragStatus = stats?.rag || {
    qdrant: stats?.ok && Object.keys(stats?.collections || {}).length > 0,
    embedder: stats?.ok,
    vision: false
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-400" />
          RAG Knowledge System
        </h2>
        <button
          onClick={fetchStats}
          className="p-2 rounded-lg bg-dark-card hover:bg-dark-border transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Service Status */}
      <div className="grid grid-cols-3 gap-4">
        <div className={`p-4 rounded-lg ${ragStatus.qdrant ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
          <div className="flex items-center gap-2">
            <Database className={`w-5 h-5 ${ragStatus.qdrant ? 'text-green-400' : 'text-red-400'}`} />
            <span className="text-white font-medium">Qdrant</span>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            {ragStatus.qdrant ? 'Connected' : 'Disconnected'}
          </p>
        </div>
        
        <div className={`p-4 rounded-lg ${ragStatus.embedder ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
          <div className="flex items-center gap-2">
            <Brain className={`w-5 h-5 ${ragStatus.embedder ? 'text-green-400' : 'text-red-400'}`} />
            <span className="text-white font-medium">Embedder</span>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            {ragStatus.embedder ? 'Ready' : 'Not loaded'}
          </p>
        </div>
        
        <div className={`p-4 rounded-lg ${ragStatus.vision ? 'bg-green-500/10 border border-green-500/30' : 'bg-yellow-500/10 border border-yellow-500/30'}`}>
          <div className="flex items-center gap-2">
            <Eye className={`w-5 h-5 ${ragStatus.vision ? 'text-green-400' : 'text-yellow-400'}`} />
            <span className="text-white font-medium">Vision</span>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            {ragStatus.vision ? 'Moondream Ready' : 'Not available'}
          </p>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-dark-card rounded-lg p-4">
          <div className="text-3xl font-bold text-white">{totalChunks.toLocaleString()}</div>
          <div className="text-sm text-gray-400">Knowledge Chunks</div>
        </div>
        <div className="bg-dark-card rounded-lg p-4">
          <div className="text-3xl font-bold text-white">{Object.keys(stats?.collections || {}).length}</div>
          <div className="text-sm text-gray-400">Collections</div>
        </div>
      </div>

      {/* Collections */}
      <div className="bg-dark-card rounded-lg p-4">
        <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-400" />
          Qdrant Collections
        </h3>
        <div className="space-y-2">
          {stats?.collections && Object.entries(stats.collections).map(([name, info]) => (
            <div key={name} className="flex items-center justify-between py-2 border-b border-dark-border last:border-0">
              <span className="text-gray-300">{name.replace(/_/g, ' ')}</span>
              <div className="flex items-center gap-4">
                <span className="text-white font-medium">{info.points.toLocaleString()} points</span>
                <span className={`px-2 py-0.5 rounded text-xs ${info.status === 'green' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                  {info.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Search Test */}
      <div className="bg-dark-card rounded-lg p-4">
        <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
          <Search className="w-4 h-4 text-cyan-400" />
          Knowledge Search Test
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search knowledge base..."
            className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-2">
            {searchResults.map((result, i) => (
              <div key={i} className="bg-dark-bg rounded-lg p-3 border border-dark-border">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-500">Score: {(result.score || 0).toFixed(3)}</span>
                  <span className="text-xs text-gray-500 truncate max-w-[200px]">{result.source || result.title || 'Unknown'}</span>
                </div>
                <p className="text-gray-300 text-sm">{result.text || result.snippet || result.content || ''}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
