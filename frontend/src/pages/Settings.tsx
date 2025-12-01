import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Sun, 
  Moon, 
  Save,
  RefreshCw,
  Server,
  Cpu,
  Database,
  Palette,
  Sliders,
  Bell,
  Shield,
  HardDrive,
  Check
} from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'
import { api } from '../services/api'
import { cn } from '../utils/helpers'

interface SettingsSectionProps {
  title: string
  icon: React.ElementType
  children: React.ReactNode
}

function SettingsSection({ title, icon: Icon, children }: SettingsSectionProps) {
  return (
    <div className="bg-dark-card rounded-2xl border border-dark-border p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-xl bg-dark-border">
          <Icon className="w-5 h-5 text-slate-400" />
        </div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>
      {children}
    </div>
  )
}

interface ToggleProps {
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
}

function Toggle({ label, description, checked, onChange }: ToggleProps) {
  return (
    <div className="flex items-center justify-between py-3">
      <div>
        <p className="text-sm font-medium text-white">{label}</p>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={cn(
          "w-12 h-7 rounded-full transition-all duration-200 relative",
          checked ? "bg-blue-500" : "bg-dark-border"
        )}
      >
        <div className={cn(
          "absolute top-1 w-5 h-5 rounded-full bg-white transition-all duration-200",
          checked ? "left-6" : "left-1"
        )} />
      </button>
    </div>
  )
}

interface SelectProps {
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}

