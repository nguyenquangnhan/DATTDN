'use client'

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { apiLogin, apiRegister, apiGoogleAuth, apiGetMe, getStoredToken, setStoredToken } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore session on first load
  useEffect(() => {
    const restore = async () => {
      const token = getStoredToken()
      if (token) {
        try {
          const me = await apiGetMe()
          setUser(me)
        } catch {
          // Token expired or invalid - clear it
          setStoredToken(null)
        }
      }
      setLoading(false)
    }
    restore()
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password)
    setStoredToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const register = useCallback(async (email, password, fullName = '') => {
    const data = await apiRegister(email, password, fullName)
    setStoredToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const loginWithGoogle = useCallback(async (idToken) => {
    const data = await apiGoogleAuth(idToken)
    setStoredToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(() => {
    setStoredToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
