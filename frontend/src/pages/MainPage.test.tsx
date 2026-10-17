import { fireEvent, render, screen } from '@testing-library/react'
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

  it('shows inline confirmation when Rotate link is clicked', async () => {
    renderMainPage()

    const rotateBtn = await screen.findByTestId('rotate-calendar-url')
    fireEvent.click(rotateBtn)

    expect(screen.getByTestId('rotate-confirm')).toBeInTheDocument()
    expect(screen.getByText('Are you sure?')).toBeInTheDocument()
    expect(screen.getByTestId('rotate-confirm-yes')).toBeInTheDocument()
    expect(screen.getByTestId('rotate-confirm-cancel')).toBeInTheDocument()
  })

  it('hides confirmation and keeps URL when Cancel is clicked', async () => {
    renderMainPage()

    const rotateBtn = await screen.findByTestId('rotate-calendar-url')
    fireEvent.click(rotateBtn)
    fireEvent.click(screen.getByTestId('rotate-confirm-cancel'))

    expect(screen.queryByTestId('rotate-confirm')).not.toBeInTheDocument()
    expect(screen.getByTestId('rotate-calendar-url')).toBeInTheDocument()
    expect(screen.getByTestId('calendar-url')).toHaveValue(
      'http://localhost:8000/api/calendar/mock-ics-token',
    )
  })

  it('updates the URL on Confirm', async () => {
    renderMainPage()

    const rotateBtn = await screen.findByTestId('rotate-calendar-url')
    fireEvent.click(rotateBtn)
    fireEvent.click(screen.getByTestId('rotate-confirm-yes'))

    const urlInput = await screen.findByTestId('calendar-url')
    // After rotation the mock generates a new token with timestamp
    await screen.findByTestId('rotate-calendar-url')
    expect((urlInput as HTMLInputElement).value).not.toBe(
      'http://localhost:8000/api/calendar/mock-ics-token',
    )
    expect(screen.queryByTestId('rotate-confirm')).not.toBeInTheDocument()
  })
})
