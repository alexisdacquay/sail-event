import { createContext, useContext, useState, useCallback } from 'react'
import type { ReactNode } from 'react'

type AuthState = { token: string; username: string } | null

type AuthContextValue = {
  auth: AuthState
  setAuth: (auth: AuthState) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>(null)
  const logout = useCallback(() => setAuth(null), [])
  return (
    <AuthContext value={{ auth, setAuth, logout }}>{children}</AuthContext>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
