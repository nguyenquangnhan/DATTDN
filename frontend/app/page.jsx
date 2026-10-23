'use client'

import { useState, useEffect } from 'react'
import { Plus, BookOpen, Trash2, ArrowLeft, MessageSquare, Share2, Sparkles, LogOut, User } from 'lucide-react'
import DocumentUpload from "../components/DocumentUpload"
import ChatInterface from "../components/ChatInterface"
import DocumentList from "../components/DocumentList"
import KnowledgeGraph from "../components/KnowledgeGraph"
import AuthModal from "../components/AuthModal"
import { getNotebooks, createNotebook, deleteNotebook, getNotebook } from "../lib/api"
import { useAuth } from "../context/AuthContext"

export default function Home() {
  const { user, loading: authLoading, logout } = useAuth()
  const [notebooks, setNotebooks] = useState([])
  const [selectedNotebook, setSelectedNotebook] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('chat')

  const loadNotebooks = async () => {
    setIsLoading(true)
    try {
      const data = await getNotebooks()
      setNotebooks(data || [])
    } catch (error) {
      console.error('Error loading notebooks:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Load notebooks when user is available
  useEffect(() => {
    if (user) loadNotebooks()
  }, [user])

  const handleCreateNotebook = async (e) => {
    e.preventDefault()
    if (!newTitle.trim()) return

    try {
      const notebook = await createNotebook(newTitle.trim())
      setNotebooks([notebook, ...notebooks])
      setSelectedNotebook(notebook)
      setNewTitle('')
      setIsCreating(false)
    } catch (error) {
      console.error('Error creating notebook:', error)
    }
  }

  const handleDeleteNotebook = async (id) => {
    if (!confirm('Delete this notebook and all its data?')) return

    try {
      await deleteNotebook(id)
      setNotebooks(notebooks.filter(n => n.id !== id))
      if (selectedNotebook?.id === id) {
        setSelectedNotebook(null)
      }
    } catch (error) {
      console.error('Error deleting notebook:', error)
    }
  }

  const handleSelectNotebook = async (notebook) => {
    try {
      const fullNotebook = await getNotebook(notebook.id)
      setSelectedNotebook(fullNotebook)
    } catch (error) {
      console.error('Error loading notebook:', error)
      setSelectedNotebook(notebook)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // ── Auth guards (after all hooks) ──
  if (authLoading) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center',
        justifyContent: 'center', background: '#f8fafc',
      }}>
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500/20 border-t-blue-500" />
      </div>
    )
  }

  if (!user) return <AuthModal />

  // ── Notebook workspace view ──
  if (selectedNotebook) {
    return (
      <div className="min-h-screen">
        <header className="glass-card border-t-0 border-x-0 px-4 py-4 sticky top-0 z-30">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setSelectedNotebook(null)}
                  className="text-slate-500 hover:text-slate-800 flex items-center space-x-1 transition-colors"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span className="text-sm">Back</span>
                </button>
                <h1 className="text-xl font-bold text-slate-800">
                  {selectedNotebook.title}
                </h1>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-500">{selectedNotebook.source_count || 0} sources</span>
                <UserMenu user={user} logout={logout} />
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Panel - Document Upload & Management */}
            <div className="lg:col-span-1 space-y-6 animate-fade-in">
              <DocumentUpload notebookId={selectedNotebook.id} />
              <DocumentList notebookId={selectedNotebook.id} />
            </div>

            {/* Right Panel - Tabs: Chat / Knowledge Graph */}
            <div className="lg:col-span-2 space-y-4 animate-fade-in" style={{ animationDelay: '100ms' }}>
              {/* Tab Switcher */}
              <div className="flex space-x-1 surface-card rounded-xl p-1">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === 'chat'
                      ? 'bg-blue-50 text-blue-600 shadow-sm border border-blue-100/50'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <MessageSquare className="h-4 w-4" />
                  <span>Chat</span>
                </button>
                <button
                  onClick={() => setActiveTab('graph')}
                  className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === 'graph'
                      ? 'bg-violet-50 text-violet-600 shadow-sm border border-violet-100/50'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Share2 className="h-4 w-4" />
                  <span>Knowledge Graph</span>
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === 'chat' ? (
                <ChatInterface notebookId={selectedNotebook.id} />
              ) : (
                <KnowledgeGraph notebookId={selectedNotebook.id} />
              )}
            </div>
          </div>
        </main>
      </div>
    )
  }

  // ── Dashboard view ──
  return (
    <div className="min-h-screen">
      <header className="glass-card border-t-0 border-x-0 px-4 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">DocuGraph RAG</h1>
              </div>
            </div>
            <UserMenu user={user} logout={logout} />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Create Notebook */}
        <div className="mb-10 animate-fade-in">
          {isCreating ? (
            <form onSubmit={handleCreateNotebook} className="flex items-center space-x-3 max-w-lg">
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Notebook name..."
                className="flex-1 px-4 py-2.5 input-dark rounded-xl text-sm"
                autoFocus
              />
              <button
                type="submit"
                disabled={!newTitle.trim()}
                className="btn-primary px-5 py-2.5 rounded-xl text-sm font-medium"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => { setIsCreating(false); setNewTitle('') }}
                className="px-4 py-2.5 text-slate-500 hover:text-slate-800 text-sm transition-colors"
              >
                Cancel
              </button>
            </form>
          ) : (
            <button
              onClick={() => setIsCreating(true)}
              className="btn-primary flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-medium"
            >
              <Plus className="h-4 w-4" />
              <span>New Notebook</span>
            </button>
          )}
        </div>

        {/* Notebooks Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500/20 border-t-blue-500"></div>
          </div>
        ) : notebooks.length === 0 ? (
          <div className="text-center py-20 animate-fade-in">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-slate-100 flex items-center justify-center">
              <BookOpen className="h-10 w-10 text-slate-400" />
            </div>
            <h2 className="text-xl font-semibold text-slate-800 mb-2">No notebooks yet</h2>
            <p className="text-slate-500">Create your first notebook to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {notebooks.map((notebook, idx) => (
              <div
                key={notebook.id}
                className="surface-card rounded-xl p-5 hover:border-blue-500/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 cursor-pointer group animate-fade-in"
                style={{ animationDelay: `${idx * 60}ms` }}
                onClick={() => handleSelectNotebook(notebook)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-slate-800 truncate group-hover:text-blue-600 transition-colors">
                      {notebook.title}
                    </h3>
                    {notebook.description && (
                      <p className="text-sm text-slate-500 mt-1.5 line-clamp-2">
                        {notebook.description}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteNotebook(notebook.id)
                    }}
                    className="text-slate-400 hover:text-red-500 p-1 opacity-0 group-hover:opacity-100 transition-all"
                    title="Delete notebook"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="flex items-center space-x-4 mt-4 text-xs text-slate-500">
                  <span>{notebook.source_count || 0} sources</span>
                  <span>{formatDate(notebook.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

// ── UserMenu Component ────────────────────────────────────────────────────────

function UserMenu({ user, logout }) {
  const [open, setOpen] = useState(false)
  const initials = (user?.full_name || user?.email || 'U')
    .split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)

  return (
    <div style={{ position: 'relative' }}>
      <button
        id="user-menu-btn"
        onClick={() => setOpen(v => !v)}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          background: 'white', border: '1.5px solid #e2e8f0',
          borderRadius: '12px', padding: '6px 12px 6px 6px',
          cursor: 'pointer', transition: 'all 0.2s ease',
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
        }}
      >
        {user?.avatar_url ? (
          <img src={user.avatar_url} alt="" style={{
            width: '30px', height: '30px', borderRadius: '8px', objectFit: 'cover'
          }} />
        ) : (
          <div style={{
            width: '30px', height: '30px', borderRadius: '8px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontSize: '12px', fontWeight: '700',
          }}>
            {initials}
          </div>
        )}
        <span style={{ fontSize: '13px', fontWeight: '600', color: '#374151', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {user?.full_name || user?.email?.split('@')[0] || 'User'}
        </span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2 4l4 4 4-4" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {open && (
        <>
          <div style={{
            position: 'fixed', inset: 0, zIndex: 40,
          }} onClick={() => setOpen(false)} />
          <div style={{
            position: 'absolute', right: 0, top: 'calc(100% + 8px)',
            background: 'white', border: '1.5px solid #e2e8f0',
            borderRadius: '14px', padding: '8px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
            minWidth: '200px', zIndex: 50,
          }}>
            <div style={{ padding: '8px 10px 12px', borderBottom: '1px solid #f1f5f9', marginBottom: '6px' }}>
              <p style={{ margin: 0, fontSize: '13px', fontWeight: '700', color: '#0f172a' }}>
                {user?.full_name || 'Người dùng'}
              </p>
              <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>{user?.email}</p>
            </div>
            <button
              id="logout-btn"
              onClick={() => { setOpen(false); logout() }}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '8px',
                padding: '9px 10px', border: 'none', background: 'none',
                cursor: 'pointer', borderRadius: '8px', fontSize: '13px',
                color: '#ef4444', fontWeight: '600', transition: 'background 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#fef2f2'}
              onMouseLeave={e => e.currentTarget.style.background = 'none'}
            >
              <LogOut size={14} /> Đăng xuất
            </button>
          </div>
        </>
      )}
    </div>
  )
}
