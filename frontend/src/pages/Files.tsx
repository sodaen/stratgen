import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { 
  Folder,
  FolderOpen,
  File,
  FileText,
  FileSpreadsheet,
  FileImage,
  Presentation,
  Upload,
  Trash2,
  Eye,
  RefreshCw,
  HardDrive,
  Search,
  ChevronRight,
  Download,
  Loader2,
  CheckCircle,
  Database
} from 'lucide-react'
import { api } from '../services/api'
import { cn, formatBytes } from '../utils/helpers'

interface FileInfo {
  name: string
  path: string
  type: string
  size: number
  modified: string
}

interface DirectoryListing {
  path: string
  files: FileInfo[]
  directories: string[]
  total_size: number
}

const folderStructure = [
  { id: 'raw', label: 'Raw Presentations', icon: Presentation, color: 'text-blue-400' },
  { id: 'knowledge', label: 'Knowledge Base', icon: Database, color: 'text-green-400' },
  { id: 'uploads', label: 'Uploads', icon: Upload, color: 'text-orange-400' },
  { id: 'templates', label: 'Templates', icon: FileText, color: 'text-purple-400' },
]

function getFileIcon(type: string) {
  switch (type.toLowerCase()) {
    case '.pptx':
    case '.ppt':
      return Presentation
    case '.xlsx':
    case '.xls':
    case '.csv':
      return FileSpreadsheet
    case '.png':
    case '.jpg':
    case '.jpeg':
    case '.gif':
    case '.webp':
      return FileImage
    case '.docx':
    case '.doc':
    case '.pdf':
    case '.md':
    case '.txt':
      return FileText
    default:
      return File
  }
}