function Select({ label, value, options, onChange }: SelectProps) {
  return (
    <div className="py-3">
      <label className="block text-sm font-medium text-white mb-2">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2.5 bg-dark-border rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

interface SliderSettingProps {
  label: string
  value: number
  min: number
  max: number
  step?: number
  unit?: string
  onChange: (value: number) => void
}

function SliderSetting({ label, value, min, max, step = 1, unit = '', onChange }: SliderSettingProps) {
  return (
    <div className="py-3">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-white">{label}</label>
        <span className="text-sm text-slate-400">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full"
      />
    </div>
  )
}

export default function Settings() {
  const { isDark, toggleTheme } = useThemeStore()
  const [saved, setSaved] = useState(false)
  const [settings, setSettings] = useState({
    // Appearance
    theme: isDark ? 'dark' : 'light',
    accentColor: 'blue',
    compactMode: false,
    animations: true,
    
    // Generation Defaults
    defaultSlides: 10,
    defaultTemperature: 0.7,
    defaultStyle: 'corporate',
    autoSave: true,
    
    // LLM Settings
    llmModel: 'mistral:latest',
    maxTokens: 4096,
    timeout: 120,
    
    // Notifications
    notifyOnComplete: true,
    notifyOnError: true,
    soundEnabled: false,
  })

  const handleSave = async () => {
    // Save to localStorage
    localStorage.setItem('stratgen-settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  useEffect(() => {
    // Load from localStorage
    const stored = localStorage.getItem('stratgen-settings')
    if (stored) {
      try {
        setSettings(JSON.parse(stored))
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }
  }, [])

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Appearance */}
      <SettingsSection title="Appearance" icon={Palette}>
        <div className="space-y-1 divide-y divide-dark-border">
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-white">Theme</p>
              <p className="text-xs text-slate-500 mt-0.5">Switch between dark and light mode</p>
            </div>
            <div className="flex items-center gap-2 p-1 bg-dark-border rounded-xl">
              <button
                onClick={() => { if (isDark) toggleTheme() }}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all",
                  !isDark ? "bg-dark-card text-white" : "text-slate-500"
                )}
              >
                <Sun className="w-4 h-4" />
                Light
              </button>
              <button
                onClick={() => { if (!isDark) toggleTheme() }}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all",
                  isDark ? "bg-dark-card text-white" : "text-slate-500"
                )}
              >
                <Moon className="w-4 h-4" />
                Dark
              </button>
            </div>
          </div>
          
          <Select
            label="Accent Color"
            value={settings.accentColor}
            options={[
              { value: 'blue', label: 'Blue' },
              { value: 'green', label: 'Green' },
              { value: 'purple', label: 'Purple' },
              { value: 'orange', label: 'Orange' },
            ]}
            onChange={(v) => setSettings({ ...settings, accentColor: v })}
          />
          
          <Toggle
            label="Compact Mode"
            description="Reduce spacing and padding"
            checked={settings.compactMode}
            onChange={(v) => setSettings({ ...settings, compactMode: v })}
          />
          
          <Toggle
            label="Animations"
            description="Enable smooth transitions and effects"
            checked={settings.animations}
            onChange={(v) => setSettings({ ...settings, animations: v })}
          />
        </div>
      </SettingsSection>

      {/* Generation Defaults */}
      <SettingsSection title="Generation Defaults" icon={Sliders}>
        <div className="space-y-1 divide-y divide-dark-border">
          <SliderSetting
            label="Default Slide Count"
            value={settings.defaultSlides}
            min={5}
            max={50}
            onChange={(v) => setSettings({ ...settings, defaultSlides: v })}
          />
          
          <SliderSetting
            label="Default Creativity (Temperature)"
            value={settings.defaultTemperature}
            min={0.1}
            max={1.0}
            step={0.1}
            onChange={(v) => setSettings({ ...settings, defaultTemperature: v })}
          />
          
          <Select
            label="Default Style"
            value={settings.defaultStyle}
            options={[
              { value: 'corporate', label: 'Corporate' },
              { value: 'startup', label: 'Startup' },
              { value: 'creative', label: 'Creative' },
              { value: 'minimal', label: 'Minimal' },
              { value: 'academic', label: 'Academic' },
            ]}
            onChange={(v) => setSettings({ ...settings, defaultStyle: v })}
          />
          
          <Toggle
            label="Auto-Save"
            description="Automatically save projects while editing"
            checked={settings.autoSave}
            onChange={(v) => setSettings({ ...settings, autoSave: v })}
          />
        </div>
      </SettingsSection>

      {/* LLM Settings */}
      <SettingsSection title="LLM Configuration" icon={Cpu}>
        <div className="space-y-1 divide-y divide-dark-border">
          <Select
            label="Model"
            value={settings.llmModel}
            options={[
              { value: 'mistral:latest', label: 'Mistral (Default)' },
              { value: 'llama3:latest', label: 'Llama 3' },
              { value: 'qwen2.5:latest', label: 'Qwen 2.5' },
              { value: 'gemma2:latest', label: 'Gemma 2' },
            ]}
            onChange={(v) => setSettings({ ...settings, llmModel: v })}
          />
          
          <SliderSetting
            label="Max Tokens"
            value={settings.maxTokens}
            min={1024}
            max={8192}
            step={512}
            onChange={(v) => setSettings({ ...settings, maxTokens: v })}
          />
          
          <SliderSetting
            label="Request Timeout"
            value={settings.timeout}
            min={30}
            max={300}
            step={10}
            unit="s"
            onChange={(v) => setSettings({ ...settings, timeout: v })}
          />
        </div>
      </SettingsSection>

      {/* Notifications */}
      <SettingsSection title="Notifications" icon={Bell}>
        <div className="space-y-1 divide-y divide-dark-border">
          <Toggle
            label="Notify on Completion"
            description="Show notification when generation completes"
            checked={settings.notifyOnComplete}
            onChange={(v) => setSettings({ ...settings, notifyOnComplete: v })}
          />
          
          <Toggle
            label="Notify on Error"
            description="Show notification when an error occurs"
            checked={settings.notifyOnError}
            onChange={(v) => setSettings({ ...settings, notifyOnError: v })}
          />
          
          <Toggle
            label="Sound Effects"
            description="Play sounds for notifications"
            checked={settings.soundEnabled}
            onChange={(v) => setSettings({ ...settings, soundEnabled: v })}
          />
        </div>
      </SettingsSection>

      {/* System Actions */}
      <SettingsSection title="System" icon={Server}>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-dark-border rounded-xl">
            <div>
              <p className="text-sm font-medium text-white">Restart All Services</p>
              <p className="text-xs text-slate-500 mt-0.5">Restart API, Workers, and Redis</p>
            </div>
            <button
              onClick={async () => {
                try {
                  await api.restartSystem()
                } catch (e) {
                  console.error('Restart failed:', e)
                }
              }}
              className="flex items-center gap-2 px-4 py-2 bg-orange-500/20 text-orange-400 rounded-lg hover:bg-orange-500/30 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Restart
            </button>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-dark-border rounded-xl">
            <div>
              <p className="text-sm font-medium text-white">Clear Cache</p>
              <p className="text-xs text-slate-500 mt-0.5">Clear all cached data and embeddings</p>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors">
              <HardDrive className="w-4 h-4" />
              Clear
            </button>
          </div>
        </div>
      </SettingsSection>

      {/* Save Button */}
      <motion.button
        onClick={handleSave}
        whileTap={{ scale: 0.98 }}
        className={cn(
          "w-full py-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all",
          saved 
            ? "bg-green-500 text-white" 
            : "bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25"
        )}
      >
        {saved ? (
          <>
            <Check className="w-5 h-5" />
            Saved!
          </>
        ) : (
          <>
            <Save className="w-5 h-5" />
            Save Settings
          </>
        )}
      </motion.button>
    </div>
  )
}
