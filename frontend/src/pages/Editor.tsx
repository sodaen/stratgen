import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence, Reorder } from 'framer-motion'
import { 
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  GripVertical,
  Sparkles,
  RefreshCw,
  Wand2,
  Save,
  Download,
  Undo,
  Redo,
  Check,
  X,
  Loader2,
  Minimize2,
  Maximize2,
  List,
  Type,
  MessageSquare,
  Zap,
  ArrowLeft
} from 'lucide-react'
import { cn } from '../utils/helpers'
import ChatSidebar from '../components/ChatSidebar'
import { api } from '../services/api'

interface Slide {
  id: string
  type: string
  title: string
  bullets: string[]
  notes: string
  layout: string
}

const slideTypes = [
  { value: 'title', label: 'Title Slide' },
  { value: 'agenda', label: 'Agenda' },
  { value: 'content', label: 'Content' },
  { value: 'bullets', label: 'Bullet Points' },
  { value: 'comparison', label: 'Comparison' },
  { value: 'chart', label: 'Chart/Data' },
  { value: 'quote', label: 'Quote' },
  { value: 'image', label: 'Image Focus' },
  { value: 'cta', label: 'Call to Action' },
]

const layouts = [
  { value: 'title-only', label: 'Title Only' },
  { value: 'title-content', label: 'Title + Content' },
  { value: 'two-column', label: 'Two Columns' },
  { value: 'title-bullets', label: 'Title + Bullets' },
  { value: 'full-image', label: 'Full Image' },
]

const quickActions = [
  { icon: Minimize2, label: 'Kürzer', prompt: 'Make this slide more concise, reduce to key points' },
  { icon: Maximize2, label: 'Ausführlicher', prompt: 'Expand this slide with more detail and examples' },
  { icon: Type, label: 'Formeller', prompt: 'Rewrite in a more formal, professional tone' },
  { icon: MessageSquare, label: 'Einfacher', prompt: 'Simplify the language for a general audience' },
  { icon: List, label: '+ Bullet', prompt: 'Add one more relevant bullet point' },
  { icon: Zap, label: 'Überzeugender', prompt: 'Make this more persuasive and compelling' },
]

function SlidePreview({ slide, isEditing, onUpdate }: { 
  slide: Slide
  isEditing: boolean
  onUpdate: (slide: Slide) => void 
}) {
  const [editingTitle, setEditingTitle] = useState(false)
  const [editingBullets, setEditingBullets] = useState<number | null>(null)

  return (
    <div className="aspect-video bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-8 flex flex-col border border-dark-border">
      {editingTitle ? (
        <input
          type="text"
          value={slide.title}
          onChange={(e) => onUpdate({ ...slide, title: e.target.value })}
          onBlur={() => setEditingTitle(false)}
          onKeyDown={(e) => e.key === 'Enter' && setEditingTitle(false)}
          autoFocus
          className="text-2xl font-bold text-white bg-transparent border-b-2 border-blue-500 focus:outline-none mb-6"
        />
      ) : (
        <h2 
          onClick={() => isEditing && setEditingTitle(true)}
          className={cn(
            "text-2xl font-bold text-white mb-6",
            isEditing && "cursor-text hover:bg-white/5 rounded px-1 -mx-1"
          )}
        >
          {slide.title}
        </h2>
      )}

      <ul className="space-y-3 flex-1">
        {slide.bullets.map((bullet, index) => (
          <li key={index} className="flex items-start gap-3">
            <span className="w-2 h-2 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
            {editingBullets === index ? (
              <input
                type="text"
                value={bullet}
                onChange={(e) => {
                  const newBullets = [...slide.bullets]
                  newBullets[index] = e.target.value
                  onUpdate({ ...slide, bullets: newBullets })
                }}
                onBlur={() => setEditingBullets(null)}
                onKeyDown={(e) => e.key === 'Enter' && setEditingBullets(null)}
                autoFocus
                className="flex-1 text-slate-300 bg-transparent border-b border-blue-500 focus:outline-none"
              />
            ) : (
              <span 
                onClick={() => isEditing && setEditingBullets(index)}
                className={cn(
                  "text-slate-300",
                  isEditing && "cursor-text hover:bg-white/5 rounded px-1 -mx-1"
                )}
              >
                {bullet}
              </span>
            )}
          </li>
        ))}
      </ul>

      <div className="flex items-center justify-between text-xs text-slate-600">
        <span className="capitalize">{slide.type}</span>
        <span>Slide {slide.id}</span>
      </div>
    </div>
  )
}

