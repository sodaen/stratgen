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
import Knowledge from './pages/Knowledge'

function App() {
  const { loadSessionsFromBackend } = useSessionStore()
  
  // Load sessions on app start
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
            <Route path="/knowledge" element={<Knowledge />} />
          </Routes>
        </Layout>
      </div>
    </div>
  )
}

export default App
