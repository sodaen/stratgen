import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Building2, 
  FileText, 
  Palette, 
  Upload, 
  CheckCircle,
  Sparkles,
  ChevronRight,
  ChevronLeft
} from 'lucide-react'

const steps = [
  { id: 1, title: 'Basic Info', icon: Building2 },
  { id: 2, title: 'Briefing', icon: FileText },
  { id: 3, title: 'Style', icon: Palette },
  { id: 4, title: 'Files', icon: Upload },
  { id: 5, title: 'Review', icon: CheckCircle },
  { id: 6, title: 'Generate', icon: Sparkles },
]

export default function Wizard() {
  const [currentStep, setCurrentStep] = useState(1)

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isActive = step.id === currentStep
            const isComplete = step.id < currentStep

            return (
              <div key={step.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                    isComplete ? 'bg-green-500' :
                    isActive ? 'bg-blue-500' :
                    'bg-dark-border'
                  }`}>
                    <Icon className={`w-5 h-5 ${isComplete || isActive ? 'text-white' : 'text-slate-500'}`} />
                  </div>
                  <span className={`text-xs mt-2 ${isActive ? 'text-white' : 'text-slate-500'}`}>
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-0.5 mx-2 ${
                    step.id < currentStep ? 'bg-green-500' : 'bg-dark-border'
                  }`} />
                )}
              </div>
            )
          })}
        </div>
      </div>

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
          <h2 className="text-2xl font-bold text-white mb-6">
            {steps[currentStep - 1].title}
          </h2>

          {/* Step Content */}
          <div className="min-h-[300px]">
            {currentStep === 1 && <StepBasicInfo />}
            {currentStep === 2 && <StepBriefing />}
            {currentStep === 3 && <StepStyle />}
            {currentStep === 4 && <StepFiles />}
            {currentStep === 5 && <StepReview />}
            {currentStep === 6 && <StepGenerate />}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className="flex items-center gap-2 px-6 py-3 bg-dark-card rounded-xl border border-dark-border text-slate-400 hover:bg-dark-border transition-colors disabled:opacity-50"
        >
          <ChevronLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={() => setCurrentStep(Math.min(6, currentStep + 1))}
          disabled={currentStep === 6}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white hover:shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-50"
        >
          {currentStep === 5 ? 'Generate' : 'Continue'}
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

function StepBasicInfo() {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm text-slate-400 mb-2">Company Name</label>
        <input type="text" className="w-full px-4 py-3 bg-dark-border rounded-xl text-white" placeholder="Enter company name" />
      </div>
      <div>
        <label className="block text-sm text-slate-400 mb-2">Industry</label>
        <select className="w-full px-4 py-3 bg-dark-border rounded-xl text-white">
          <option>Technology</option>
          <option>Finance</option>
          <option>Healthcare</option>
          <option>Manufacturing</option>
          <option>Retail</option>
        </select>
      </div>
      <div>
        <label className="block text-sm text-slate-400 mb-2">Target Audience</label>
        <input type="text" className="w-full px-4 py-3 bg-dark-border rounded-xl text-white" placeholder="e.g., C-Level, IT Department" />
      </div>
    </div>
  )
}

function StepBriefing() {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm text-slate-400 mb-2">Project Description</label>
        <textarea rows={8} className="w-full px-4 py-3 bg-dark-border rounded-xl text-white resize-none" placeholder="Describe your presentation requirements in detail..." />
      </div>
      <div className="flex items-center gap-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
        <div className="flex-1">
          <p className="text-sm text-blue-400">Briefing Quality</p>
          <div className="h-2 bg-dark-border rounded-full mt-2">
            <div className="h-full w-1/4 bg-blue-500 rounded-full" />
          </div>
        </div>
        <span className="text-2xl font-bold text-blue-400">25%</span>
      </div>
    </div>
  )
}

function StepStyle() {
  return (
    <div className="space-y-4">
      <p className="text-slate-400">Style configuration coming soon...</p>
    </div>
  )
}

function StepFiles() {
  return (
    <div className="border-2 border-dashed border-dark-border rounded-xl p-12 text-center">
      <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
      <p className="text-slate-400">Drop files here or click to upload</p>
      <p className="text-sm text-slate-600 mt-2">Supports: Images, PDFs, PPTX, DOCX, XLSX</p>
    </div>
  )
}

function StepReview() {
  return (
    <div className="space-y-4">
      <p className="text-slate-400">Review your configuration before generating...</p>
    </div>
  )
}

function StepGenerate() {
  return (
    <div className="text-center py-12">
      <Sparkles className="w-16 h-16 text-blue-500 mx-auto mb-4" />
      <h3 className="text-xl font-semibold text-white">Ready to Generate</h3>
      <p className="text-slate-400 mt-2">Click the button below to start generating your presentation</p>
    </div>
  )
}
