'use client'

import { useState } from 'react'
import {
  X,
  FileText,
  Globe,
  Image,
  Calendar,
  AlertCircle,
  CheckCircle,
  Loader,
  Type,
  Info,
  ExternalLink,
  Copy,
  Check,
} from 'lucide-react'
import { getSourceFileUrl } from '../lib/api'

export default function SourceViewer({ source, onClose }) {
  const [activeTab, setActiveTab] = useState('text')
  const [copied, setCopied] = useState(false)

  if (!source) return null

  const fileUrl = getSourceFileUrl(source.notebook_id, source.id)

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'url': return Globe
      case 'image': return Image
      case 'pdf': return FileText
      default: return FileText
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ready':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="h-3 w-3" />
            <span>Sẵn sàng</span>
          </span>
        )
      case 'processing':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs bg-amber-50 text-amber-700 border border-amber-200">
            <Loader className="h-3 w-3 animate-spin" />
            <span>Đang xử lý</span>
          </span>
        )
      case 'error':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs bg-red-50 text-red-700 border border-red-200">
            <AlertCircle className="h-3 w-3" />
            <span>Lỗi</span>
          </span>
        )
      default:
        return null
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const handleCopyText = async () => {
    if (source.content_preview) {
      try {
        await navigator.clipboard.writeText(source.content_preview)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } catch {
        const textarea = document.createElement('textarea')
        textarea.value = source.content_preview
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    }
  }

  const handleOpenInNewTab = () => {
    if (source.file_type === 'url' && source.url) {
      window.open(source.url, '_blank', 'noopener,noreferrer')
    } else {
      window.open(fileUrl, '_blank', 'noopener,noreferrer')
    }
  }

  const FileIcon = getFileIcon(source.file_type)

  const tabs = [
    { id: 'text', label: 'Văn bản trích xuất (AI Data)', icon: Type },
    { id: 'info', label: 'Thông tin chi tiết', icon: Info },
  ]

  const renderTextTab = () => {
    if (source.status === 'processing') {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center mb-3">
            <Loader className="h-6 w-6 text-amber-500 animate-spin" />
          </div>
          <p className="text-sm font-medium text-slate-700">Hệ thống đang xử lý tài liệu...</p>
          <p className="text-xs text-slate-400 mt-1">Đang bóc tách dữ liệu để sẵn sàng trả lời câu hỏi.</p>
        </div>
      )
    }

    if (source.status === 'error') {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center mb-3">
            <AlertCircle className="h-6 w-6 text-red-500" />
          </div>
          <p className="text-sm font-medium text-slate-700">Không thể trích xuất văn bản</p>
          {source.error_message && (
            <p className="text-xs text-red-500 mt-1 max-w-sm">{source.error_message}</p>
          )}
        </div>
      )
    }

    if (!source.content_preview) {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
            <Type className="h-6 w-6 text-slate-400" />
          </div>
          <p className="text-sm text-slate-500">Chưa có nội dung văn bản trích xuất.</p>
        </div>
      )
    }

    return (
      <div>
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs text-slate-500 font-medium">
            Nội dung chữ đã được bóc tách để AI sử dụng tìm kiếm & trả lời:
          </p>
          <button
            onClick={handleCopyText}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200/60"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-emerald-600 font-semibold">Đã sao chép!</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Sao chép văn bản</span>
              </>
            )}
          </button>
        </div>

        <div className="bg-slate-50 rounded-xl p-5 border border-slate-200/60 max-h-[380px] overflow-y-auto">
          <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed selection:bg-blue-100 font-sans">
            {source.content_preview}
          </p>
        </div>
      </div>
    )
  }

  const renderInfoTab = () => {
    const infoItems = [
      { label: 'Tên file gốc', value: source.original_name },
      { label: 'Định dạng', value: source.file_type?.toUpperCase() },
      { label: 'Trạng thái RAG', value: null, badge: getStatusBadge(source.status) },
      ...(source.page_count ? [{ label: 'Số trang', value: `${source.page_count} trang` }] : []),
      { label: 'Ngày tạo', value: formatDate(source.created_at) },
      { label: 'ID Hệ thống', value: source.id },
    ]

    return (
      <div className="space-y-0 divide-y divide-slate-100">
        {infoItems.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between py-3.5">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">{item.label}</span>
            {item.badge ? (
              item.badge
            ) : (
              <span className="text-sm text-slate-700 font-medium text-right max-w-[60%] truncate" title={String(item.value)}>
                {item.value}
              </span>
            )}
          </div>
        ))}

        {source.url && (
          <div className="py-3.5">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-medium block mb-1.5">Địa chỉ Web (URL)</span>
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-500 hover:text-blue-600 break-all transition-colors"
            >
              {source.url}
            </a>
          </div>
        )}

        {source.error_message && (
          <div className="py-3.5">
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
              <p className="text-xs text-red-500 uppercase tracking-wider font-medium mb-1">Thông tin lỗi</p>
              <p className="text-sm text-red-700">{source.error_message}</p>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-sm" onClick={onClose}>
      <div
        className="glass-card rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200/60 px-6 py-4">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
              <FileIcon className="h-4.5 w-4.5 text-blue-600" />
            </div>
            <div className="min-w-0">
              <h2 className="text-base font-semibold text-slate-800 truncate">
                {source.original_name}
              </h2>
              <p className="text-xs text-slate-400 capitalize">{source.file_type}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 flex-shrink-0 transition-all"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Bar */}
        <div className="flex border-b border-slate-200/60 px-6 bg-slate-50/50">
          {tabs.map((tab) => {
            const TabIcon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                  isActive
                    ? 'border-blue-500 text-blue-600 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-600 hover:border-slate-300'
                }`}
              >
                <TabIcon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Tab Content */}
        <div className="overflow-y-auto px-6 py-5 flex-1">
          {activeTab === 'text' && renderTextTab()}
          {activeTab === 'info' && renderInfoTab()}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200/60 px-6 py-3 flex items-center justify-between bg-slate-50/30">
          <div>
            {source.status === 'ready' && (
              <button
                onClick={handleOpenInNewTab}
                className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-500 hover:text-blue-600 transition-colors"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                <span>Tải/Mở file gốc</span>
              </button>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200/70 rounded-xl transition-colors border border-slate-200/60"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  )
}
