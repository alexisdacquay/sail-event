import { useState } from 'react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { MainPage } from '@/pages/MainPage'

type Page = 'login' | 'register' | 'main'

function AppRouter() {
  const { auth } = useAuth()
  const [page, setPage] = useState<Page>('login')

  if (!auth) {
    if (page === 'register') {
      return <RegisterPage onNavigateLogin={() => setPage('login')} />
    }
    return <LoginPage onNavigateRegister={() => setPage('register')} />
  }

  return <MainPage />
}

function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  )
}

export default App
