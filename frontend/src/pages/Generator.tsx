import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Sparkles, 
  Upload, 
  Sliders, 
  Play,
  Download,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

export default function Generator() {
  const [config, setConfig] = useState({
    company: '',
    project: '',
    brief: '',
    slides: 10,
    temperature: 0.7,
    colors: {
      primary: '#1a365d',
      secondary: '#22c55e',
      accent: '#f59e0b'
    },
    style: 'corporate'
  })

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Panel - Input */}
      <div className="space-y-6">
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Briefing Input</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">Company Name</label>
              <input
                type="text"
                value={config.company}
                onChange={(e) => setConfig({...config, company: e.target.value})}
                className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                placeholder="MusterTech GmbH"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Project Name</label>
              <input
                type="text"
                value={config.project}
                onChange={(e) => setConfig({...config, project: e.target.value})}
                className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                placeholder="KI-Strategie 2025"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Briefing</label>
              <textarea
                value={config.brief}
                onChange={(e) => setConfig({...config, brief: e.target.value})}
                rows={6}
                className="w-full px-4 py-3 bg-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                placeholder="Describe your presentation requirements..."
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">
                Slides: {config.slides}
              </label>
              <input
                type="range"
                min="5"
                max="150"
                value={config.slides}
                onChange={(e) => setConfig({...config, slides: parseInt(e.target.value)})}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>5</span>
                <span>150</span>
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">
                Creativity (K-Value): {config.temperature}
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={config.temperature}
                onChange={(e) => setConfig({...config, temperature: parseFloat(e.target.value)})}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Core Colors</label>
              <div className="flex gap-4">
                {(['primary', 'secondary', 'accent'] as const).map((colorKey) => (
                  <div key={colorKey} className="flex items-center gap-2">
                    <input
                      type="color"
                      value={config.colors[colorKey]}
                      onChange={(e) => setConfig({
                        ...config, 
                        colors: {...config.colors, [colorKey]: e.target.value}
                      })}
                      className="w-10 h-10 rounded-lg cursor-pointer"
                    />
                    <span className="text-xs text-slate-500 capitalize">{colorKey}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-2 border-dashed border-dark-border rounded-xl p-8 text-center cursor-pointer hover:border-blue-500/50 transition-colors">
              <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              <p className="text-sm text-slate-400">Drop files here or click to upload</p>
              <p className="text-xs text-slate-600 mt-1">Images, PDFs, Data</p>
            </div>
          </div>
        </div>

        <button className="w-full py-4 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl text-white font-semibold flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-blue-500/25 transition-all">
          <Sparkles className="w-5 h-5" />
          Generate Presentation
        </button>
      </div>

      {/* Right Panel - Preview */}
      <div className="space-y-4">
        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Live Preview</h2>
          
          <div className="aspect-video bg-dark-border rounded-xl flex items-center justify-center">
            <p className="text-slate-500">Preview will appear here</p>
          </div>

          <div className="flex items-center justify-between mt-4">
            <button className="p-2 rounded-lg bg-dark-border hover:bg-dark-bg transition-colors">
              <ChevronLeft className="w-5 h-5 text-slate-400" />
            </button>
            <span className="text-sm text-slate-400">Slide 1 of 1</span>
            <button className="p-2 rounded-lg bg-dark-border hover:bg-dark-bg transition-colors">
              <ChevronRight className="w-5 h-5 text-slate-400" />
            </button>
          </div>
        </div>

        <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Pipeline Status</h2>
          <div className="flex items-center gap-2">
            {['Analyze', 'Structure', 'Draft', 'Critique', 'Revise', 'Visualize', 'Render', 'Export'].map((phase, i) => (
              <div key={phase} className="flex-1 text-center">
                <div className={`w-full h-2 rounded-full ${i === 0 ? 'bg-blue-500' : 'bg-dark-border'}`} />
                <p className="text-xs text-slate-500 mt-1 truncate">{phase}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-4">
          <button className="flex-1 py-3 bg-dark-card rounded-xl border border-dark-border text-slate-400 flex items-center justify-center gap-2 hover:bg-dark-border transition-colors">
            <Download className="w-4 h-4" />
            Export PPTX
          </button>
          <button className="flex-1 py-3 bg-dark-card rounded-xl border border-dark-border text-slate-400 flex items-center justify-center gap-2 hover:bg-dark-border transition-colors">
            <Download className="w-4 h-4" />
            Export PDF
          </button>
        </div>
      </div>
    </div>
  )
}
