import { useState, useEffect } from 'react'
import { motion, AnimatePresence, Reorder } from 'framer-motion'
import { 
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  Copy,
  GripVertical,
  Sparkles,
  RefreshCw,
  Wand2,
  Type,
  AlignLeft,
  List,
  Image,
  BarChart3,
  Save,
  Download,
  Undo,
  Redo,
  Check,
  X,
  Loader2,
  MessageSquare,
  Zap,
  Minimize2,
  Maximize2
} from 'lucide-react'
import { cn } from '../utils/helpers'

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
  { icon: Minimize2, label: 'Kürzer', prompt: 'Make this more concise' },
  { icon: Maximize2, label: 'Ausführlicher', prompt: 'Add more detail' },
  { icon: Type, label: 'Formeller', prompt: 'Make this more formal' },
  { icon: MessageSquare, label: 'Einfacher', prompt: 'Simplify the language' },
  { icon: List, label: '+ Bullet', prompt: 'Add another bullet point' },
  { icon: Zap, label: 'Überzeugender', prompt: 'Make this more persuasive' },
]

// Demo slides
const demoSlides: Slide[] = [
  {
    id: '1',
    type: 'title',
    title: 'KI-Strategie 2025',
    bullets: ['MusterTech GmbH', 'Strategische Roadmap für KI-Integration'],
    notes: 'Begrüßung und Vorstellung des Teams',
    layout: 'title-only'
  },
  {
    id: '2',
    type: 'agenda',
    title: 'Agenda',
    bullets: [
      'Ausgangssituation & Herausforderungen',
      'KI-Potenziale in der Fertigung',
      'Unsere Lösungsstrategie',
      'ROI & Business Case',
      'Implementierungsplan',
      'Nächste Schritte'
    ],
    notes: 'Überblick über die Präsentation geben',
    layout: 'title-bullets'
  },
  {
    id: '3',
    type: 'content',
    title: 'Ausgangssituation',
    bullets: [
      'Steigende Produktionskosten durch manuelle Prozesse',
      'Qualitätsprobleme führen zu 3% Ausschussrate',
      'Ungeplante Ausfallzeiten kosten 2.4M EUR/Jahr',
      'Wettbewerber setzen bereits auf KI-Lösungen'
    ],
    notes: 'Zahlen aus dem Q3 Report verwenden',
    layout: 'title-bullets'
  },
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
      {/* Title */}
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

      {/* Bullets */}
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

      {/* Slide number */}
      <div className="text-xs text-slate-600 text-right">
        Slide {slide.id}
      </div>
    </div>
  )
}

function AIVariant({ variant, onSelect }: { variant: Slide; onSelect: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-dark-border rounded-xl p-4 cursor-pointer hover:ring-2 hover:ring-blue-500/50 transition-all"
      onClick={onSelect}
    >
      <h4 className="text-sm font-medium text-white mb-2 truncate">{variant.title}</h4>
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
  const [slides, setSlides] = useState<Slide[]>(demoSlides)
  const [selectedSlide, setSelectedSlide] = useState<string>('2')
  const [isGenerating, setIsGenerating] = useState(false)
  const [customPrompt, setCustomPrompt] = useState('')
  const [variants, setVariants] = useState<Slide[]>([])
  const [showVariants, setShowVariants] = useState(false)
  const [saved, setSaved] = useState(false)

  const currentSlide = slides.find(s => s.id === selectedSlide) || slides[0]
  const currentIndex = slides.findIndex(s => s.id === selectedSlide)

  const handleSlideUpdate = (updatedSlide: Slide) => {
    setSlides(slides.map(s => s.id === updatedSlide.id ? updatedSlide : s))
  }

  const handleQuickAction = async (prompt: string) => {
    setIsGenerating(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Generate mock variants
    const mockVariants: Slide[] = [
      { ...currentSlide, id: 'var-a', title: currentSlide.title + ' (Variante A)', bullets: currentSlide.bullets.map(b => b + ' - optimiert') },
      { ...currentSlide, id: 'var-b', title: currentSlide.title + ' (Variante B)', bullets: currentSlide.bullets.slice(0, -1) },
      { ...currentSlide, id: 'var-c', title: currentSlide.title + ' (Variante C)', bullets: [...currentSlide.bullets, 'Neuer Punkt hinzugefügt'] },
    ]
    
    setVariants(mockVariants)
    setShowVariants(true)
    setIsGenerating(false)
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
      title: 'Neue Slide',
      bullets: ['Punkt 1', 'Punkt 2'],
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

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="grid grid-cols-12 gap-6 h-[calc(100vh-180px)]">
      {/* Slide List - Left */}
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
                
                {/* Delete button */}
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

      {/* Preview & Editor - Center */}
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
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg transition-all",
                saved 
                  ? "bg-green-500/20 text-green-400"
                  : "bg-dark-border text-slate-400 hover:text-white"
              )}
            >
              {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
              {saved ? 'Saved!' : 'Save'}
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg text-white">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {/* Slide Preview */}
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
              {slides.map((slide, index) => (
                <button
                  key={slide.id}
                  onClick={() => setSelectedSlide(slide.id)}
                  className={cn(
                    "w-2 h-2 rounded-full transition-all",
                    selectedSlide === slide.id ? "bg-blue-500 w-4" : "bg-dark-border hover:bg-slate-600"
                  )}
                />
              ))}
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
                    onSelect={() => handleSelectVariant(variant)}
                  />
                ))}
              </div>
              
              <button
                onClick={() => handleQuickAction('regenerate')}
                className="mt-4 w-full py-2 border border-dark-border rounded-lg text-slate-400 hover:text-white hover:border-slate-600 transition-colors flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Regenerate All
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Properties & AI Assist - Right */}
      <div className="col-span-3 space-y-4">
        {/* Properties */}
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
                  className="flex items-center gap-2 px-3 py-2 bg-dark-border rounded-lg text-slate-400 hover:text-white hover:bg-dark-bg transition-colors text-xs"
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
                isGenerating
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
          onClick={() => handleQuickAction('regenerate full slide')}
          disabled={isGenerating}
          className="w-full py-3 bg-dark-card border border-dark-border rounded-xl text-slate-400 hover:text-white hover:border-slate-600 transition-colors flex items-center justify-center gap-2"
        >
          <RefreshCw className={cn("w-4 h-4", isGenerating && "animate-spin")} />
          Regenerate Entire Slide
        </button>
      </div>
    </div>
  )
}
