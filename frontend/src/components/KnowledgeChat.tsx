import React, { useState, useRef, useEffect } from 'react'
import { MessageSquare, Send, Bot, User, Loader2, Sparkles } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{ text: string; source: string; score: number }>
  timestamp: Date
}

export default function KnowledgeChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hallo! Ich bin der Stratgen Knowledge Bot. Frag mich alles über Marketing-Strategien, Go-to-Market, Brand Archetypes, Personas und mehr aus unserer Knowledge Base.',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Suche in der Knowledge Base
      const searchRes = await fetch(`/api/health/rag/search?q=${encodeURIComponent(input)}&limit=5`)
      const searchData = await searchRes.json()

      // Baue Kontext aus Suchergebnissen
      const context = searchData.ok && searchData.results.length > 0
        ? searchData.results.map((r: any) => r.text).join('\n\n')
        : ''

      // Generiere Antwort mit LLM
      const llmRes = await fetch('/api/orchestrator/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: `Du bist ein hilfreicher Marketing-Strategie-Assistent. Beantworte die Frage basierend auf dem folgenden Kontext aus der Knowledge Base.

KONTEXT:
${context || 'Kein spezifischer Kontext gefunden.'}

FRAGE: ${input}

Antworte präzise und hilfreich. Wenn der Kontext relevant ist, beziehe dich darauf. Wenn nicht, gib eine allgemeine hilfreiche Antwort.`,
          max_tokens: 500
        })
      })

      let assistantContent = ''
      
      if (llmRes.ok) {
        const llmData = await llmRes.json()
        assistantContent = llmData.response || llmData.text || 'Entschuldigung, ich konnte keine Antwort generieren.'
      } else {
        // Fallback: Zeige nur die Suchergebnisse
        if (searchData.ok && searchData.results.length > 0) {
          assistantContent = `Hier sind relevante Informationen aus der Knowledge Base:\n\n${searchData.results.slice(0, 3).map((r: any, i: number) => `${i + 1}. ${r.text}`).join('\n\n')}`
        } else {
          assistantContent = 'Ich konnte leider keine relevanten Informationen zu deiner Frage finden.'
        }
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: assistantContent,
        sources: searchData.ok ? searchData.results.slice(0, 3) : [],
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (e) {
      console.error('Chat error:', e)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Es ist ein Fehler aufgetreten. Bitte versuche es erneut.',
        timestamp: new Date()
      }])
    }

    setLoading(false)
  }

  return (
    <div className="flex flex-col h-[600px] bg-dark-card rounded-xl border border-dark-border">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-dark-border">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-white font-medium">Knowledge Bot</h3>
          <p className="text-xs text-gray-400">Powered by RAG + Mistral</p>
        </div>
        <div className="ml-auto flex items-center gap-1 text-xs text-green-400">
          <Sparkles className="w-3 h-3" />
          <span>4000+ Knowledge Chunks</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user' 
                ? 'bg-blue-600' 
                : 'bg-gradient-to-br from-purple-500 to-blue-500'
            }`}>
              {msg.role === 'user' ? (
                <User className="w-4 h-4 text-white" />
              ) : (
                <Bot className="w-4 h-4 text-white" />
              )}
            </div>
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
              <div className={`rounded-2xl px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-dark-bg text-gray-200'
              }`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-500">Quellen:</p>
                  {msg.sources.map((s, i) => (
                    <div key={i} className="text-xs text-gray-400 bg-dark-bg/50 rounded px-2 py-1">
                      [{s.score.toFixed(2)}] {s.source?.split('/').pop() || 'Knowledge Base'}
                    </div>
                  ))}
                </div>
              )}
              <p className="text-xs text-gray-500 mt-1">
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            </div>
            <div className="bg-dark-bg rounded-2xl px-4 py-2">
              <p className="text-gray-400">Suche in Knowledge Base...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-dark-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Frag mich etwas über Marketing-Strategien..."
            className="flex-1 bg-dark-bg border border-dark-border rounded-full px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 flex items-center justify-center transition-colors"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}
