/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi, refreshAccessToken } from '@/lib/api'
import { setAccessToken } from '@/lib/tokenStore'
import type { User, LoginRequest, RegisterRequest } from '@/types'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  const isAuthenticated = !!user

  useEffect(() => {
    const initAuth = async () => {
      // Restore the session from the HttpOnly refresh cookie, if any
      try {
        await refreshAccessToken()
        const userData = await authApi.getMe()
        setUser(userData)
      } catch {
        setAccessToken(null)
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (data: LoginRequest) => {
    const response = await authApi.login(data)
    setAccessToken(response.access_token)

    const userData = await authApi.getMe()
    setUser(userData)
    navigate('/dashboard')
  }

  const register = async (data: RegisterRequest) => {
    const response = await authApi.register(data)
    setAccessToken(response.access_token)

    const userData = await authApi.getMe()
    setUser(userData)
    navigate('/dashboard')
  }

  const logout = () => {
    authApi
      .logout()
      .catch(() => {
        // Ignore errors, we're logging out anyway
      })
      .finally(() => setAccessToken(null))

    setUser(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
