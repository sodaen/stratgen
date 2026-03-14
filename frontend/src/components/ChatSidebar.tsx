import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare, Send, ThumbsUp, ThumbsDown, X,
  Loader2, Bot, User, Trash2, ChevronDown
} from 'lucide-react'
import { cn } from '../utils/helpers'

const API_BASE = '/api'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  feedback?: 'up' | 'down'
}

interface ChatSidebarProps {
  sessionId?: string
  slideContext?: string   // aktueller Slide-Inhalt als Kontext
  onClose?: () => void
  className?: string
}

export default function ChatSidebar({ sessionId, slideContext, onClose, className }: ChatSidebarProps) {
  const [chatSessionId, setChatSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Chat-Session anlegen oder laden
  useEffect(() => {
    if (sessionId) {
      initChat(sessionId)
    } else {
      createNewChat()
    }
  }, [sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  async function createNewChat() {
    try {
      const r = await fetch(`${API_BASE}/chat/sessions/new`, { method: 'POST' })
      const d = await r.json()
      setChatSessionId(d.session_id)
    } catch {
      setError('Chat-Session konnte nicht erstellt werden.')
    }
  }

  async function initChat(sid: string) {
    setChatSessionId(sid)
    try {
      const r = await fetch(`${API_BASE}/chat/${sid}/history`)
      const d = await r.json()
      if (d.messages) {
        setMessages(d.messages.map((m: any) => ({
          id: crypto.randomUUID(),
          role: m.role,
          content: m.content,
          timestamp: Date.now(),
        })))
      }
    } catch { /* neue Session */ }
  }

  async function sendMessage() {
    if (!input.trim() || isStreaming || !chatSessionId) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsStreaming(true)
    setStreamingContent('')
    setError(null)

    // Slide-Kontext anhängen falls vorhanden
    const contextualInput = slideContext
      ? `[Slide-Kontext: ${slideContext.slice(0, 300)}]\n\n${userMsg.content}`
      : userMsg.content

    try {
      const response = await fetch(`${API_BASE}/chat/${chatSessionId}/message/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: contextualInput }),
      })

      if (!response.ok) throw new Error('Stream-Fehler')

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        // SSE-Format: "data: token\n\n"
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const token = line.slice(6)
            if (token === '[DONE]') continue
            accumulated += token
            setStreamingContent(accumulated)
          }
        }
      }

      // Streaming-Inhalt als Nachricht speichern
      if (accumulated) {
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: accumulated,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, assistantMsg])
      }
    } catch {
      // Fallback: normaler Request
      try {
        const r = await fetch(`${API_BASE}/chat/${chatSessionId}/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: contextualInput }),
        })
        const d = await r.json()
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: d.response || d.message || 'Keine Antwort',
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, assistantMsg])
      } catch {
        setError('Verbindungsfehler. Ist das Backend erreichbar?')
      }
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
      inputRef.current?.focus()
    }
  }

  async function sendFeedback(msgId: string, rating: 'up' | 'down') {
    if (!chatSessionId) return
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, feedback: rating } : m))
    try {
      await fetch(`${API_BASE}/chat/${chatSessionId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, message_id: msgId }),
      })
    } catch { /* silent */ }
  }

  async function clearChat() {
    if (!chatSessionId) return
    setMessages([])
    try {
      await fetch(`${API_BASE}/chat/${chatSessionId}`, { method: 'DELETE' })
    } catch { /* silent */ }
    createNewChat()
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className={cn(
      'flex flex-col bg-dark-card border border-dark-border rounded-2xl overflow-hidden',
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-dark-border">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">KI-Assistent</h3>
            {chatSessionId && (
              <p className="text-xs text-slate-500 font-mono">{chatSessionId.slice(0, 8)}…</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={clearChat}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-dark-border transition-colors"
            title="Chat leeren"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-dark-border transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <MessageSquare className="w-8 h-8 text-slate-600 mb-3" />
            <p className="text-sm text-slate-500">Stelle eine Frage zu deiner Präsentation</p>
            <div className="mt-4 space-y-2 w-full">
              {[
                'Analysiere den aktuellen Slide',
                'Schlage 3 Alternativen vor',
                'Mach den Text überzeugender',
              ].map(s => (
                <button
                  key={s}
                  onClick={() => { setInput(s); inputRef.current?.focus() }}
                  className="w-full text-left px-3 py-2 rounded-lg bg-dark-border text-xs text-slate-400 hover:text-white hover:bg-dark-bg transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map(msg => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn('flex gap-2', msg.role === 'user' ? 'flex-row-reverse' : 'flex-row')}
            >
              <div className={cn(
                'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-1',
                msg.role === 'user'
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'bg-gradient-to-br from-blue-500 to-cyan-500'
              )}>
                {msg.role === 'user'
                  ? <User className="w-3 h-3" />
                  : <Bot className="w-3 h-3 text-white" />
                }
              </div>

              <div className={cn(
                'max-w-[85%] space-y-1',
                msg.role === 'user' ? 'items-end' : 'items-start'
              )}>
                <div className={cn(
                  'px-3 py-2 rounded-xl text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-blue-500/20 text-blue-100 rounded-tr-sm'
                    : 'bg-dark-border text-slate-200 rounded-tl-sm'
                )}>
                  {msg.content}
                </div>

                {/* Feedback (nur für Assistant) */}
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-1 pl-1">
                    <button
                      onClick={() => sendFeedback(msg.id, 'up')}
                      className={cn(
                        'p-1 rounded transition-colors',
                        msg.feedback === 'up' ? 'text-green-400' : 'text-slate-600 hover:text-green-400'
                      )}
                    >
                      <ThumbsUp className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => sendFeedback(msg.id, 'down')}
                      className={cn(
                        'p-1 rounded transition-colors',
                        msg.feedback === 'down' ? 'text-red-400' : 'text-slate-600 hover:text-red-400'
                      )}
                    >
                      <ThumbsDown className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Streaming */}
        {isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-2"
          >
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0 mt-1">
              <Bot className="w-3 h-3 text-white" />
            </div>
            <div className="px-3 py-2 rounded-xl rounded-tl-sm bg-dark-border text-slate-200 text-sm max-w-[85%]">
              {streamingContent ? (
                <span>{streamingContent}<span className="inline-block w-1.5 h-4 bg-blue-400 ml-0.5 animate-pulse rounded-sm" /></span>
              ) : (
                <div className="flex items-center gap-1.5 py-0.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>
          </motion.div>
        )}

        {error && (
          <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-dark-border">
        {slideContext && (
          <div className="mb-2 flex items-center gap-1.5 px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <ChevronDown className="w-3 h-3 text-blue-400 flex-shrink-0" />
            <span className="text-xs text-blue-300 truncate">Kontext: aktueller Slide</span>
          </div>
        )}
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            disabled={isStreaming || !chatSessionId}
            placeholder="Nachricht eingeben… (Enter zum Senden)"
            className="flex-1 px-3 py-2 bg-dark-border rounded-xl text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={isStreaming || !input.trim() || !chatSessionId}
            className={cn(
              'p-2.5 rounded-xl transition-all self-end',
              isStreaming || !input.trim()
                ? 'bg-dark-border text-slate-500'
                : 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25'
            )}
          >
            {isStreaming
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Send className="w-4 h-4" />
            }
          </button>
        </div>
      </div>
    </div>
  )
}
