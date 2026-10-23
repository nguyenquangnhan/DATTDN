
'use client'

import { useState, useCallback } from 'react'
import { Upload, Link2, FileText, Image, AlertCircle, CheckCircle } from 'lucide-react'
import { uploadDocument, addUrl } from '../lib/api'
import { ACCEPTED_FILE_EXTENSIONS } from '../lib/constants'

export default function DocumentUpload({ notebookId }) {
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [url, setUrl] = useState('')
  const [uploadResults, setUploadResults] = useState([])

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files))
    }
  }, [notebookId])

  const handleFiles = async (files) => {
    if (files.length === 0 || !notebookId) return

    setIsUploading(true)
    setUploadResults([])

    const results = []

    // Upload files one by one (backend expects single file)
    for (const file of files) {
      try {
        const data = await uploadDocument(notebookId, file)
        results.push({
          filename: data.original_name || file.name,
          success: data.status === 'ready',
          status: data.status,
          message: data.message,
        })
      } catch (error) {
        results.push({
          filename: file.name,
          error: error.message || 'Failed to upload file',
        })
      }
    }

    setUploadResults(results)

    // Trigger document list refresh
    window.dispatchEvent(new CustomEvent('documentsUpdated'))

    setIsUploading(false)
  }

  const handleFileInput = (e) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files))
    }
  }

  const handleUrlSubmit = async (e) => {
    e.preventDefault()
    if (!url.trim() || !notebookId) return

    setIsUploading(true)
    setUploadResults([])

    try {
      const data = await addUrl(notebookId, url.trim())

      setUploadResults([{
        filename: data.original_name || url,
        success: data.status === 'ready',
        status: data.status,
        message: data.message,
      }])
      setUrl('')

      // Trigger document list refresh
      window.dispatchEvent(new CustomEvent('documentsUpdated'))

    } catch (error) {
      console.error('URL processing error:', error)
      setUploadResults([{
        filename: url,
        error: error.message || 'Failed to process URL. Please try again.'
      }])
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="surface-card rounded-xl p-6">
      <h2 className="text-base font-semibold text-slate-800 mb-4">Upload Documents</h2>

      {!notebookId && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700">
          Please select or create a notebook first.
        </div>
      )}

      {/* File Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
          dragActive 
            ? 'border-blue-500/50 bg-blue-50/50' 
            : 'border-slate-200 hover:border-slate-300'
        } ${isUploading || !notebookId ? 'opacity-40 pointer-events-none' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept={ACCEPTED_FILE_EXTENSIONS}
          multiple
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isUploading || !notebookId}
        />

        <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-slate-100 flex items-center justify-center">
          <Upload className="h-6 w-6 text-slate-400" />
        </div>
        <p className="text-sm text-slate-600 mb-1">
          {dragActive ? 'Drop files here' : 'Click to upload or drag and drop'}
        </p>
        <p className="text-xs text-slate-400">
          PDF and Image files (PNG, JPG, WebP) — max 10MB each
        </p>

        {isUploading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 rounded-xl">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500/20 border-t-blue-500"></div>
              <span className="text-sm text-slate-600">Processing...</span>
            </div>
          </div>
        )}
      </div>

      {/* URL Input */}
      <div className="mt-5">
        <form onSubmit={handleUrlSubmit} className="space-y-3">
          <div className="flex space-x-2">
            <div className="flex-1">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter website URL to process..."
                className="w-full px-4 py-2.5 input-dark rounded-xl text-sm"
                disabled={isUploading || !notebookId}
              />
            </div>
            <button
              type="submit"
              disabled={isUploading || !url.trim() || !notebookId}
              className="btn-primary px-4 py-2.5 rounded-xl flex items-center space-x-2 text-sm"
            >
              <Link2 className="h-4 w-4" />
              <span>Add URL</span>
            </button>
          </div>
        </form>
      </div>

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <div className="mt-5 space-y-2">
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide">Upload Results</h3>
          {uploadResults.map((result, index) => (
            <div
              key={index}
              className={`flex items-start space-x-2 p-3 rounded-xl text-sm border ${
                result.success
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : result.error
                  ? 'bg-red-50 text-red-700 border-red-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}
            >
              {result.success ? (
                <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              ) : (
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{result.filename}</div>
                {result.message && (
                  <div className="text-xs mt-1 opacity-80">{result.message}</div>
                )}
                {result.error && (
                  <div className="mt-1">{result.error}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
