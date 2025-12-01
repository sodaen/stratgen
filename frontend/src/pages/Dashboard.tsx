import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Presentation, 
  Server, 
  Zap, 
  FolderOpen,
  TrendingUp,
  Clock,
  ArrowRight,
  Sparkles
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { api } from '../services/api'
import { cn } from '../utils/helpers'

interface StatCardProps {
  icon: React.ElementType
  label: string
  value: string | number
  trend?: string
  color: string
}

function StatCard({ icon: Icon, label, value, trend, color }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-dark-card rounded-2xl p-6 border border-dark-border card-hover"
    >
      <div className="flex items-start justify-between">
        <div className={cn("p-3 rounded-xl", color)}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <span className="text-xs text-green-400 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            {trend}
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-bold text-white">{value}</p>
        <p className="text-sm text-slate-500 mt-1">{label}</p>
      </div>
    </motion.div>
  )
}

interface QuickActionProps {
  icon: React.ElementType
  label: string
  description: string
  onClick: () => void
  gradient: string
}

function QuickAction({ icon: Icon, label, description, onClick, gradient }: QuickActionProps) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "w-full p-4 rounded-xl text-left transition-all",
        "bg-gradient-to-r", gradient,
        "hover:shadow-lg hover:shadow-blue-500/20"
      )}
    >
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5 text-white" />
        <div>
          <p className="font-medium text-white">{label}</p>
          <p className="text-xs text-white/70">{description}</p>
        </div>
        <ArrowRight className="w-4 h-4 text-white/50 ml-auto" />
      </div>
    </motion.button>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { systemStatus } = useAppStore()
  const [recentProjects, setRecentProjects] = useState<any[]>([])
  const [stats, setStats] = useState({
    projects: 0,
    templates: 32,
    slides: 2436,
    avgTime: '7.3s'
  })

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Presentation}
          label="Projects"
          value={stats.projects}
          trend="+12 today"
          color="bg-gradient-to-br from-blue-500 to-blue-600"
        />
        <StatCard
          icon={Server}
          label="Services Active"
          value={`${systemStatus.servicesActive}/${systemStatus.servicesTotal}`}
          color="bg-gradient-to-br from-green-500 to-green-600"
        />
        <StatCard
          icon={Zap}
          label="Avg. Generation"
          value={stats.avgTime}
          trend="-2.1s"
          color="bg-gradient-to-br from-orange-500 to-orange-600"
        />
        <StatCard
          icon={FolderOpen}
          label="Templates"
          value={stats.templates}
          color="bg-gradient-to-br from-purple-500 to-purple-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-lg font-semibold text-white">Quick Actions</h2>
          <div className="space-y-3">
            <QuickAction
              icon={Sparkles}
              label="New Presentation"
              description="Start from scratch"
              onClick={() => navigate('/generator')}
              gradient="from-blue-500 to-cyan-500"
            />
            <QuickAction
              icon={FolderOpen}
              label="From Template"
              description="Use existing template"
              onClick={() => navigate('/wizard')}
              gradient="from-purple-500 to-pink-500"
            />
            <QuickAction
              icon={Zap}
              label="Quick Generate"
              description="AI-powered fast mode"
              onClick={() => navigate('/generator')}
              gradient="from-orange-500 to-red-500"
            />
          </div>
        </div>

        {/* System Status */}
        <div className="lg:col-span-1">
          <h2 className="text-lg font-semibold text-white mb-4">System Status</h2>
          <div className="bg-dark-card rounded-2xl border border-dark-border p-4 space-y-3">
            <ServiceStatus name="API" status={systemStatus.api} />
            <ServiceStatus name="Ollama LLM" status={systemStatus.ollama} />
            <ServiceStatus name="Redis" status={systemStatus.redis} />
            <ServiceStatus name="Celery Workers" status={systemStatus.celery} />
            <div className="pt-3 border-t border-dark-border">
              <button 
                onClick={() => navigate('/health')}
                className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                View Details <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        {/* Recent Projects */}
        <div className="lg:col-span-1">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Projects</h2>
          <div className="bg-dark-card rounded-2xl border border-dark-border p-4 space-y-3">
            {recentProjects.length === 0 ? (
              <div className="text-center py-8">
                <Presentation className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">No projects yet</p>
                <button 
                  onClick={() => navigate('/generator')}
                  className="mt-3 text-sm text-blue-400 hover:text-blue-300"
                >
                  Create your first presentation
                </button>
              </div>
            ) : (
              recentProjects.map((project, index) => (
                <ProjectItem key={index} project={project} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ServiceStatus({ name, status }: { name: string; status: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-400">{name}</span>
      <div className="flex items-center gap-2">
        <div className={cn(
          "w-2 h-2 rounded-full",
          status ? "bg-green-500" : "bg-red-500"
        )} />
        <span className={cn(
          "text-xs",
          status ? "text-green-400" : "text-red-400"
        )}>
          {status ? "Online" : "Offline"}
        </span>
      </div>
    </div>
  )
}

function ProjectItem({ project }: { project: any }) {
  return (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-dark-border transition-colors cursor-pointer">
      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center">
        <Presentation className="w-5 h-5 text-blue-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{project.name}</p>
        <p className="text-xs text-slate-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {project.time} • {project.slides} slides
        </p>
      </div>
    </div>
  )
}
