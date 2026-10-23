'use client'

import { useState } from 'react'
import { Eye, EyeOff, Mail, Lock, User, BookOpen, Sparkles, ArrowRight, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function AuthModal() {
  const { login, register, loginWithGoogle } = useAuth()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [form, setForm] = useState({ email: '', password: '', fullName: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        if (!form.fullName.trim()) {
          setError('Vui lòng nhập họ và tên')
          setLoading(false)
          return
        }
        await register(form.email, form.password, form.fullName)
      }
    } catch (err) {
      setError(err.message || 'Đã có lỗi xảy ra. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  const switchMode = () => {
    setMode(m => m === 'login' ? 'register' : 'login')
    setError('')
    setForm({ email: '', password: '', fullName: '' })
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0fdf4 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
    }}>
      {/* Background decorative orbs */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        overflow: 'hidden', pointerEvents: 'none', zIndex: 0,
      }}>
        <div style={{
          position: 'absolute', top: '-10%', left: '-5%',
          width: '400px', height: '400px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', bottom: '-10%', right: '-5%',
          width: '500px', height: '500px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', top: '30%', right: '10%',
          width: '250px', height: '250px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)',
        }} />
      </div>

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: '440px' }}>
        {/* Logo & Brand */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: '64px', height: '64px', borderRadius: '20px', marginBottom: '16px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            boxShadow: '0 8px 32px rgba(99,102,241,0.3)',
          }}>
            <Sparkles size={32} color="white" />
          </div>
          <h1 style={{
            fontSize: '28px', fontWeight: '800', color: '#0f172a',
            margin: '0 0 8px 0', letterSpacing: '-0.5px',
          }}>
            DocuGraph RAG
          </h1>
          <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
            Nền tảng trích xuất & hỏi đáp tài liệu thông minh
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: 'rgba(255,255,255,0.85)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderRadius: '24px',
          border: '1px solid rgba(99,102,241,0.12)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04)',
          padding: '36px',
        }}>
          {/* Tab switcher */}
          <div style={{
            display: 'flex', background: '#f1f5f9', borderRadius: '12px',
            padding: '4px', marginBottom: '28px',
          }}>
            {['login', 'register'].map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(''); setForm({ email: '', password: '', fullName: '' }) }}
                style={{
                  flex: 1, padding: '10px', borderRadius: '10px', border: 'none',
                  cursor: 'pointer', fontSize: '14px', fontWeight: '600',
                  transition: 'all 0.2s ease',
                  background: mode === m ? 'white' : 'transparent',
                  color: mode === m ? '#6366f1' : '#64748b',
                  boxShadow: mode === m ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                {m === 'login' ? 'Đăng nhập' : 'Đăng ký'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            {/* Full name field (register only) */}
            {mode === 'register' && (
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
                  Họ và tên
                </label>
                <div style={{ position: 'relative' }}>
                  <User size={16} style={{
                    position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af'
                  }} />
                  <input
                    id="auth-fullname"
                    name="fullName"
                    type="text"
                    value={form.fullName}
                    onChange={handleChange}
                    placeholder="Nguyễn Văn A"
                    required
                    style={inputStyle}
                  />
                </div>
              </div>
            )}

            {/* Email */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
                Email
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} style={{
                  position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af'
                }} />
                <input
                  id="auth-email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="name@example.com"
                  required
                  style={inputStyle}
                />
              </div>
            </div>

            {/* Password */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
                Mật khẩu {mode === 'register' && <span style={{ fontWeight: '400', color: '#9ca3af' }}>(ít nhất 6 ký tự)</span>}
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={{
                  position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af'
                }} />
                <input
                  id="auth-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  required
                  minLength={6}
                  style={{ ...inputStyle, paddingRight: '44px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  style={{
                    position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af', padding: '2px',
                  }}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div style={{
                background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px',
                padding: '12px 14px', marginBottom: '16px',
                fontSize: '13px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <span>⚠️</span> {error}
              </div>
            )}

            {/* Submit button */}
            <button
              id="auth-submit"
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '13px',
                background: loading ? '#a5b4fc' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: 'white', border: 'none', borderRadius: '12px',
                fontSize: '15px', fontWeight: '700', cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'all 0.2s ease',
                boxShadow: loading ? 'none' : '0 4px 16px rgba(99,102,241,0.35)',
              }}
            >
              {loading ? (
                <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Đang xử lý...</>
              ) : (
                <>{mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'} <ArrowRight size={16} /></>
              )}
            </button>
          </form>

          {/* Divider */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            margin: '20px 0', color: '#cbd5e1', fontSize: '13px',
          }}>
            <div style={{ flex: 1, height: '1px', background: '#e2e8f0' }} />
            <span style={{ color: '#94a3b8', fontWeight: '500' }}>hoặc</span>
            <div style={{ flex: 1, height: '1px', background: '#e2e8f0' }} />
          </div>

          {/* Google Sign-In */}
          <GoogleSignInButton onSuccess={loginWithGoogle} />

          {/* Features teaser */}
          <div style={{
            marginTop: '28px', paddingTop: '20px',
            borderTop: '1px solid #f1f5f9',
            display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center',
          }}>
            {['📁 PDF & Ảnh', '🌐 URL', '💬 Chat AI', '📊 Knowledge Graph'].map(f => (
              <span key={f} style={{
                fontSize: '12px', color: '#64748b', background: '#f8fafc',
                padding: '4px 10px', borderRadius: '20px', border: '1px solid #e2e8f0',
              }}>
                {f}
              </span>
            ))}
          </div>
        </div>

        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '12px', color: '#94a3b8' }}>
          Bằng cách tiếp tục, bạn đồng ý với Điều khoản dịch vụ của chúng tôi.
        </p>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        input:focus { outline: none; border-color: #6366f1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important; }
        button:not([disabled]):hover { opacity: 0.92; transform: translateY(-1px); }
      `}</style>
    </div>
  )
}

// ── Google Sign-In Button ─────────────────────────────────────────────────────

function GoogleSignInButton({ onSuccess }) {
  const [loading, setLoading] = useState(false)

  const handleGoogleClick = () => {
    // Show instruction since we need Google Client ID configured
    alert('Để sử dụng đăng nhập Google, vui lòng điền GOOGLE_CLIENT_ID vào backend/.env và tích hợp Google Sign-In SDK ở frontend.')
  }

  return (
    <button
      id="google-signin-btn"
      type="button"
      onClick={handleGoogleClick}
      disabled={loading}
      style={{
        width: '100%', padding: '13px',
        background: 'white', border: '1.5px solid #e2e8f0',
        borderRadius: '12px', fontSize: '14px', fontWeight: '600',
        cursor: 'pointer', display: 'flex', alignItems: 'center',
        justifyContent: 'center', gap: '10px', color: '#374151',
        transition: 'all 0.2s ease',
        boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      }}
    >
      {/* Google logo SVG */}
      <svg width="18" height="18" viewBox="0 0 18 18">
        <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/>
        <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 0 1-7.18-2.54H1.83v2.07A8 8 0 0 0 8.98 17z"/>
        <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 0 1 0-3.04V5.41H1.83a8 8 0 0 0 0 7.18l2.67-2.07z"/>
        <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 1.83 5.4L4.5 7.49a4.77 4.77 0 0 1 4.48-3.31z"/>
      </svg>
      Đăng nhập với Google
    </button>
  )
}

// ── Shared Styles ─────────────────────────────────────────────────────────────

const inputStyle = {
  width: '100%', padding: '11px 14px 11px 40px',
  border: '1.5px solid #e2e8f0', borderRadius: '10px',
  fontSize: '14px', color: '#0f172a', background: '#fafafa',
  transition: 'all 0.2s ease', boxSizing: 'border-box',
}
