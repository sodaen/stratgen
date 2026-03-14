import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, BarChart2, PieChart, TrendingUp, FileSpreadsheet,
  CheckCircle, AlertCircle, Loader2, Download, Plus, Eye, X
} from 'lucide-react'
import { cn } from '../utils/helpers'

const API_BASE = '/api'

interface ColumnInfo {
  name: string
  type: 'label' | 'numeric'
  sample: (string | number)[]
}

interface ImportResult {
  id: string
  filename: string
  rows: number
  columns: ColumnInfo[]
}

interface ChartPreview {
  slide: {
    type: string
    title: string
    chart_type: string
    chart_path: string
    bullets: string[]
  }
  chart_image_url?: string
}

const CHART_TYPES = [
  { value: 'bar', label: 'Balken', icon: BarChart2 },
  { value: 'line', label: 'Linie', icon: TrendingUp },
  { value: 'pie', label: 'Kreis', icon: PieChart },
]

export default function DataImport() {
  const [isDragging, setIsDragging] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [selectedLabel, setSelectedLabel] = useState<string>('')
  const [selectedValues, setSelectedValues] = useState<string[]>([])
  const [chartType, setChartType] = useState<'bar' | 'line' | 'pie'>('bar')
  const [chartTitle, setChartTitle] = useState('')
  const [generating, setGenerating] = useState(false)
  const [preview, setPreview] = useState<ChartPreview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [added, setAdded] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const labelColumns = importResult?.columns.filter(c => c.type === 'label') ?? []
  const numericColumns = importResult?.columns.filter(c => c.type === 'numeric') ?? []

  async function handleFile(file: File) {
    if (!file.name.match(/\.(csv|xlsx|xls)$/i)) {
      setError('Nur CSV und Excel-Dateien (.csv, .xlsx, .xls) werden unterstützt.')
      return
    }

    setImporting(true)
    setError(null)
    setImportResult(null)
    setPreview(null)
    setAdded(false)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const r = await fetch(`${API_BASE}/data-import/upload`, {
        method: 'POST',
        body: formData,
      })
      const d = await r.json()
      if (!d.ok) throw new Error(d.error || 'Upload fehlgeschlagen')

      setImportResult(d)
      setChartTitle(file.name.replace(/\.[^.]+$/, ''))

      // Label-Spalte vorauswählen
      const firstLabel = d.columns.find((c: ColumnInfo) => c.type === 'label')
      if (firstLabel) setSelectedLabel(firstLabel.name)

      // Erste numerische Spalte vorauswählen
      const firstNum = d.columns.find((c: ColumnInfo) => c.type === 'numeric')
      if (firstNum) setSelectedValues([firstNum.name])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setImporting(false)
    }
  }

  async function generateChart() {
    if (!importResult || !selectedLabel || selectedValues.length === 0) return

    setGenerating(true)
    setError(null)
    setPreview(null)

    try {
      const r = await fetch(`${API_BASE}/data-import/chart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          import_id: importResult.id,
          chart_type: chartType,
          label_column: selectedLabel,
          value_columns: selectedValues,
          title: chartTitle || 'Datenvisualisierung',
        }),
      })
      const d = await r.json()
      if (!d.ok) throw new Error(d.error || 'Chart-Generierung fehlgeschlagen')

      setPreview({
        slide: d.slide,
        chart_image_url: d.chart_image
          ? `${API_BASE}/data-import/chart-image/${d.chart_image}`
          : undefined,
      })
    } catch (e: any) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  function toggleValueColumn(col: string) {
    setSelectedValues(prev =>
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    )
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [])

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Daten-Import</h1>
        <p className="text-slate-400 mt-1">CSV oder Excel hochladen und als Chart-Slide verwenden</p>
      </div>

      {/* Upload Area */}
      {!importResult && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all',
            isDragging
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-dark-border hover:border-slate-600 bg-dark-card'
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          {importing ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
              <p className="text-slate-400">Datei wird analysiert…</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-2xl bg-dark-border flex items-center justify-center">
                <FileSpreadsheet className="w-8 h-8 text-slate-400" />
              </div>
              <div>
                <p className="text-white font-medium">Datei hier ablegen oder klicken</p>
                <p className="text-slate-500 text-sm mt-1">CSV, XLSX, XLS – max. 10 MB</p>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Import Result + Config */}
      {importResult && (
        <div className="grid grid-cols-5 gap-6">
          {/* Konfiguration */}
          <div className="col-span-2 space-y-4">
            <div className="bg-dark-card border border-dark-border rounded-2xl p-5 space-y-5">
              {/* Datei-Info */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-white font-medium">{importResult.filename}</span>
                </div>
                <button
                  onClick={() => { setImportResult(null); setPreview(null); setError(null) }}
                  className="p-1 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-slate-500">{importResult.rows} Zeilen · {importResult.columns.length} Spalten</p>

              {/* Chart-Titel */}
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Titel</label>
                <input
                  value={chartTitle}
                  onChange={e => setChartTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-dark-border rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  placeholder="Chart-Titel"
                />
              </div>

              {/* Chart-Typ */}
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Diagramm-Typ</label>
                <div className="grid grid-cols-3 gap-2">
                  {CHART_TYPES.map(ct => {
                    const Icon = ct.icon
                    return (
                      <button
                        key={ct.value}
                        onClick={() => setChartType(ct.value as any)}
                        className={cn(
                          'flex flex-col items-center gap-1.5 py-2.5 rounded-lg border text-xs transition-all',
                          chartType === ct.value
                            ? 'border-blue-500 bg-blue-500/15 text-blue-300'
                            : 'border-dark-border text-slate-400 hover:border-slate-600 hover:text-white'
                        )}
                      >
                        <Icon className="w-4 h-4" />
                        {ct.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Label-Spalte */}
              {labelColumns.length > 0 && (
                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Beschriftungen (X-Achse)</label>
                  <select
                    value={selectedLabel}
                    onChange={e => setSelectedLabel(e.target.value)}
                    className="w-full px-3 py-2 bg-dark-border rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  >
                    {labelColumns.map(c => (
                      <option key={c.name} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Wert-Spalten */}
              {numericColumns.length > 0 && (
                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Werte (Y-Achse)</label>
                  <div className="space-y-1">
                    {numericColumns.map(c => (
                      <label key={c.name} className="flex items-center gap-2 cursor-pointer group">
                        <input
                          type="checkbox"
                          checked={selectedValues.includes(c.name)}
                          onChange={() => toggleValueColumn(c.name)}
                          className="rounded border-dark-border"
                        />
                        <span className="text-sm text-slate-400 group-hover:text-white transition-colors">{c.name}</span>
                        <span className="text-xs text-slate-600 ml-auto">{c.sample.slice(0, 2).join(', ')}…</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Generate Button */}
              <button
                onClick={generateChart}
                disabled={generating || !selectedLabel || selectedValues.length === 0}
                className={cn(
                  'w-full py-2.5 rounded-xl font-medium flex items-center justify-center gap-2 transition-all text-sm',
                  generating || !selectedLabel || selectedValues.length === 0
                    ? 'bg-dark-border text-slate-500'
                    : 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25'
                )}
              >
                {generating ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Generiere Chart…</>
                ) : (
                  <><Eye className="w-4 h-4" /> Vorschau generieren</>
                )}
              </button>
            </div>

            {/* Spalten-Vorschau */}
            <div className="bg-dark-card border border-dark-border rounded-2xl p-4">
              <h3 className="text-xs font-medium text-slate-400 mb-3">Erkannte Spalten</h3>
              <div className="space-y-1.5">
                {importResult.columns.map(c => (
                  <div key={c.name} className="flex items-center gap-2">
                    <span className={cn(
                      'px-1.5 py-0.5 rounded text-xs font-mono',
                      c.type === 'label' ? 'bg-purple-500/20 text-purple-300' : 'bg-green-500/20 text-green-300'
                    )}>
                      {c.type === 'label' ? 'text' : 'num'}
                    </span>
                    <span className="text-sm text-slate-300 truncate">{c.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Vorschau */}
          <div className="col-span-3">
            <AnimatePresence mode="wait">
              {!preview && !generating && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="h-full min-h-64 bg-dark-card border border-dark-border rounded-2xl flex items-center justify-center"
                >
                  <div className="text-center">
                    <BarChart2 className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-500 text-sm">Konfiguriere links und klicke auf Vorschau</p>
                  </div>
                </motion.div>
              )}

              {generating && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="h-full min-h-64 bg-dark-card border border-dark-border rounded-2xl flex items-center justify-center"
                >
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-3" />
                    <p className="text-slate-400 text-sm">Chart wird generiert…</p>
                  </div>
                </motion.div>
              )}

              {preview && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-dark-card border border-dark-border rounded-2xl overflow-hidden"
                >
                  {/* Slide Preview */}
                  <div className="aspect-video bg-gradient-to-br from-slate-900 to-slate-800 p-6 flex flex-col">
                    <h2 className="text-white text-lg font-bold mb-4">{preview.slide.title}</h2>
                    {preview.chart_image_url ? (
                      <div className="flex-1 flex items-center justify-center">
                        <img
                          src={preview.chart_image_url}
                          alt="Chart"
                          className="max-h-full max-w-full object-contain rounded"
                        />
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center">
                        <div className="text-center text-slate-500">
                          <BarChart2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p className="text-xs">Chart-Bild wird eingebettet</p>
                        </div>
                      </div>
                    )}
                    {preview.slide.bullets.length > 0 && (
                      <ul className="mt-3 space-y-1">
                        {preview.slide.bullets.slice(0, 3).map((b, i) => (
                          <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                            <span className="text-blue-400 mt-0.5">•</span>
                            {b}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="p-4 border-t border-dark-border flex items-center gap-3">
                    {added ? (
                      <div className="flex items-center gap-2 text-green-400 text-sm">
                        <CheckCircle className="w-4 h-4" />
                        Slide-Daten kopiert! Jetzt im Generator verwenden.
                      </div>
                    ) : (
                      <>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(JSON.stringify(preview.slide, null, 2))
                            setAdded(true)
                          }}
                          className="flex-1 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl text-sm font-medium flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-blue-500/25 transition-all"
                        >
                          <Plus className="w-4 h-4" />
                          Slide-Daten übernehmen
                        </button>
                        {preview.chart_image_url && (
                          <a
                            href={preview.chart_image_url}
                            download="chart.png"
                            className="p-2 bg-dark-border rounded-xl text-slate-400 hover:text-white transition-colors"
                            title="Chart herunterladen"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                        )}
                      </>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  )
}
