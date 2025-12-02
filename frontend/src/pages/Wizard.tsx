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
import { useSessionStore } from '../stores/sessionStore'

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
  const { addSession, setCurrentSession } = useSessionStore()
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

  // Calculate briefing quality
  const calculateBriefingQuality = (brief: string) => {
    let score = 0
    
    // Length check
    if (brief.length > 50) score += 15
    if (brief.length > 100) score += 15
    if (brief.length > 200) score += 10
    
    // Contains key elements
    if (/ziel|goal|objective/i.test(brief)) score += 10
    if (/zielgruppe|audience|target/i.test(brief)) score += 10
    if (/budget|kosten|cost/i.test(brief)) score += 10
    if (/timeline|zeit|deadline/i.test(brief)) score += 10
    if (/\d+/.test(brief)) score += 10 // Contains numbers
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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'text/*': ['.txt', '.md', '.csv']
    }
  })

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
      case 1:
        return config.company_name.trim() && config.project_name.trim()
      case 2:
        return config.brief.trim().length >= 20
      case 3:
        return true
      case 4:
        return true
      case 5:
        return true
      case 6:
        return generationComplete
      default:
        return true
    }
  }

  const handleNext = () => {
    if (currentStep < 6) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  // Polling für Session Status
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
      
      if (!createResponse.ok) {
        const errorData = await createResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to create session')
      }
      
      const session = await createResponse.json()
      setSessionId(session.id)
      
      // Add to global store
      addSession({
        id: session.id,
        name: config.project_name,
        company: config.company_name,
        status: 'created',
        phase: 'pending',
        progress: 0,
        slidesGenerated: 0,
        totalSlides: config.deck_size,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      })
      setCurrentSession(session.id)
      setCurrentPhase('Starting generation...')

      // 2. Upload files if any
      for (const uploadedFile of uploadedFiles) {
        try {
          const formData = new FormData()
          formData.append('file', uploadedFile.file)
          await fetch(`/api/sessions/${session.id}/upload`, {
            method: 'POST',
            body: formData
          })
        } catch (err) {
          console.error('File upload failed:', err)
        }
      }

      // 3. Start generation
      const startResponse = await fetch(`/api/sessions/${session.id}/start`, {
        method: 'POST'
      })
      
      if (!startResponse.ok) {
        const errorData = await startResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to start generation')
      }
      
      setCurrentPhase('Analyzing briefing...')
      
      // 4. Start polling for status
      pollingRef.current = setInterval(() => {
        pollSessionStatus(session.id)
      }, 2000)
      
      // Initial poll after short delay
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
                    initial={false}
                    animate={{
                      scale: isActive ? 1.1 : 1,
                      backgroundColor: isComplete ? '#22c55e' : isActive ? '#3b82f6' : '#2a2a3e'
                    }}
                    className={cn(
                      "w-12 h-12 rounded-full flex items-center justify-center transition-all",
                      isComplete ? "bg-green-500" : isActive ? "bg-blue-500" : "bg-dark-border"
                    )}
                  >
                    {isComplete ? (
                      <CheckCircle className="w-6 h-6 text-white" />
                    ) : (
                      <Icon className={cn("w-5 h-5", isActive ? "text-white" : "text-slate-500")} />
                    )}
                  </motion.div>
                  <span className={cn(
                    "text-xs mt-2 font-medium",
                    isActive ? "text-white" : "text-slate-500"
                  )}>
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div className={cn(
                    "w-12 lg:w-20 h-0.5 mx-1 lg:mx-2 transition-colors",
                    step.id < currentStep ? "bg-green-500" : "bg-dark-border"
                  )} />
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
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError(null)} className="p-1 hover:bg-red-500/20 rounded">
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
          className="bg-dark-card rounded-2xl border border-dark-border p-8"
        >
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white">{steps[currentStep - 1].title}</h2>
            <p className="text-slate-500 mt-1">{steps[currentStep - 1].description}</p>
          </div>

          <div className="min-h-[350px]">
            {currentStep === 1 && (
              <StepBasicInfo config={config} setConfig={setConfig} />
            )}
            {currentStep === 2 && (
              <StepBriefing 
                config={config} 
                onBriefChange={handleBriefChange}
                quality={briefingQuality}
              />
            )}
            {currentStep === 3 && (
              <StepStyle config={config} setConfig={setConfig} />
            )}
            {currentStep === 4 && (
              <StepFiles 
                uploadedFiles={uploadedFiles}
                removeFile={removeFile}
                getRootProps={getRootProps}
                getInputProps={getInputProps}
                isDragActive={isDragActive}
                getFileIcon={getFileIcon}
              />
            )}
            {currentStep === 5 && (
              <StepReview config={config} uploadedFiles={uploadedFiles} />
            )}
            {currentStep === 6 && (
              <StepGenerate 
                isGenerating={isGenerating}
                progress={progress}
                currentPhase={currentPhase}
                generationComplete={generationComplete}
                onGenerate={handleGenerate}
                onOpenEditor={openInEditor}
                onViewPipeline={viewInPipeline}
                sessionId={sessionId}
              />
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <button
          onClick={handleBack}
          disabled={currentStep === 1}
          className="flex items-center gap-2 px-6 py-3 bg-dark-card rounded-xl border border-dark-border text-slate-400 hover:bg-dark-border hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="w-4 h-4" />
          Back
        </button>
        
        {currentStep < 6 ? (
          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className={cn(
              "flex items-center gap-2 px-6 py-3 rounded-xl transition-all",
              canProceed()
                ? "bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25"
                : "bg-dark-border text-slate-500 cursor-not-allowed"
            )}
          >
            Continue
            <ChevronRight className="w-4 h-4" />
          </button>
        ) : generationComplete ? (
          <button
            onClick={openInEditor}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl text-white hover:shadow-lg hover:shadow-green-500/25 transition-all"
          >
            Open in Editor
            <ChevronRight className="w-4 h-4" />
          </button>
        ) : null}
      </div>
    </div>
  )
}

