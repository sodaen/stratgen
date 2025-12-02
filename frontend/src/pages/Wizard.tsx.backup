import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { 
  Building2, 
  FileText, 
  Palette, 
  Upload, 
  CheckCircle,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Loader2,
  X,
  AlertCircle,
  Image as ImageIcon,
  FileSpreadsheet,
  File
} from 'lucide-react'
import { cn } from '../utils/helpers'

const steps = [
  { id: 1, title: 'Basic Info', icon: Building2, description: 'Company & Project Details' },
  { id: 2, title: 'Briefing', icon: FileText, description: 'Describe Your Presentation' },
  { id: 3, title: 'Style', icon: Palette, description: 'Design & Settings' },
  { id: 4, title: 'Files', icon: Upload, description: 'Upload Resources' },
  { id: 5, title: 'Review', icon: CheckCircle, description: 'Confirm Settings' },
  { id: 6, title: 'Generate', icon: Sparkles, description: 'Create Presentation' },
]

interface WizardConfig {
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

interface UploadedFile {
  file: File
  name: string
  size: number
  type: string
}

export default function Wizard() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [currentPhase, setCurrentPhase] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [generationComplete, setGenerationComplete] = useState(false)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  
  const [config, setConfig] = useState<WizardConfig>({
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
  const [briefingQuality, setBriefingQuality] = useState(0)

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  const calculateBriefingQuality = (brief: string) => {
    let score = 0
    if (brief.length > 50) score += 15
    if (brief.length > 100) score += 15
    if (brief.length > 200) score += 10
    if (/ziel|goal|objective/i.test(brief)) score += 10
    if (/zielgruppe|audience|target/i.test(brief)) score += 10
    if (/budget|kosten|cost/i.test(brief)) score += 10
    if (/timeline|zeit|deadline/i.test(brief)) score += 10
    if (/\d+/.test(brief)) score += 10
    if (/problem|challenge|herausforderung/i.test(brief)) score += 10
    return Math.min(100, score)
  }

  const handleBriefChange = (value: string) => {
    setConfig({ ...config, brief: value })
    setBriefingQuality(calculateBriefingQuality(value))
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(f => ({
      file: f,
      name: f.name,
      size: f.size,
      type: f.type
    }))
    setUploadedFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return ImageIcon
    if (type.includes('spreadsheet') || type.includes('excel')) return FileSpreadsheet
    return File
  }

  const canProceed = () => {
    switch (currentStep) {
      case 1: return config.company_name.trim() && config.project_name.trim()
      case 2: return config.brief.trim().length >= 20
      case 3: return true
      case 4: return true
      case 5: return true
      case 6: return generationComplete
      default: return true
    }
  }

  const handleNext = () => {
    if (currentStep < 6) setCurrentStep(currentStep + 1)
  }

  const handleBack = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1)
  }

