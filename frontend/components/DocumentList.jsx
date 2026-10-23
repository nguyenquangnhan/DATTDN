
'use client'

import { useState, useEffect } from 'react'
import { FileText, Globe, Image, Trash2, Eye, Calendar, Loader, CheckCircle, XCircle } from 'lucide-react'
import { getDocuments, deleteDocument, deleteAllDocuments, getSourceFileUrl } from '../lib/api'
import SourceViewer from './SourceViewer'

export default function DocumentList({ notebookId }) {
  const [documents, setDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedSource, setSelectedSource] = useState(null)

  const loadDocuments = async () => {
    if (!notebookId) {
      setDocuments([])
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const data = await getDocuments(notebookId)
      setDocuments(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error loading documents:', error)
      setError(error.message || 'Failed to load documents')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()

    // Listen for document updates
    const handleDocumentsUpdated = () => {
      loadDocuments()
    }

    window.addEventListener('documentsUpdated', handleDocumentsUpdated)
    return () => {
      window.removeEventListener('documentsUpdated', handleDocumentsUpdated)
    }
  }, [notebookId])

  // Polling mechanism when there are files in 'processing' status
  useEffect(() => {
    if (!notebookId) return

    const hasProcessing = documents.some(doc => doc.status === 'processing')
    if (!hasProcessing) return

    const interval = setInterval(async () => {
      try {
        const data = await getDocuments(notebookId)
        const docs = Array.isArray(data) ? data : []
        setDocuments(docs)
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 3000) // Poll every 3 seconds

    return () => clearInterval(interval)
  }, [documents, notebookId])

  const handleDelete = async (sourceId) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return
    }

    try {
      await deleteDocument(notebookId, sourceId)
      setDocuments(documents.filter(doc => doc.id !== sourceId))
    } catch (error) {
      console.error('Error deleting document:', error)
      setError(error.message || 'Failed to delete document')
    }
  }

  const clearAllDocs = async () => {
    if (!confirm('Are you sure you want to delete all documents? This cannot be undone.')) {
      return
    }

    try {
      await deleteAllDocuments(notebookId)
      setDocuments([])
    } catch (error) {
      console.error('Error clearing documents:', error)
      setError(error.message || 'Failed to clear documents')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'url': return Globe
      case 'image': return Image
      case 'pdf': return FileText
      default: return FileText
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ready': return <CheckCircle className="h-3 w-3 text-emerald-400" />
      case 'processing': return <Loader className="h-3 w-3 text-amber-400 animate-spin" />
      case 'error': return <XCircle className="h-3 w-3 text-red-400" />
      default: return null
    }
  }

  if (!notebookId) {
    return null
  }

  if (isLoading) {
    return (
      <div className="surface-card rounded-xl p-6">
        <h2 className="text-base font-semibold text-slate-800 mb-4">Sources</h2>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500/20 border-t-blue-500"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="surface-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-800">
          Sources ({documents.length})
        </h2>
        {documents.length > 0 && (
          <button
            onClick={clearAllDocs}
            className="text-xs text-red-500/80 hover:text-red-600 flex items-center space-x-1 transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Clear All</span>
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          {error}
        </div>
      )}

      {documents.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-14 h-14 mx-auto mb-3 rounded-xl bg-slate-100 flex items-center justify-center">
            <FileText className="h-7 w-7 text-slate-400" />
          </div>
          <p className="text-sm text-slate-500">No documents uploaded yet</p>
          <p className="text-xs text-slate-400 mt-1">Upload PDF files, images, or add website URLs to get started.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc, idx) => {
            const FileIcon = getFileIcon(doc.file_type)

            return (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/60 hover:border-blue-500/30 hover:bg-slate-100/50 transition-all duration-200 cursor-pointer group animate-fade-in"
                style={{ animationDelay: `${idx * 40}ms` }}
                onClick={() => setSelectedSource(doc)}
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                    <FileIcon className="h-4 w-4 text-slate-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium text-slate-800 truncate group-hover:text-blue-600 transition-colors">
                        {doc.original_name}
                      </p>
                      {getStatusIcon(doc.status)}
                    </div>
                    <div className="flex items-center space-x-3 mt-0.5">
                      <div className="flex items-center space-x-1 text-xs text-slate-500">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(doc.created_at)}</span>
                      </div>
                      <span className="text-xs text-slate-400 capitalize">{doc.file_type}</span>
                      {doc.status === 'error' && doc.error_message && (
                        <span className="text-xs text-red-500 truncate max-w-32" title={doc.error_message}>
                          ⚠ {doc.error_message}
                        </span>
                      )}
                    </div>
                    {doc.content_preview && (
                      <p className="text-xs text-slate-400 mt-1 truncate">
                        {doc.content_preview}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-all">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedSource(doc)
                    }}
                    className="text-slate-400 hover:text-blue-500 p-1 transition-colors"
                    title="Xem chi tiết nội dung trích xuất"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(doc.id)
                    }}
                    className="text-slate-400 hover:text-red-500 p-1 transition-colors"
                    title="Xóa tài liệu"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Source Viewer Modal */}
      {selectedSource && (
        <SourceViewer
          source={selectedSource}
          onClose={() => setSelectedSource(null)}
        />
      )}
    </div>
  )
}
