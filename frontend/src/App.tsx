import { useCallback, useEffect, useState } from 'react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { MainPage } from '@/pages/MainPage'
import { EventsPage } from '@/pages/EventsPage'
import { QueuePage } from '@/pages/QueuePage'
import { Button } from '@/components/ui/button'
import { listEvents } from '@/services/api'

type Page = 'login' | 'register' | 'main' | 'events' | 'queue'

const tabs: { page: Page; label: string }[] = [
  { page: 'main', label: 'Home' },
  { page: 'queue', label: 'Queue' },
  { page: 'events', label: 'All events' },
]

function AuthenticatedLayout() {
  const { auth, logout } = useAuth()
  const [page, setPage] = useState<Page>('main')
  const [queueCount, setQueueCount] = useState(0)

  const refreshQueueCount = useCallback(async () => {
    const queued = await listEvents('queued')
    const count = queued.length
    setQueueCount(count)
    return count
  }, [])

  useEffect(() => {
    refreshQueueCount()
  }, [refreshQueueCount])

  function handleTabClick(target: Page) {
    setPage(target)
    refreshQueueCount()
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b px-4 sm:px-8 py-3 flex flex-wrap items-center gap-x-6 gap-y-2">
        <h1 className="text-lg sm:text-xl font-bold whitespace-nowrap">Sail Event</h1>
        <nav className="flex gap-1 order-last w-full sm:order-none sm:w-auto" aria-label="Main navigation">
          {tabs.map((tab) => (
            <Button
              key={tab.page}
              variant={page === tab.page ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handleTabClick(tab.page)}
              aria-current={page === tab.page ? 'page' : undefined}
            >
              {tab.label}
              {tab.page === 'queue' && queueCount > 0 && (
                <span className="ml-1 text-xs" data-testid="queue-count">({queueCount})</span>
              )}
            </Button>
          ))}
        </nav>
        <div className="flex items-center gap-4 ml-auto">
          <span className="hidden sm:inline text-sm text-muted-foreground">
            {auth?.username}
          </span>
          <Button variant="outline" size="sm" onClick={logout}>
            Sign out
          </Button>
        </div>
      </header>
      <main className="flex-1 p-8 max-w-2xl mx-auto w-full">
        {page === 'main' && <MainPage onSearchComplete={refreshQueueCount} />}
        {page === 'events' && <EventsPage />}
        {page === 'queue' && (
          <QueuePage onQueueChange={refreshQueueCount} />
        )}
      </main>
    </div>
  )
}

function AppRouter() {
  const { auth } = useAuth()
  const [page, setPage] = useState<Page>('login')

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
