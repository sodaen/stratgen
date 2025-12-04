import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Sparkles, ExternalLink } from 'lucide-react'

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
      content: 'Hallo! Ich bin der Stratgen Knowledge Bot. Frag mich alles über Marketing-Strategien, Go-to-Market, Brand Archetypes, Personas und mehr aus unserer Knowledge Base mit über 17.000 Wissens-Chunks.',
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
    const query = input
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/rag/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })

      const data = await res.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.ok ? data.answer : 'Es ist ein Fehler aufgetreten.',
        sources: data.sources || [],
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (e) {
      console.error('Chat error:', e)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Verbindungsfehler. Bitte versuche es erneut.',
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
          <p className="text-xs text-gray-400">RAG + Mistral LLM</p>
        </div>
        <div className="ml-auto flex items-center gap-1 text-xs text-green-400">
          <Sparkles className="w-3 h-3" />
          <span>17k+ Chunks</span>
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
              <div className={`rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-dark-bg text-gray-200'
              }`}>
                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
              </div>
              
              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <ExternalLink className="w-3 h-3" />
                    Quellen:
                  </p>
                  {msg.sources.map((s, i) => (
                    <div key={i} className="text-xs bg-dark-bg/50 rounded-lg px-3 py-2 border border-dark-border">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-green-400 font-medium">Score: {s.score.toFixed(2)}</span>
                        <span className="text-gray-500 truncate max-w-[150px]">
                          {s.source?.split('/').pop() || 'Knowledge'}
                        </span>
                      </div>
                      <p className="text-gray-400 line-clamp-2">{s.text}</p>
                    </div>
                  ))}
                </div>
              )}
              
              <p className="text-xs text-gray-600 mt-1">
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
            <div className="bg-dark-bg rounded-2xl px-4 py-3">
              <p className="text-gray-400 text-sm">Durchsuche Knowledge Base...</p>
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
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Frag mich etwas über Marketing, GTM, Personas..."
            className="flex-1 bg-dark-bg border border-dark-border rounded-full px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">
          Basiert auf 4000+ Knowledge Chunks • Mistral LLM
        </p>
      </div>
    </div>
  )
}
