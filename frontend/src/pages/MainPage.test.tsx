import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { MainPage } from './MainPage'

function renderMainPage() {
  // Simulate logged-in state so useAuth doesn't throw
  localStorage.setItem('sail-event-token', 'test-token')
  localStorage.setItem('sail-event-username', 'demo')
  return render(
    <AuthProvider>
      <MainPage embedded />
    </AuthProvider>,
  )
}

describe('MainPage calendar feed', () => {
  it('shows the calendar URL and copy button', async () => {
    renderMainPage()

    const urlInput = await screen.findByTestId('calendar-url')
    expect(urlInput).toBeInTheDocument()
    expect(urlInput).toHaveValue('http://localhost:8000/api/calendar/mock-ics-token')

    expect(screen.getByTestId('copy-calendar-url')).toBeInTheDocument()
    expect(screen.getByText('Subscribe from your calendar app')).toBeInTheDocument()
  })
})