export default function Files() {
  const [currentPath, setCurrentPath] = useState('raw')
  const [listing, setListing] = useState<DirectoryListing | null>(null)
  const [storage, setStorage] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [indexing, setIndexing] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const loadListing = async (path: string) => {
    setLoading(true)
    try {
      const data = await api.listFiles(path)
      setListing(data)
    } catch (error) {
      console.error('Failed to load listing:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStorage = async () => {
    try {
      const response = await fetch('/api/files/storage')
      const data = await response.json()
      setStorage(data)
    } catch (error) {
      console.error('Failed to load storage:', error)
    }
  }

  useEffect(() => {
    loadListing(currentPath)
    loadStorage()
  }, [currentPath])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true)
    try {
      for (const file of acceptedFiles) {
        await api.uploadFile(file, currentPath)
      }
      await loadListing(currentPath)
      await loadStorage()
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }, [currentPath])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  const handleDelete = async (filePath: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return
    
    try {
      await fetch(`/api/files/${encodeURIComponent(filePath)}`, { method: 'DELETE' })
      await loadListing(currentPath)
      await loadStorage()
    } catch (error) {
      console.error('Delete failed:', error)
    }
  }

  const handleIndex = async () => {
    setIndexing(true)
    try {
      await api.indexFiles()
      // Show success notification
    } catch (error) {
      console.error('Indexing failed:', error)
    } finally {
      setIndexing(false)
    }
  }

  const filteredFiles = listing?.files.filter(f => 
    f.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar - Folders */}
      <div className="lg:col-span-1 space-y-4">
        <div className="bg-dark-card rounded-2xl border border-dark-border p-4">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Folders</h3>
          <nav className="space-y-1">
            {folderStructure.map((folder) => {
              const Icon = folder.icon
              const isActive = currentPath === folder.id
              
              return (
                <button
                  key={folder.id}
                  onClick={() => setCurrentPath(folder.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left",
                    isActive 
                      ? "bg-dark-border text-white" 
                      : "text-slate-400 hover:text-white hover:bg-dark-border/50"
                  )}
                >
                  <Icon className={cn("w-5 h-5", isActive ? folder.color : "")} />
                  <span className="text-sm font-medium">{folder.label}</span>
                  {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Storage Info */}
        <div className="bg-dark-card rounded-2xl border border-dark-border p-4">
          <div className="flex items-center gap-2 mb-4">
            <HardDrive className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-400">Storage</h3>
          </div>
          
          {storage && (
            <div className="space-y-3">
              {folderStructure.map((folder) => (
                <div key={folder.id}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-slate-500">{folder.label}</span>
                    <span className="text-slate-400">{formatBytes(storage[folder.id] || 0)}</span>
                  </div>
                  <div className="h-1.5 bg-dark-border rounded-full overflow-hidden">
                    <div 
                      className={cn(
                        "h-full rounded-full transition-all",
                        folder.id === 'raw' ? "bg-blue-500" :
                        folder.id === 'knowledge' ? "bg-green-500" :
                        folder.id === 'uploads' ? "bg-orange-500" :
                        "bg-purple-500"
                      )}
                      style={{ 
                        width: `${Math.min((storage[folder.id] / storage.total) * 100, 100)}%` 
                      }}
                    />
                  </div>
                </div>
              ))}
              
              <div className="pt-3 border-t border-dark-border">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Total</span>
                  <span className="text-sm font-medium text-white">{formatBytes(storage.total)}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Index Button */}
        <button
          onClick={handleIndex}
          disabled={indexing}
          className={cn(
            "w-full py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-all",
            indexing
              ? "bg-dark-border text-slate-500 cursor-not-allowed"
              : "bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:shadow-lg hover:shadow-green-500/25"
          )}
        >
          {indexing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Indexing...
            </>
          ) : (
            <>
              <Database className="w-4 h-4" />
              Index & Learn
            </>
          )}
        </button>
      </div>

      {/* Main Content */}
      <div className="lg:col-span-3 space-y-4">
        {/* Search & Actions */}
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search files..."
              className="w-full pl-10 pr-4 py-2.5 bg-dark-card border border-dark-border rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <button
            onClick={() => loadListing(currentPath)}
            className="p-2.5 bg-dark-card border border-dark-border rounded-xl text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
          </button>
        </div>

        {/* Upload Zone */}
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all",
            isDragActive 
              ? "border-blue-500 bg-blue-500/10" 
              : "border-dark-border hover:border-slate-600 bg-dark-card"
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center">
            {uploading ? (
              <>
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-3" />
                <p className="text-slate-400">Uploading...</p>
              </>
            ) : isDragActive ? (
              <>
                <Upload className="w-10 h-10 text-blue-500 mb-3" />
                <p className="text-blue-400 font-medium">Drop files here</p>
              </>
            ) : (
              <>
                <Upload className="w-10 h-10 text-slate-500 mb-3" />
                <p className="text-slate-400">Drop files here or click to upload</p>
                <p className="text-xs text-slate-600 mt-1">Supports: PPTX, DOCX, PDF, Images, Excel</p>
              </>
            )}
          </div>
        </div>

        {/* File List */}
        <div className="bg-dark-card rounded-2xl border border-dark-border overflow-hidden">
          <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
            <span className="text-sm text-slate-400">
              {filteredFiles.length} files • {formatBytes(listing?.total_size || 0)}
            </span>
          </div>
          
          <div className="divide-y divide-dark-border">
            <AnimatePresence>
              {loading ? (
                <div className="p-8 text-center">
                  <Loader2 className="w-8 h-8 text-slate-500 animate-spin mx-auto" />
                </div>
              ) : filteredFiles.length === 0 ? (
                <div className="p-8 text-center">
                  <Folder className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-500">No files in this folder</p>
                </div>
              ) : (
                filteredFiles.map((file) => {
                  const Icon = getFileIcon(file.type)
                  
                  return (
                    <motion.div
                      key={file.path}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="flex items-center gap-4 px-4 py-3 hover:bg-dark-border/50 transition-colors"
                    >
                      <div className="p-2 rounded-lg bg-dark-border">
                        <Icon className="w-5 h-5 text-slate-400" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{file.name}</p>
                        <p className="text-xs text-slate-500">
                          {formatBytes(file.size)} • {new Date(file.modified).toLocaleDateString('de-DE')}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <button className="p-2 rounded-lg hover:bg-dark-border text-slate-400 hover:text-white transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDelete(file.path)}
                          className="p-2 rounded-lg hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  )
                })
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
