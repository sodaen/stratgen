import { useState, useEffect } from 'react'

import { 
  Sun, Moon, Save, RefreshCw, Server, Cpu, Database,
  Palette, Sliders, Bell, HardDrive, Check, RotateCcw,
  Volume2, VolumeX
} from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useNotificationStore, notify } from '../stores/notificationStore'

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
        <p className="text-white font-medium">{label}</p>
        {description && <p className="text-sm text-slate-400">{description}</p>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`w-12 h-6 rounded-full transition-colors ${
          checked ? 'bg-blue-500' : 'bg-dark-border'
        }`}
      >
        <div
          className={`w-5 h-5 rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-0.5'
          }`}
        />
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
    <div className="flex items-center justify-between py-3">
      <p className="text-white font-medium">{label}</p>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-dark-border border border-dark-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
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
        <p className="text-white font-medium">{label}</p>
        <span className="text-blue-400 font-mono">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-dark-border rounded-lg appearance-none cursor-pointer accent-blue-500"
      />
    </div>
  )
}

export default function Settings() {
  const { isDark, toggleTheme } = useThemeStore()
  const settings = useSettingsStore()
  const notifSettings = useNotificationStore()
  const [saved, setSaved] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [availableModels, setAvailableModels] = useState<string[]>(['mistral:latest'])

  // Fetch available models
  useEffect(() => {
    fetch('/api/ollama/models')
      .then(r => r.json())
      .then(data => {
        if (data.models) {
          setAvailableModels(data.models.map((m: any) => m.name || m))
        }
      })
      .catch(() => {})
  }, [])

  const handleSave = async () => {
    setSyncing(true)
    try {
      await settings.syncWithBackend()
      setSaved(true)
      notify.success('Einstellungen gespeichert', 'Alle Einstellungen wurden erfolgreich gespeichert.')
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      notify.error('Fehler', 'Einstellungen konnten nicht gespeichert werden.')
    }
    setSyncing(false)
  }

  const handleReset = () => {
    settings.resetToDefaults()
    notify.info('Zurückgesetzt', 'Einstellungen wurden auf Standardwerte zurückgesetzt.')
  }

  const testNotification = () => {
    notify.success('Test Notification', 'Das ist eine Test-Benachrichtigung!')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Einstellungen</h1>
          <p className="text-gray-400 text-sm mt-1">Konfiguriere Stratgen nach deinen Wünschen</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 bg-dark-card hover:bg-dark-border rounded-lg transition-colors text-gray-400"
          >
            <RotateCcw className="w-4 h-4" />
            Zurücksetzen
          </button>
          <button
            onClick={handleSave}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors text-white disabled:opacity-50"
          >
            {syncing ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : saved ? (
              <Check className="w-4 h-4" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saved ? 'Gespeichert!' : 'Speichern'}
          </button>
        </div>
      </div>

      {/* Appearance */}
      <SettingsSection title="Erscheinungsbild" icon={Palette}>
        <div className="space-y-1 divide-y divide-dark-border">
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-white font-medium">Theme</p>
              <p className="text-sm text-slate-400">Wechsle zwischen Hell und Dunkel</p>
            </div>
            <button
              onClick={toggleTheme}
              className="flex items-center gap-2 px-4 py-2 bg-dark-border rounded-lg"
            >
              {isDark ? <Moon className="w-4 h-4 text-blue-400" /> : <Sun className="w-4 h-4 text-yellow-400" />}
              <span className="text-white">{isDark ? 'Dunkel' : 'Hell'}</span>
            </button>
          </div>
          
          <Select
            label="Akzentfarbe"
            value={settings.accentColor}
            options={[
              { value: 'blue', label: 'Blau' },
              { value: 'purple', label: 'Lila' },
              { value: 'green', label: 'Grün' },
              { value: 'orange', label: 'Orange' },
              { value: 'pink', label: 'Pink' },
            ]}
            onChange={(v) => settings.setSettings({ accentColor: v })}
          />
          
          <Toggle
            label="Kompakter Modus"
            description="Reduziert Abstände für mehr Inhalt"
            checked={settings.compactMode}
            onChange={(v) => settings.setSettings({ compactMode: v })}
          />
          
          <Toggle
            label="Animationen"
            description="Aktiviere UI-Animationen"
            checked={settings.animations}
            onChange={(v) => settings.setSettings({ animations: v })}
          />
        </div>
      </SettingsSection>

      {/* Generation Defaults */}
      <SettingsSection title="Generierungs-Standards" icon={Sliders}>
        <div className="space-y-1 divide-y divide-dark-border">
          <SliderSetting
            label="Standard Slides"
            value={settings.defaultSlides}
            min={3}
            max={30}
            onChange={(v) => settings.setSettings({ defaultSlides: v })}
          />
          
          <SliderSetting
            label="Temperatur"
            value={settings.defaultTemperature}
            min={0}
            max={1}
            step={0.1}
            onChange={(v) => settings.setSettings({ defaultTemperature: v })}
          />
          
          <Select
            label="Standard-Stil"
            value={settings.defaultStyle}
            options={[
              { value: 'corporate', label: 'Corporate' },
              { value: 'modern', label: 'Modern' },
              { value: 'minimal', label: 'Minimal' },
              { value: 'vibrant', label: 'Vibrant' },
            ]}
            onChange={(v) => settings.setSettings({ defaultStyle: v })}
          />
          
          <Toggle
            label="Auto-Save"
            description="Speichere Änderungen automatisch"
            checked={settings.autoSave}
            onChange={(v) => settings.setSettings({ autoSave: v })}
          />
        </div>
      </SettingsSection>

      {/* LLM Configuration */}
      <SettingsSection title="LLM Konfiguration" icon={Cpu}>
        <div className="space-y-1 divide-y divide-dark-border">
          <Select
            label="Model"
            value={settings.llmModel}
            options={availableModels.map(m => ({ value: m, label: m }))}
            onChange={(v) => settings.setSettings({ llmModel: v })}
          />
          
          <SliderSetting
            label="Max Tokens"
            value={settings.maxTokens}
            min={1024}
            max={8192}
            step={256}
            onChange={(v) => settings.setSettings({ maxTokens: v })}
          />
          
          <SliderSetting
            label="Timeout"
            value={settings.timeout}
            min={30}
            max={300}
            unit="s"
            onChange={(v) => settings.setSettings({ timeout: v })}
          />
        </div>
      </SettingsSection>

      {/* Notifications */}
      <SettingsSection title="Benachrichtigungen" icon={Bell}>
        <div className="space-y-1 divide-y divide-dark-border">
          <Toggle
            label="Bei Fertigstellung"
            description="Benachrichtigung wenn Generierung abgeschlossen"
            checked={notifSettings.notifyOnComplete}
            onChange={(v) => {
              notifSettings.setSettings({ notifyOnComplete: v })
              settings.setSettings({ notifyOnComplete: v })
            }}
          />
          
          <Toggle
            label="Bei Fehler"
            description="Benachrichtigung bei Fehlern"
            checked={notifSettings.notifyOnError}
            onChange={(v) => {
              notifSettings.setSettings({ notifyOnError: v })
              settings.setSettings({ notifyOnError: v })
            }}
          />
          
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-white font-medium">Sound-Effekte</p>
              <p className="text-sm text-slate-400">Akustische Benachrichtigungen</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  notifSettings.setSettings({ soundEnabled: !notifSettings.soundEnabled })
                  settings.setSettings({ soundEnabled: !notifSettings.soundEnabled })
                }}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifSettings.soundEnabled ? 'bg-blue-500' : 'bg-dark-border'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    notifSettings.soundEnabled ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
              {notifSettings.soundEnabled ? (
                <Volume2 className="w-5 h-5 text-blue-400" />
              ) : (
                <VolumeX className="w-5 h-5 text-gray-500" />
              )}
            </div>
          </div>
          
          <div className="pt-4">
            <button
              onClick={testNotification}
              className="px-4 py-2 bg-dark-border hover:bg-dark-bg rounded-lg text-white text-sm transition-colors"
            >
              Test-Benachrichtigung senden
            </button>
          </div>
        </div>
      </SettingsSection>

      {/* System */}
      <SettingsSection title="System" icon={Server}>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-dark-bg rounded-xl">
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-purple-400" />
              <div>
                <p className="text-white font-medium">Knowledge Base</p>
                <p className="text-sm text-slate-400">Cache und Index leeren</p>
              </div>
            </div>
            <button 
              onClick={() => {
                fetch('/api/knowledge/cache/clear', { method: 'POST' })
                  .then(() => notify.success('Cache geleert', 'Knowledge Cache wurde erfolgreich geleert.'))
                  .catch(() => notify.error('Fehler', 'Cache konnte nicht geleert werden.'))
              }}
              className="px-4 py-2 bg-dark-border hover:bg-red-500/20 rounded-lg text-slate-400 hover:text-red-400 transition-colors"
            >
              Cache leeren
            </button>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-dark-bg rounded-xl">
            <div className="flex items-center gap-3">
              <HardDrive className="w-5 h-5 text-blue-400" />
              <div>
                <p className="text-white font-medium">Temporäre Dateien</p>
                <p className="text-sm text-slate-400">Vorschau und Temp-Exports löschen</p>
              </div>
            </div>
            <button 
              onClick={() => {
                fetch('/api/system/cleanup', { method: 'POST' })
                  .then(() => notify.success('Bereinigt', 'Temporäre Dateien wurden gelöscht.'))
                  .catch(() => notify.error('Fehler', 'Bereinigung fehlgeschlagen.'))
              }}
              className="px-4 py-2 bg-dark-border hover:bg-red-500/20 rounded-lg text-slate-400 hover:text-red-400 transition-colors"
            >
              Bereinigen
            </button>
          </div>
        </div>
      </SettingsSection>
    </div>
  )
}
