import React from 'react'
import { BookOpen, Database, MessageSquare, Brain } from 'lucide-react'
import RAGStatus from '../components/RAGStatus'
import KnowledgeChat from '../components/KnowledgeChat'
import AdminDashboard from '../components/AdminDashboard'

export default function Knowledge() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <BookOpen className="w-7 h-7 text-purple-400" />
            Knowledge Center
          </h1>
          <p className="text-gray-400 mt-1">
            RAG-System, Knowledge Base und AI-Assistent
          </p>
        </div>
      </div>

      {/* Admin Dashboard */}
      <div className="mb-6">
        <AdminDashboard />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chat */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-400" />
            Knowledge Chat
          </h2>
          <KnowledgeChat />
        </div>

        {/* Status */}
        <div>
          <RAGStatus />
        </div>
      </div>
    </div>
  )
}
