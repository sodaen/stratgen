import { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { 
  Sparkles, 
  Upload, 
  Play,
  Download,
  ChevronLeft,
  ChevronRight,
  Loader2,
  CheckCircle,
  FileText,
  Image as ImageIcon,
  X,
  AlertCircle
} from 'lucide-react'
import { api } from '../services/api'
import { cn } from '../utils/helpers'

interface UploadedFile {
  name: string
  size: number
  type: string
}

interface GenerationConfig {
  company_name: string
  project_name: string
  industry: string
  audience: string
  brief: string
  deck_size: number
  temperature: number
  colors: {
    primary: string
    secondary: string
    accent: string
  }
  style: string
}

interface GeneratedSlide {
  type: string
  title: string
  bullets: string[]
  notes?: string
}

export default function Generator() {
  const navigate = useNavigate()
  
  const [config, setConfig] = useState<GenerationConfig>({
    company_name: '',
    project_name: '',
    industry: 'Technology',
    audience: 'C-Level',
    brief: '',
    deck_size: 10,
    temperature: 0.7,
    colors: {
      primary: '#1a365d',
      secondary: '#22c55e',
      accent: '#f59e0b'
    },
    style: 'corporate'
  })
  
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [currentPhase, setCurrentPhase] = useState<string>('')
  const [progress, setProgress] = useState(0)
  const [slides, setSlides] = useState<GeneratedSlide[]>([])
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(f => ({
      name: f.name,
      size: f.size,
      type: f.type
    }))
    setUploadedFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'text/*': ['.txt', '.md', '.csv']
    }
  })

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const pollSessionStatus = async (sid: string) => {
    try {
      const response = await fetch(`/api/sessions/${sid}/status`)
      if (!response.ok) throw new Error('Status fetch failed')
      
      const status = await response.json()
      
      setCurrentPhase(status.phase || '')
      setProgress(status.progress || 0)
      
      if (status.slides_generated > 0 && slides.length === 0) {
        // Fetch slides
        const slidesResponse = await fetch(`/api/sessions/${sid}/slides`)
        if (slidesResponse.ok) {
          const data = await slidesResponse.json()
          if (data.slides && data.slides.length > 0) {
            setSlides(data.slides)
          }
        }
      }
      
      if (status.status === 'complete') {
        // Stop polling
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
        setIsGenerating(false)
        setProgress(100)
        setCurrentPhase('Complete!')
        
        // Fetch final slides
        const slidesResponse = await fetch(`/api/sessions/${sid}/slides`)
        if (slidesResponse.ok) {
          const data = await slidesResponse.json()
          if (data.slides) {
            setSlides(data.slides)
          }
        }
      } else if (status.status === 'error') {
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
        setIsGenerating(false)
        setError(status.errors?.[0] || 'Generation failed')
      }
    } catch (err) {
      console.error('Polling error:', err)
    }
  }

  const handleGenerate = async () => {
    if (!config.brief.trim()) {
      setError('Please enter a briefing')
      return
    }

    setIsGenerating(true)
    setError(null)
    setSlides([])
    setProgress(0)
    setCurrentPhase('Creating session...')

    try {
      // 1. Create session
      const createResponse = await fetch('/api/sessions/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      })
      
      if (!createResponse.ok) throw new Error('Failed to create session')
      
      const session = await createResponse.json()
      setSessionId(session.id)
      setCurrentPhase('Starting generation...')
      
      // 2. Start generation
      const startResponse = await fetch(`/api/sessions/${session.id}/start`, {
        method: 'POST'
      })
      
      if (!startResponse.ok) throw new Error('Failed to start generation')
      
      setCurrentPhase('Analyzing...')
      
      // 3. Start polling for status
      pollingRef.current = setInterval(() => {
        pollSessionStatus(session.id)
      }, 2000)
      
      // Initial poll
      setTimeout(() => pollSessionStatus(session.id), 500)
      
    } catch (err: any) {
      setError(err.message || 'Failed to start generation')
      setIsGenerating(false)
    }
  }

  const handleCancel = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    setIsGenerating(false)
    setCurrentPhase('')
    setProgress(0)
  }

  const handleExport = async (format: 'pptx' | 'pdf') => {
    if (!sessionId) return
    
    try {
      const response = await fetch(`/api/export/${format}/${sessionId}`)
      if (!response.ok) throw new Error('Export failed')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${config.project_name || 'presentation'}.${format}`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Export failed')
    }
  }

  const openInEditor = () => {
    if (sessionId) {
      navigate(`/editor?session=${sessionId}`)
    }
  }

  const currentSlide = slides[currentSlideIndex]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Panel - Input */}
      <div className="space-y-6">
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Briefing Input</h2>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Company Name</label>
                <input
                  type="text"
                  value={config.company_name}
                  onChange={(e) => setConfig({...config, company_name: e.target.value})}
                  className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  placeholder="MusterTech GmbH"
                  disabled={isGenerating}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Project Name</label>
                <input
                  type="text"
                  value={config.project_name}
                  onChange={(e) => setConfig({...config, project_name: e.target.value})}
                  className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  placeholder="KI-Strategie 2025"
                  disabled={isGenerating}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Industry</label>
                <select
                  value={config.industry}
                  onChange={(e) => setConfig({...config, industry: e.target.value})}
                  className="w-full px-4 py-3 bg-dark-border rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  disabled={isGenerating}
                >
                  <option value="Technology">Technology</option>
                  <option value="Finance">Finance</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Retail">Retail</option>
                  <option value="Consulting">Consulting</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Target Audience</label>
                <select
                  value={config.audience}
                  onChange={(e) => setConfig({...config, audience: e.target.value})}
                  className="w-full px-4 py-3 bg-dark-border rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  disabled={isGenerating}
                >
                  <option value="C-Level">C-Level</option>
                  <option value="Management">Management</option>
                  <option value="Technical">Technical Team</option>
                  <option value="Sales">Sales Team</option>
                  <option value="Investors">Investors</option>
                  <option value="General">General Audience</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Briefing</label>
              <textarea
                value={config.brief}
                onChange={(e) => setConfig({...config, brief: e.target.value})}
                rows={6}
                className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                placeholder="Describe your presentation requirements in detail..."
                disabled={isGenerating}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">
                  Slides: <span className="text-white font-medium">{config.deck_size}</span>
                </label>
                <input
                  type="range"
                  min="5"
                  max="150"
                  value={config.deck_size}
                  onChange={(e) => setConfig({...config, deck_size: parseInt(e.target.value)})}
                  className="w-full"
                  disabled={isGenerating}
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-2">
                  Creativity: <span className="text-white font-medium">{config.temperature}</span>
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({...config, temperature: parseFloat(e.target.value)})}
                  className="w-full"
                  disabled={isGenerating}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Style</label>
              <div className="grid grid-cols-4 gap-2">
                {['corporate', 'startup', 'creative', 'minimal'].map((style) => (
                  <button
                    key={style}
                    onClick={() => setConfig({...config, style})}
                    disabled={isGenerating}
                    className={cn(
                      "py-2 px-3 rounded-lg text-sm font-medium transition-all capitalize",
                      config.style === style
                        ? "bg-blue-500 text-white"
                        : "bg-dark-border text-slate-400 hover:text-white"
                    )}
                  >
                    {style}
                  </button>
                ))}
              </div>
            </div>

            {/* File Upload */}
            <div>
              <label className="block text-sm text-slate-400 mb-2">Additional Files (optional)</label>
              <div
                {...getRootProps()}
                className={cn(
                  "border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors",
                  isDragActive 
                    ? "border-blue-500 bg-blue-500/10" 
                    : "border-dark-border hover:border-slate-600",
                  isGenerating && "opacity-50 pointer-events-none"
                )}
              >
                <input {...getInputProps()} />
                <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                <p className="text-sm text-slate-400">Drop files here or click to upload</p>
              </div>
              
              {uploadedFiles.length > 0 && (
                <div className="mt-3 space-y-2">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center gap-3 p-2 bg-dark-border rounded-lg">
                      {file.type.startsWith('image/') ? (
                        <ImageIcon className="w-4 h-4 text-slate-400" />
                      ) : (
                        <FileText className="w-4 h-4 text-slate-400" />
                      )}
                      <span className="text-sm text-slate-300 flex-1 truncate">{file.name}</span>
                      <button 
                        onClick={() => removeFile(index)}
                        className="p-1 hover:bg-dark-bg rounded text-slate-500 hover:text-red-400"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="flex-1">{error}</span>
            <button onClick={() => setError(null)} className="p-1 hover:bg-red-500/20 rounded">
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}

        {/* Generate Button */}
        {isGenerating ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">{currentPhase}</span>
              <span className="text-sm text-white font-medium">{progress.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-dark-border rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/pipeline')}
                className="flex-1 py-3 bg-dark-card border border-dark-border rounded-xl text-slate-400 hover:text-white transition-colors"
              >
                View Pipeline
              </button>
              <button
                onClick={handleCancel}
                className="flex-1 py-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400 hover:bg-red-500/30 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : slides.length > 0 ? (
          <div className="flex gap-3">
            <button 
              onClick={openInEditor}
              className="flex-1 py-4 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl text-white font-semibold flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-green-500/25 transition-all"
            >
              <CheckCircle className="w-5 h-5" />
              Open in Editor
            </button>
            <button 
              onClick={() => {
                setSlides([])
                setSessionId(null)
                setProgress(0)
              }}
              className="py-4 px-6 bg-dark-card border border-dark-border rounded-xl text-slate-400 hover:text-white transition-colors"
            >
              New
            </button>
          </div>
        ) : (
          <button 
            onClick={handleGenerate}
            className="w-full py-4 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-semibold flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-blue-500/25 transition-all"
          >
            <Sparkles className="w-5 h-5" />
            Generate Presentation
          </button>
        )}
      </div>

      {/* Right Panel - Preview */}
      <div className="space-y-4">
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Live Preview</h2>
            {slides.length > 0 && (
              <span className="text-sm text-slate-500">{slides.length} slides</span>
            )}
          </div>
          
          {/* Slide Preview */}
          <div className="aspect-video bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl flex items-center justify-center border border-dark-border overflow-hidden">
            {isGenerating && slides.length === 0 ? (
              <div className="text-center">
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin mx-auto mb-3" />
                <p className="text-slate-400">{currentPhase}</p>
              </div>
            ) : slides.length > 0 && currentSlide ? (
              <div className="w-full h-full p-6 flex flex-col">
                <h3 className="text-xl font-bold text-white mb-4">{currentSlide.title}</h3>
                <ul className="space-y-2 flex-1">
                  {currentSlide.bullets.map((bullet, i) => (
                    <li key={i} className="flex items-start gap-2 text-slate-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
                      <span className="text-sm">{bullet}</span>
                    </li>
                  ))}
                </ul>
                <div className="text-xs text-slate-600 text-right">
                  {currentSlide.type}
                </div>
              </div>
            ) : (
              <div className="text-center">
                <Play className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500">Preview will appear here</p>
              </div>
            )}
          </div>

          {/* Slide Navigation */}
          {slides.length > 0 && (
            <div className="flex items-center justify-between mt-4">
              <button
                onClick={() => setCurrentSlideIndex(Math.max(0, currentSlideIndex - 1))}
                disabled={currentSlideIndex === 0}
                className="p-2 rounded-lg bg-dark-border hover:bg-dark-bg text-slate-400 hover:text-white transition-colors disabled:opacity-50"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-2">
                {slides.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentSlideIndex(index)}
                    className={cn(
                      "w-2 h-2 rounded-full transition-all",
                      currentSlideIndex === index ? "bg-blue-500 w-4" : "bg-dark-border hover:bg-slate-600"
                    )}
                  />
                ))}
              </div>
              <button
                onClick={() => setCurrentSlideIndex(Math.min(slides.length - 1, currentSlideIndex + 1))}
                disabled={currentSlideIndex >= slides.length - 1}
                className="p-2 rounded-lg bg-dark-border hover:bg-dark-bg text-slate-400 hover:text-white transition-colors disabled:opacity-50"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>

        {/* Export Buttons */}
        {slides.length > 0 && (
          <div className="flex gap-4">
            <button 
              onClick={() => handleExport('pptx')}
              className="flex-1 py-3 bg-dark-card rounded-xl border border-dark-border text-slate-400 flex items-center justify-center gap-2 hover:bg-dark-border hover:text-white transition-colors"
            >
              <Download className="w-4 h-4" />
              Export PPTX
            </button>
            <button 
              onClick={() => handleExport('pdf')}
              className="flex-1 py-3 bg-dark-card rounded-xl border border-dark-border text-slate-400 flex items-center justify-center gap-2 hover:bg-dark-border hover:text-white transition-colors"
            >
              <Download className="w-4 h-4" />
              Export PDF
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
