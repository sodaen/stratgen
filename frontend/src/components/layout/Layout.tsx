import { ReactNode, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import Sidebar from './Sidebar'
import Header from './Header'
import { useAppStore } from '../../stores/appStore'
import { api } from '../../services/api'

interface LayoutProps {
  children: ReactNode
}

const pageTitles: Record<string, { title: string; subtitle?: string }> = {
  '/': { title: 'Dashboard', subtitle: 'Welcome to StratGen' },
  '/generator': { title: 'Generator', subtitle: 'Create presentations' },
  '/wizard': { title: 'Wizard', subtitle: 'Step-by-step guide' },
  '/editor': { title: 'Live Editor', subtitle: 'Edit in real-time' },
  '/pipeline': { title: 'Pipeline', subtitle: 'Monitor progress' },
  '/health': { title: 'System Health', subtitle: 'Service status' },
  '/files': { title: 'File Manager', subtitle: 'Manage your files' },
  '/settings': { title: 'Settings', subtitle: 'Configuration' },
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { sidebarCollapsed, setSystemStatus, setLoading } = useAppStore()
  const pageInfo = pageTitles[location.pathname] || { title: 'StratGen' }

  // Fetch system status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [agentStatus, workersStatus] = await Promise.all([
          api.getAgentStatus().catch(() => null),
          api.getWorkersStatus().catch(() => null),
        ])

        setSystemStatus({
          api: true,
          ollama: agentStatus?.ollama?.ok ?? false,
          redis: workersStatus?.celery_available ?? false,
          celery: (workersStatus?.worker_count ?? 0) > 0,
          servicesActive: Object.values(agentStatus?.services || {}).filter(Boolean).length,
          servicesTotal: 14,
        })
      } catch (error) {
        setSystemStatus({
          api: false,
          ollama: false,
          redis: false,
          celery: false,
          servicesActive: 0,
          servicesTotal: 14,
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [setSystemStatus, setLoading])

  return (
    <div className="min-h-screen bg-dark-bg">
      <Sidebar />
      
      <motion.main
        initial={false}
        animate={{ marginLeft: sidebarCollapsed ? 80 : 260 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="min-h-screen"
      >
        <Header title={pageInfo.title} subtitle={pageInfo.subtitle} />
        
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.2 }}
          className="p-6"
        >
          {children}
        </motion.div>
      </motion.main>
    </div>
  )
}
