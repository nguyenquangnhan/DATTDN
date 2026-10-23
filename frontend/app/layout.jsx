import './globals.css'
import { Inter } from 'next/font/google'
import { AuthProvider } from '../context/AuthContext'

const inter = Inter({
  subsets: ['latin', 'vietnamese'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata = {
  title: 'DocuGraph RAG — Nền Tảng Trích Xuất & Hỏi Đáp Tài Liệu Thông Minh',
  description: 'Trích xuất văn bản OCR, xây dựng đồ thị tri thức (Knowledge Graph) và hỏi đáp AI trên tài liệu với DocuGraph RAG.',
  keywords: 'DocuGraph RAG, OCR, AI, RAG, Knowledge Graph, PDF, Chat, Neo4j, Gemini',
}

export default function RootLayout({ children }) {
  return (
    <html lang="vi" className="light" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <AuthProvider>
          <div className="min-h-screen bg-slate-50 text-slate-900">
            {children}
          </div>
        </AuthProvider>
      </body>
    </html>
  )
}