// Step 1: Basic Info
function StepBasicInfo({ config, setConfig }: { config: WizardConfig; setConfig: (c: WizardConfig) => void }) {
  return (
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
            className="w-full px-4 py-3 bg-dark-border rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="Technology">Technology</option>
            <option value="Finance">Finance</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Manufacturing">Manufacturing</option>
            <option value="Retail">Retail</option>
            <option value="Consulting">Consulting</option>
            <option value="Education">Education</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-2">Target Audience</label>
          <select 
            value={config.audience}
            onChange={(e) => setConfig({ ...config, audience: e.target.value })}
            className="w-full px-4 py-3 bg-dark-border rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="C-Level">C-Level / Executives</option>
            <option value="Management">Management</option>
            <option value="Technical">Technical Team</option>
            <option value="Sales">Sales Team</option>
            <option value="Investors">Investors</option>
            <option value="Customers">Customers</option>
            <option value="General">General Audience</option>
          </select>
        </div>
      </div>
      
      <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
        <p className="text-sm text-blue-400">
          💡 Tip: Be specific with your company and project names - they'll appear on your slides.
        </p>
      </div>
    </div>
  )
}

// Step 2: Briefing
function StepBriefing({ config, onBriefChange, quality }: { 
  config: WizardConfig
  onBriefChange: (value: string) => void
  quality: number 
}) {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-slate-400 mb-2">Project Description *</label>
        <textarea 
          value={config.brief}
          onChange={(e) => onBriefChange(e.target.value)}
          rows={10} 
          className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none" 
          placeholder="Describe your presentation requirements in detail...

Example:
Create a strategic presentation for our AI initiative in manufacturing. 

Key points to cover:
- Current challenges (3% defect rate, 2.4M EUR annual downtime costs)
- Proposed AI solutions (Predictive Maintenance, Quality Control, Process Optimization)
- Expected ROI and timeline
- Implementation roadmap

Target: Executive board approval for 500k EUR budget
Timeline: 18 months implementation" 
        />
      </div>
      
      <div className="flex items-center gap-4 p-4 bg-dark-border rounded-xl">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-slate-400">Briefing Quality</p>
            <span className={cn(
              "text-sm font-bold",
              quality >= 70 ? "text-green-400" :
              quality >= 40 ? "text-yellow-400" :
              "text-red-400"
            )}>
              {quality}%
            </span>
          </div>
          <div className="h-2 bg-dark-bg rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${quality}%` }}
              className={cn(
                "h-full rounded-full transition-colors",
                quality >= 70 ? "bg-green-500" :
                quality >= 40 ? "bg-yellow-500" :
                "bg-red-500"
              )}
            />
          </div>
        </div>
      </div>
      
      <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
        <p className="text-sm text-blue-400">
          💡 Tips for better results:
        </p>
        <ul className="text-sm text-blue-400/80 mt-2 space-y-1">
          <li>• Include specific goals and objectives</li>
          <li>• Mention your target audience</li>
          <li>• Add relevant numbers and data</li>
          <li>• Describe challenges and solutions</li>
          <li>• Specify budget and timeline if relevant</li>
        </ul>
      </div>
    </div>
  )
}