function AIVariant({ variant, index, onSelect }: { variant: Slide; index: number; onSelect: () => void }) {
  const labels = ['A', 'B', 'C']
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-dark-border rounded-xl p-4 cursor-pointer hover:ring-2 hover:ring-blue-500/50 transition-all"
      onClick={onSelect}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex items-center justify-center">
          {labels[index]}
        </span>
        <h4 className="text-sm font-medium text-white truncate">{variant.title}</h4>
      </div>
      <ul className="space-y-1">
        {variant.bullets.slice(0, 3).map((bullet, i) => (
          <li key={i} className="text-xs text-slate-500 truncate flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-slate-600" />
            {bullet}
          </li>
        ))}
        {variant.bullets.length > 3 && (
          <li className="text-xs text-slate-600">+{variant.bullets.length - 3} more</li>
        )}
      </ul>
      <button className="mt-3 w-full py-1.5 bg-blue-500/20 text-blue-400 rounded-lg text-xs font-medium hover:bg-blue-500/30 transition-colors">
        Use This
      </button>
    </motion.div>
  )
}

export default function Editor() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('session')
  
  const [slides, setSlides] = useState<Slide[]>([])
  const [selectedSlide, setSelectedSlide] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [customPrompt, setCustomPrompt] = useState('')
  const [variants, setVariants] = useState<Slide[]>([])
  const [showVariants, setShowVariants] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [projectName, setProjectName] = useState('Untitled Project')

  // Load slides from session or create empty
  useEffect(() => {
    const loadSlides = async () => {
      setIsLoading(true)
      
      if (sessionId) {
        try {
          const session = await api.getSessionStatus(sessionId)
          if (session.config?.project_name) {
            setProjectName(session.config.project_name)
          }
          
          // Try to get generated slides
          const response = await fetch(`/api/sessions/${sessionId}/slides`)
          if (response.ok) {
            const data = await response.json()
            if (data.slides && data.slides.length > 0) {
              const loadedSlides = data.slides.map((s: any, i: number) => ({
                id: String(i + 1),
                type: s.type || 'content',
                title: s.title || 'Untitled',
                bullets: s.bullets || [],
                notes: s.notes || '',
                layout: s.layout_hint || 'title-bullets'
              }))
              setSlides(loadedSlides)
              setSelectedSlide(loadedSlides[0].id)
              setIsLoading(false)
              return
            }
          }
        } catch (err) {
          console.error('Failed to load session:', err)
        }
      }
      
      // Default empty slide
      const defaultSlide: Slide = {
        id: '1',
        type: 'title',
        title: 'New Presentation',
        bullets: ['Click to edit', 'Add your content here'],
        notes: '',
        layout: 'title-only'
      }
      setSlides([defaultSlide])
      setSelectedSlide('1')
      setIsLoading(false)
    }
    
    loadSlides()
  }, [sessionId])

  const currentSlide = slides.find(s => s.id === selectedSlide) || slides[0]
  const currentIndex = slides.findIndex(s => s.id === selectedSlide)

  const handleSlideUpdate = (updatedSlide: Slide) => {
    setSlides(slides.map(s => s.id === updatedSlide.id ? updatedSlide : s))
  }

  const handleQuickAction = async (prompt: string) => {
    if (!currentSlide) return
    
    setIsGenerating(true)
    setError(null)
    
    try {
      // Call backend to generate variants
      const response = await fetch('/api/orchestrator/slide-variants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slide: currentSlide,
          prompt: prompt,
          count: 3
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.variants && data.variants.length > 0) {
          setVariants(data.variants.map((v: any, i: number) => ({
            ...currentSlide,
            id: `var-${i}`,
            title: v.title || currentSlide.title,
            bullets: v.bullets || currentSlide.bullets
          })))
          setShowVariants(true)
        } else {
          // Fallback: simple local generation
          generateLocalVariants(prompt)
        }
      } else {
        generateLocalVariants(prompt)
      }
    } catch (err) {
      // Fallback to local generation
      generateLocalVariants(prompt)
    } finally {
      setIsGenerating(false)
    }
  }

  const generateLocalVariants = (prompt: string) => {
    // Local fallback variant generation
    const mockVariants: Slide[] = [
      { 
        ...currentSlide, 
        id: 'var-a', 
        title: currentSlide.title,
        bullets: currentSlide.bullets.map(b => b.length > 50 ? b.substring(0, 50) + '...' : b + ' (optimized)')
      },
      { 
        ...currentSlide, 
        id: 'var-b', 
        bullets: currentSlide.bullets.slice(0, Math.max(2, currentSlide.bullets.length - 1))
      },
      { 
        ...currentSlide, 
        id: 'var-c', 
        bullets: [...currentSlide.bullets, 'Additional insight based on context']
      },
    ]
    
    setVariants(mockVariants)
    setShowVariants(true)
  }

  const handleSelectVariant = (variant: Slide) => {
    handleSlideUpdate({ ...variant, id: currentSlide.id })
    setShowVariants(false)
    setVariants([])
  }

  const handleAddSlide = () => {
    const newSlide: Slide = {
      id: String(Date.now()),
      type: 'content',
      title: 'New Slide',
      bullets: ['Point 1', 'Point 2'],
      notes: '',
      layout: 'title-bullets'
    }
    setSlides([...slides, newSlide])
    setSelectedSlide(newSlide.id)
  }

  const handleDeleteSlide = (id: string) => {
    if (slides.length <= 1) return
    const newSlides = slides.filter(s => s.id !== id)
    setSlides(newSlides)
    if (selectedSlide === id) {
      setSelectedSlide(newSlides[0].id)
    }
  }

  const handleDuplicateSlide = () => {
    if (!currentSlide) return
    const newSlide: Slide = {
      ...currentSlide,
      id: String(Date.now()),
      title: currentSlide.title + ' (Copy)'
    }
    const insertIndex = currentIndex + 1
    const newSlides = [...slides]
    newSlides.splice(insertIndex, 0, newSlide)
    setSlides(newSlides)
    setSelectedSlide(newSlide.id)
  }

  const handleSave = async () => {
    // Save to backend if we have a session
    if (sessionId) {
      try {
        await fetch(`/api/sessions/${sessionId}/slides`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slides })
        })
      } catch (err) {
        console.error('Save failed:', err)
      }
    }
    
    // Also save to localStorage as backup
    localStorage.setItem('stratgen-editor-slides', JSON.stringify(slides))
    
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleExport = async (format: 'pptx' | 'pdf') => {
    try {
      const endpoint = sessionId 
        ? `/api/export/${format}/${sessionId}`
        : `/api/export/${format}`
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slides })
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${projectName}.${format}`
        a.click()
        window.URL.revokeObjectURL(url)
      } else {
        setError('Export failed')
      }
    } catch (err) {
      setError('Export failed')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading slides...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-dark-card text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-white">{projectName}</h1>
            <p className="text-sm text-slate-500">
              {slides.length} slides {sessionId && `• Session: ${sessionId}`}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport('pptx')}
            className="flex items-center gap-2 px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <Download className="w-4 h-4" />
            PPTX
          </button>
          <button
            onClick={handleSave}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg transition-all",
              saved 
                ? "bg-green-500/20 text-green-400"
                : "bg-gradient-to-r from-blue-500 to-cyan-500 text-white"
            )}
          >
            {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {saved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400"
        >
          <span className="flex-1">{error}</span>
          <button onClick={() => setError(null)}><X className="w-4 h-4" /></button>
        </motion.div>
      )}

      <div className={cn("grid gap-6 h-[calc(100vh-220px)]", showChat ? "grid-cols-12" : "grid-cols-12")}>
        {/* Slide List */}
        <div className="col-span-2 bg-dark-card rounded-2xl border border-dark-border p-4 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-400 mb-4">Slides</h3>
          
          <Reorder.Group 
            axis="y" 
            values={slides} 
            onReorder={setSlides}
            className="flex-1 space-y-2 overflow-y-auto"
          >
            {slides.map((slide, index) => (
              <Reorder.Item key={slide.id} value={slide}>
                <motion.div
                  onClick={() => setSelectedSlide(slide.id)}
                  className={cn(
                    "group relative p-2 rounded-xl cursor-pointer transition-all",
                    selectedSlide === slide.id 
                      ? "bg-blue-500/20 border border-blue-500/30" 
                      : "hover:bg-dark-border"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <GripVertical className="w-4 h-4 text-slate-600 opacity-0 group-hover:opacity-100 cursor-grab" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{index + 1}. {slide.title}</p>
                      <p className="text-xs text-slate-500 capitalize">{slide.type}</p>
                    </div>
                  </div>
                  
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteSlide(slide.id) }}
                    className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-all"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </motion.div>
              </Reorder.Item>
            ))}
          </Reorder.Group>

          <button
            onClick={handleAddSlide}
            className="mt-4 w-full py-2 border border-dashed border-dark-border rounded-xl text-slate-500 hover:text-white hover:border-slate-600 transition-colors flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Slide
          </button>
        </div>

        {/* Preview & Editor */}
        <div className="col-span-7 flex flex-col gap-4">
          {/* Toolbar */}
          <div className="flex items-center justify-between bg-dark-card rounded-xl border border-dark-border p-2">
            <div className="flex items-center gap-2">
              <button className="p-2 rounded-lg hover:bg-dark-border text-slate-400 hover:text-white transition-colors">
                <Undo className="w-4 h-4" />
              </button>
              <button className="p-2 rounded-lg hover:bg-dark-border text-slate-400 hover:text-white transition-colors">
                <Redo className="w-4 h-4" />
              </button>
              <div className="w-px h-6 bg-dark-border mx-2" />
              <span className="text-sm text-slate-400">
                Slide {currentIndex + 1} of {slides.length}
              </span>
            </div>
            
            <button
              onClick={handleDuplicateSlide}
              className="flex items-center gap-2 px-3 py-1.5 bg-dark-border rounded-lg text-slate-400 hover:text-white transition-colors text-sm"
            >
              Duplicate
            </button>
          </div>

          {/* Slide Preview */}
          {currentSlide && (
            <div className="flex-1 bg-dark-card rounded-2xl border border-dark-border p-6">
              <SlidePreview 
                slide={currentSlide} 
                isEditing={true}
                onUpdate={handleSlideUpdate}
              />
              
              {/* Navigation */}
              <div className="flex items-center justify-between mt-4">
                <button
                  onClick={() => currentIndex > 0 && setSelectedSlide(slides[currentIndex - 1].id)}
                  disabled={currentIndex === 0}
                  className="p-2 rounded-lg bg-dark-border hover:bg-dark-bg text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                
                <div className="flex items-center gap-2">
                  {slides.slice(0, 10).map((slide, index) => (
                    <button
                      key={slide.id}
                      onClick={() => setSelectedSlide(slide.id)}
                      className={cn(
                        "w-2 h-2 rounded-full transition-all",
                        selectedSlide === slide.id ? "bg-blue-500 w-4" : "bg-dark-border hover:bg-slate-600"
                      )}
                    />
                  ))}
                  {slides.length > 10 && <span className="text-xs text-slate-500">+{slides.length - 10}</span>}
                </div>
                
                <button
                  onClick={() => currentIndex < slides.length - 1 && setSelectedSlide(slides[currentIndex + 1].id)}
                  disabled={currentIndex === slides.length - 1}
                  className="p-2 rounded-lg bg-dark-border hover:bg-dark-bg text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          {/* AI Variants */}
          <AnimatePresence>
            {showVariants && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="bg-dark-card rounded-2xl border border-blue-500/30 p-4"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                    <h3 className="font-medium text-white">AI Variants</h3>
                  </div>
                  <button
                    onClick={() => setShowVariants(false)}
                    className="p-1 rounded hover:bg-dark-border text-slate-400"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  {variants.map((variant, index) => (
                    <AIVariant 
                      key={variant.id} 
                      variant={variant}
                      index={index}
                      onSelect={() => handleSelectVariant(variant)}
                    />
                  ))}
                </div>
                
                <button
                  onClick={() => handleQuickAction('regenerate with different approach')}
                  disabled={isGenerating}
                  className="mt-4 w-full py-2 border border-dark-border rounded-lg text-slate-400 hover:text-white hover:border-slate-600 transition-colors flex items-center justify-center gap-2"
                >
                  <RefreshCw className={cn("w-4 h-4", isGenerating && "animate-spin")} />
                  Regenerate All
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Properties & AI Assist */}
        <div className="col-span-3 space-y-4">
          {/* Properties */}
          {currentSlide && (
            <div className="bg-dark-card rounded-2xl border border-dark-border p-4">
              <h3 className="text-sm font-semibold text-slate-400 mb-4">Properties</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Type</label>
                  <select
                    value={currentSlide.type}
                    onChange={(e) => handleSlideUpdate({ ...currentSlide, type: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-border rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  >
                    {slideTypes.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Layout</label>
                  <select
                    value={currentSlide.layout}
                    onChange={(e) => handleSlideUpdate({ ...currentSlide, layout: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-border rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  >
                    {layouts.map(l => (
                      <option key={l.value} value={l.value}>{l.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Speaker Notes</label>
                  <textarea
                    value={currentSlide.notes}
                    onChange={(e) => handleSlideUpdate({ ...currentSlide, notes: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 bg-dark-border rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                    placeholder="Add speaker notes..."
                  />
                </div>
              </div>
            </div>
          )}

          {/* AI Assist */}
          <div className="bg-dark-card rounded-2xl border border-dark-border p-4">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-blue-400" />
              <h3 className="text-sm font-semibold text-white">AI Assist</h3>
            </div>
            
            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              {quickActions.map((action) => {
                const Icon = action.icon
                return (
                  <button
                    key={action.label}
                    onClick={() => handleQuickAction(action.prompt)}
                    disabled={isGenerating}
                    className="flex items-center gap-2 px-3 py-2 bg-dark-border rounded-lg text-slate-400 hover:text-white hover:bg-dark-bg transition-colors text-xs disabled:opacity-50"
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {action.label}
                  </button>
                )
              })}
            </div>
            
            {/* Custom Prompt */}
            <div className="space-y-2">
              <label className="block text-xs text-slate-500">Custom Prompt</label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 bg-dark-border rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                placeholder="Describe what you want to change..."
              />
              <button
                onClick={() => handleQuickAction(customPrompt)}
                disabled={isGenerating || !customPrompt.trim()}
                className={cn(
                  "w-full py-2 rounded-lg font-medium flex items-center justify-center gap-2 transition-all",
                  isGenerating || !customPrompt.trim()
                    ? "bg-dark-border text-slate-500"
                    : "bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25"
                )}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4" />
                    Apply
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Regenerate Full Slide */}
          <button
            onClick={() => handleQuickAction('Completely regenerate this slide with a fresh approach while keeping the same topic')}
            disabled={isGenerating}
            className="w-full py-3 bg-dark-card border border-dark-border rounded-xl text-slate-400 hover:text-white hover:border-slate-600 transition-colors flex items-center justify-center gap-2"
          >
            <RefreshCw className={cn("w-4 h-4", isGenerating && "animate-spin")} />
            Regenerate Entire Slide
          </button>
        </div>

        {/* Chat Sidebar */}
        {showChat && (
          <div className="col-span-3">
            <ChatSidebar
              slideContext={currentSlide ? `${currentSlide.title}
${currentSlide.bullets?.join("
")}` : undefined}
              onClose={() => setShowChat(false)}
              className="h-full"
            />
          </div>
        )}
      </div>
    </div>
  )
}