  const pollSessionStatus = async (sid: string) => {
    try {
      const response = await fetch(`/api/sessions/${sid}/status`)
      if (!response.ok) return
      
      const status = await response.json()
      
      setCurrentPhase(status.phase || '')
      setProgress(status.progress || 0)
      
      if (status.status === 'complete') {
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
        setIsGenerating(false)
        setProgress(100)
        setCurrentPhase('Complete!')
        setGenerationComplete(true)
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
    setIsGenerating(true)
    setError(null)
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
      
      // 3. Start polling
      pollingRef.current = setInterval(() => {
        pollSessionStatus(session.id)
      }, 2000)
      
      setTimeout(() => pollSessionStatus(session.id), 500)
      
    } catch (err: any) {
      setError(err.message || 'Failed to start generation')
      setIsGenerating(false)
    }
  }

  const openInEditor = () => {
    if (sessionId) {
      navigate(`/editor?session=${sessionId}`)
    }
  }

  const viewInPipeline = () => {
    navigate('/pipeline')
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isActive = step.id === currentStep
            const isComplete = step.id < currentStep || (step.id === 6 && generationComplete)

            return (
              <div key={step.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <motion.div 
                    animate={{
                      scale: isActive ? 1.1 : 1,
                      backgroundColor: isComplete ? '#22c55e' : isActive ? '#3b82f6' : '#2a2a3e'
                    }}
                    className="w-12 h-12 rounded-full flex items-center justify-center"
                  >
                    {isComplete ? (
                      <CheckCircle className="w-6 h-6 text-white" />
                    ) : (
                      <Icon className={cn("w-5 h-5", isActive ? "text-white" : "text-slate-500")} />
                    )}
                  </motion.div>
                  <span className={cn("text-xs mt-2 font-medium", isActive ? "text-white" : "text-slate-500")}>
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div className={cn("w-12 lg:w-20 h-0.5 mx-1 lg:mx-2", step.id < currentStep ? "bg-green-500" : "bg-dark-border")} />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400"
        >
          <AlertCircle className="w-5 h-5" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError(null)}><X className="w-4 h-4" /></button>
        </motion.div>
      )}

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="bg-dark-card rounded-2xl border border-dark-border p-8"
        >
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white">{steps[currentStep - 1].title}</h2>
            <p className="text-slate-500 mt-1">{steps[currentStep - 1].description}</p>
          </div>

          <div className="min-h-[350px]">
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">Company Name *</label>
                    <input 
                      type="text" 
                      value={config.company_name}
                      onChange={(e) => setConfig({ ...config, company_name: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50" 
                      placeholder="MusterTech GmbH" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">Project Name *</label>
                    <input 
                      type="text" 
                      value={config.project_name}
                      onChange={(e) => setConfig({ ...config, project_name: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50" 
                      placeholder="KI-Strategie 2025" 
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">Industry</label>
                    <select 
                      value={config.industry}
                      onChange={(e) => setConfig({ ...config, industry: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-border rounded-xl text-white focus:outline-none"
                    >
                      <option value="Technology">Technology</option>
                      <option value="Finance">Finance</option>
                      <option value="Healthcare">Healthcare</option>
                      <option value="Manufacturing">Manufacturing</option>
                      <option value="Consulting">Consulting</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">Target Audience</label>
                    <select 
                      value={config.audience}
                      onChange={(e) => setConfig({ ...config, audience: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-border rounded-xl text-white focus:outline-none"
                    >
                      <option value="C-Level">C-Level</option>
                      <option value="Management">Management</option>
                      <option value="Technical">Technical Team</option>
                      <option value="Investors">Investors</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Project Description *</label>
                  <textarea 
                    value={config.brief}
                    onChange={(e) => handleBriefChange(e.target.value)}
                    rows={10} 
                    className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none resize-none" 
                    placeholder="Describe your presentation requirements..." 
                  />
                </div>
                <div className="flex items-center gap-4 p-4 bg-dark-border rounded-xl">
                  <div className="flex-1">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm text-slate-400">Briefing Quality</span>
                      <span className={cn("text-sm font-bold", briefingQuality >= 70 ? "text-green-400" : briefingQuality >= 40 ? "text-yellow-400" : "text-red-400")}>
                        {briefingQuality}%
                      </span>
                    </div>
                    <div className="h-2 bg-dark-bg rounded-full overflow-hidden">
                      <div className={cn("h-full rounded-full", briefingQuality >= 70 ? "bg-green-500" : briefingQuality >= 40 ? "bg-yellow-500" : "bg-red-500")} style={{ width: `${briefingQuality}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 3 && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">Slides: {config.deck_size}</label>
                    <input type="range" min="5" max="50" value={config.deck_size} onChange={(e) => setConfig({ ...config, deck_size: parseInt(e.target.value) })} className="w-full" />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">Creativity: {config.temperature}</label>
                    <input type="range" min="0.1" max="1.0" step="0.1" value={config.temperature} onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })} className="w-full" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-3">Style</label>
                  <div className="grid grid-cols-4 gap-3">
                    {['corporate', 'startup', 'creative', 'minimal'].map((style) => (
                      <button key={style} onClick={() => setConfig({ ...config, style })} className={cn("p-4 rounded-xl border-2 capitalize", config.style === style ? "border-blue-500 bg-blue-500/10" : "border-dark-border hover:border-slate-600")}>
                        {style}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {currentStep === 4 && (
              <div className="space-y-6">
                <div {...getRootProps()} className={cn("border-2 border-dashed rounded-xl p-12 text-center cursor-pointer", isDragActive ? "border-blue-500 bg-blue-500/10" : "border-dark-border hover:border-slate-600")}>
                  <input {...getInputProps()} />
                  <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                  <p className="text-slate-400">Drop files here or click to upload</p>
                </div>
                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    {uploadedFiles.map((file, index) => {
                      const Icon = getFileIcon(file.type)
                      return (
                        <div key={index} className="flex items-center gap-3 p-3 bg-dark-border rounded-xl">
                          <Icon className="w-5 h-5 text-slate-400" />
                          <span className="flex-1 text-white truncate">{file.name}</span>
                          <button onClick={() => removeFile(index)} className="text-slate-500 hover:text-red-400"><X className="w-4 h-4" /></button>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )}

            {currentStep === 5 && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-slate-400 uppercase">Project Details</h4>
                    <div className="flex justify-between"><span className="text-slate-500">Company</span><span className="text-white">{config.company_name}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Project</span><span className="text-white">{config.project_name}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Industry</span><span className="text-white">{config.industry}</span></div>
                  </div>
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-slate-400 uppercase">Settings</h4>
                    <div className="flex justify-between"><span className="text-slate-500">Slides</span><span className="text-white">{config.deck_size}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Style</span><span className="text-white capitalize">{config.style}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Files</span><span className="text-white">{uploadedFiles.length}</span></div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-400 uppercase mb-2">Briefing</h4>
                  <div className="p-4 bg-dark-border rounded-xl max-h-32 overflow-y-auto">
                    <p className="text-slate-300 text-sm whitespace-pre-wrap">{config.brief || 'No briefing'}</p>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 6 && (
              <div className="text-center py-8">
                {generationComplete ? (
                  <>
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                      <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-6" />
                    </motion.div>
                    <h3 className="text-2xl font-bold text-white mb-2">Generation Complete!</h3>
                    <p className="text-slate-400 mb-8">Your presentation is ready.</p>
                    <div className="flex justify-center gap-4">
                      <button onClick={openInEditor} className="px-8 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-medium">Open in Editor</button>
                      <button onClick={viewInPipeline} className="px-8 py-3 bg-dark-border rounded-xl text-slate-400 hover:text-white">View Pipeline</button>
                    </div>
                  </>
                ) : isGenerating ? (
                  <>
                    <Loader2 className="w-16 h-16 text-blue-500 animate-spin mx-auto mb-6" />
                    <h3 className="text-xl font-semibold text-white mb-2">{currentPhase}</h3>
                    <p className="text-slate-400 mb-6">Please wait...</p>
                    <div className="max-w-md mx-auto">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-500">Progress</span>
                        <span className="text-white">{progress.toFixed(0)}%</span>
                      </div>
                      <div className="h-3 bg-dark-border rounded-full overflow-hidden">
                        <motion.div animate={{ width: `${progress}%` }} className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full" />
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-16 h-16 text-blue-500 mx-auto mb-6" />
                    <h3 className="text-xl font-semibold text-white mb-2">Ready to Generate</h3>
                    <p className="text-slate-400 mb-8">Click to create your presentation with AI.</p>
                    <button onClick={handleGenerate} className="px-12 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-semibold text-lg flex items-center gap-3 mx-auto">
                      <Sparkles className="w-5 h-5" />
                      Generate Presentation
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <button onClick={handleBack} disabled={currentStep === 1} className="flex items-center gap-2 px-6 py-3 bg-dark-card rounded-xl border border-dark-border text-slate-400 hover:text-white disabled:opacity-50">
          <ChevronLeft className="w-4 h-4" /> Back
        </button>
        
        {currentStep < 6 ? (
          <button onClick={handleNext} disabled={!canProceed()} className={cn("flex items-center gap-2 px-6 py-3 rounded-xl", canProceed() ? "bg-gradient-to-r from-blue-500 to-cyan-500 text-white" : "bg-dark-border text-slate-500")}>
            Continue <ChevronRight className="w-4 h-4" />
          </button>
        ) : generationComplete ? (
          <button onClick={openInEditor} className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl text-white">
            Open in Editor <ChevronRight className="w-4 h-4" />
          </button>
        ) : null}
      </div>
    </div>
  )
}