// Step 3: Style
function StepStyle({ config, setConfig }: { config: WizardConfig; setConfig: (c: WizardConfig) => void }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-2">
            Number of Slides: <span className="text-white">{config.deck_size}</span>
          </label>
          <input
            type="range"
            min="5"
            max="150"
            value={config.deck_size}
            onChange={(e) => setConfig({ ...config, deck_size: parseInt(e.target.value) })}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>5 (Quick)</span>
            <span>150 (Comprehensive)</span>
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-2">
            Creativity Level: <span className="text-white">{config.temperature}</span>
          </label>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.1"
            value={config.temperature}
            onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>Focused</span>
            <span>Creative</span>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-400 mb-3">Presentation Style</label>
        <div className="grid grid-cols-4 gap-3">
          {[
            { value: 'corporate', label: 'Corporate', desc: 'Professional & formal' },
            { value: 'startup', label: 'Startup', desc: 'Modern & dynamic' },
            { value: 'creative', label: 'Creative', desc: 'Bold & expressive' },
            { value: 'minimal', label: 'Minimal', desc: 'Clean & simple' },
          ].map((style) => (
            <button
              key={style.value}
              onClick={() => setConfig({ ...config, style: style.value })}
              className={cn(
                "p-4 rounded-xl border-2 transition-all text-left",
                config.style === style.value
                  ? "border-blue-500 bg-blue-500/10"
                  : "border-dark-border hover:border-slate-600"
              )}
            >
              <p className="font-medium text-white">{style.label}</p>
              <p className="text-xs text-slate-500 mt-1">{style.desc}</p>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-400 mb-3">Brand Colors</label>
        <div className="flex gap-6">
          {[
            { key: 'primary', label: 'Primary' },
            { key: 'secondary', label: 'Secondary' },
            { key: 'accent', label: 'Accent' },
          ].map((color) => (
            <div key={color.key} className="flex items-center gap-3">
              <input
                type="color"
                value={config.colors[color.key as keyof typeof config.colors]}
                onChange={(e) => setConfig({
                  ...config,
                  colors: { ...config.colors, [color.key]: e.target.value }
                })}
                className="w-12 h-12 rounded-xl cursor-pointer border-0"
              />
              <div>
                <p className="text-sm text-white">{color.label}</p>
                <p className="text-xs text-slate-500">{config.colors[color.key as keyof typeof config.colors]}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Step 4: Files
function StepFiles({ 
  uploadedFiles, 
  removeFile, 
  getRootProps, 
  getInputProps, 
  isDragActive,
  getFileIcon 
}: any) {
  return (
    <div className="space-y-6">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all",
          isDragActive
            ? "border-blue-500 bg-blue-500/10"
            : "border-dark-border hover:border-slate-600"
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400 font-medium">Drop files here or click to upload</p>
        <p className="text-sm text-slate-600 mt-2">
          Supports: Images, PDFs, PPTX, DOCX, XLSX, CSV, TXT
        </p>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-400">Uploaded Files ({uploadedFiles.length})</h4>
          {uploadedFiles.map((file: any, index: number) => {
            const Icon = getFileIcon(file.type)
            return (
              <div key={index} className="flex items-center gap-3 p-3 bg-dark-border rounded-xl">
                <Icon className="w-5 h-5 text-slate-400" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{file.name}</p>
                  <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="p-1.5 rounded-lg hover:bg-dark-bg text-slate-500 hover:text-red-400 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )
          })}
        </div>
      )}

      <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
        <p className="text-sm text-blue-400">
          💡 Uploaded files will be analyzed and their content integrated into your presentation where relevant.
        </p>
      </div>
    </div>
  )
}

// Step 5: Review
function StepReview({ config, uploadedFiles }: { config: WizardConfig; uploadedFiles: UploadedFile[] }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Project Details</h4>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-500">Company</span>
              <span className="text-white font-medium">{config.company_name || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Project</span>
              <span className="text-white font-medium">{config.project_name || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Industry</span>
              <span className="text-white font-medium">{config.industry}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Audience</span>
              <span className="text-white font-medium">{config.audience}</span>
            </div>
          </div>
        </div>
        
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Settings</h4>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-500">Slides</span>
              <span className="text-white font-medium">{config.deck_size}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Style</span>
              <span className="text-white font-medium capitalize">{config.style}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Creativity</span>
              <span className="text-white font-medium">{config.temperature}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Files</span>
              <span className="text-white font-medium">{uploadedFiles.length} uploaded</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">Briefing Preview</h4>
        <div className="p-4 bg-dark-border rounded-xl max-h-32 overflow-y-auto">
          <p className="text-sm text-slate-300 whitespace-pre-wrap">
            {config.brief || 'No briefing provided'}
          </p>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">Colors</h4>
        <div className="flex gap-4">
          {Object.entries(config.colors).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <div 
                className="w-8 h-8 rounded-lg border border-dark-border"
                style={{ backgroundColor: value }}
              />
              <span className="text-sm text-slate-400 capitalize">{key}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Step 6: Generate
function StepGenerate({ 
  isGenerating, 
  progress, 
  currentPhase, 
  generationComplete,
  onGenerate,
  onOpenEditor,
  onViewPipeline,
  sessionId
}: {
  isGenerating: boolean
  progress: number
  currentPhase: string
  generationComplete: boolean
  onGenerate: () => void
  onOpenEditor: () => void
  onViewPipeline: () => void
  sessionId: string | null
}) {
  if (generationComplete) {
    return (
      <div className="text-center py-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', damping: 15 }}
        >
          <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-6" />
        </motion.div>
        <h3 className="text-2xl font-bold text-white mb-2">Generation Complete!</h3>
        <p className="text-slate-400 mb-8">Your presentation is ready to view and edit.</p>
        
        <div className="flex justify-center gap-4">
          <button
            onClick={onOpenEditor}
            className="px-8 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all"
          >
            Open in Editor
          </button>
          <button
            onClick={onViewPipeline}
            className="px-8 py-3 bg-dark-border rounded-xl text-slate-400 hover:text-white transition-colors"
          >
            View Pipeline
          </button>
        </div>
        
        {sessionId && (
          <p className="text-xs text-slate-600 mt-6">Session ID: {sessionId}</p>
        )}
      </div>
    )
  }

  if (isGenerating) {
    return (
      <div className="text-center py-8">
        <Loader2 className="w-16 h-16 text-blue-500 animate-spin mx-auto mb-6" />
        <h3 className="text-xl font-semibold text-white mb-2">{currentPhase}</h3>
        <p className="text-slate-400 mb-6">Please wait while we create your presentation...</p>
        
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-slate-500">Progress</span>
            <span className="text-white font-medium">{progress.toFixed(0)}%</span>
          </div>
          <div className="h-3 bg-dark-border rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
            />
          </div>
        </div>
        
        <button
          onClick={onViewPipeline}
          className="mt-8 text-sm text-blue-400 hover:text-blue-300 transition-colors"
        >
          View detailed pipeline →
        </button>
      </div>
    )
  }

  return (
    <div className="text-center py-8">
      <Sparkles className="w-16 h-16 text-blue-500 mx-auto mb-6" />
      <h3 className="text-xl font-semibold text-white mb-2">Ready to Generate</h3>
      <p className="text-slate-400 mb-8">
        Click the button below to start creating your presentation with AI.
      </p>
      
      <button
        onClick={onGenerate}
        className="px-12 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-semibold text-lg hover:shadow-lg hover:shadow-blue-500/25 transition-all flex items-center gap-3 mx-auto"
      >
        <Sparkles className="w-5 h-5" />
        Generate Presentation
      </button>
      
      <p className="text-xs text-slate-600 mt-6">
        Estimated time: 30-60 seconds depending on slide count
      </p>
    </div>
  )
}
