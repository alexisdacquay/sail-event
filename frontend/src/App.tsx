import { useState } from 'react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { MainPage } from '@/pages/MainPage'
import { Button } from '@/components/ui/button'
import { SailMark } from '@/components/SailMark'
import { ThemeToggle } from '@/components/ThemeToggle'

function AuthenticatedLayout() {
  const { auth, logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 h-14 border-b bg-card/80 backdrop-blur px-4 sm:px-8 flex items-center gap-4">
        <h1 className="flex items-center gap-2 font-heading text-lg sm:text-xl font-bold tracking-tight whitespace-nowrap"><SailMark className="size-6" aria-hidden="true" />Sail Event</h1>
        <div className="flex items-center gap-3 ml-auto">
          <span className="hidden sm:inline text-sm text-muted-foreground">
            {auth?.username}
          </span>
          <Button variant="outline" size="sm" onClick={logout}>
            Sign out
          </Button>
          <ThemeToggle />
        </div>
      </header>
      <main className="flex-1 p-4 sm:p-8 mx-auto w-full max-w-5xl">
        <MainPage />
      </main>
    </div>
  )
}

function AppRouter() {
  const { auth } = useAuth()
  const [page, setPage] = useState<'login' | 'register'>('login')

  if (!auth) {
    if (page === 'register') {
      return <RegisterPage onNavigateLogin={() => setPage('login')} />
    }
    return <LoginPage onNavigateRegister={() => setPage('register')} />
  }

  return <AuthenticatedLayout />
}

function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  )
}

export default App
