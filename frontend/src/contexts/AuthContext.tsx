import { createContext, useContext, useState, useCallback } from 'react'
import type { ReactNode } from 'react'

type AuthState = { token: string; username: string } | null

type AuthContextValue = {
  auth: AuthState
  setAuth: (auth: AuthState) => void
  logout: () => void
}

const TOKEN_KEY = 'sail-event-token'
const USER_KEY = 'sail-event-username'

function loadAuth(): AuthState {
  try {
    const token = localStorage.getItem(TOKEN_KEY)
    const username = localStorage.getItem(USER_KEY)
    if (token && username) return { token, username }
  } catch {
    // private browsing or blocked storage
  }
  return null
}

function persistAuth(auth: AuthState) {
  try {
    if (auth) {
      localStorage.setItem(TOKEN_KEY, auth.token)
      localStorage.setItem(USER_KEY, auth.username)
    } else {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  } catch {
    // ignore
  }
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuthState] = useState<AuthState>(loadAuth)

  const setAuth = useCallback((next: AuthState) => {
    persistAuth(next)
    setAuthState(next)
  }, [])

  const logout = useCallback(() => {
    persistAuth(null)
    setAuthState(null)
  }, [])

  return (
    <AuthContext value={{ auth, setAuth, logout }}>{children}</AuthContext>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
