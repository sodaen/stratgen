import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { useThemeStore } from './stores/themeStore'
import { useSessionStore } from './stores/sessionStore'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Generator from './pages/Generator'
import Wizard from './pages/Wizard'
import Editor from './pages/Editor'
import Pipeline from './pages/Pipeline'
import Health from './pages/Health'
import Files from './pages/Files'
import Settings from './pages/Settings'
import AdminDashboard from './pages/AdminDashboard'
import Knowledge from './pages/Knowledge'
import KnowledgeDashboard from './components/KnowledgeDashboard'
import DataImport from './pages/DataImport'
import Research from './pages/Research'
import PorterAnalysis from './pages/PorterAnalysis'

function App() {
  const { loadSessionsFromBackend } = useSessionStore()

  React.useEffect(() => {
    loadSessionsFromBackend()
  }, [])

  const { isDark } = useThemeStore()

  return (
    <div className={isDark ? 'dark' : 'light'}>
      <div className="min-h-screen bg-dark-bg dark:bg-dark-bg light:bg-slate-50">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/generator" element={<Generator />} />
            <Route path="/wizard" element={<Wizard />} />
            <Route path="/editor" element={<Editor />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/health" element={<Health />} />
            <Route path="/files" element={<Files />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/knowledge" element={<Knowledge />} />
            <Route path="/knowledge-analytics" element={<KnowledgeDashboard />} />
            <Route path="/data-import" element={<DataImport />} />
            <Route path="/research" element={<Research />} />
            <Route path="/porter" element={<PorterAnalysis />} />
          </Routes>
        </Layout>
      </div>
    </div>
  )
}

export default App
