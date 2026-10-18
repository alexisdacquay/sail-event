import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { MainPage } from './MainPage'

function renderMainPage(onSearchComplete = async () => 0) {
  localStorage.setItem('sail-event-token', 'test-token')
  localStorage.setItem('sail-event-username', 'demo')
  return render(
    <AuthProvider>
      <MainPage onSearchComplete={onSearchComplete} />
    </AuthProvider>,
  )
}

describe('MainPage cards', () => {
  it('renders all four card testids', async () => {
    renderMainPage()
    await screen.findByTestId('criteria-card')
    expect(screen.getByTestId('scoring-card')).toBeInTheDocument()
    expect(screen.getByTestId('search-card')).toBeInTheDocument()
    expect(screen.getByTestId('calendar-card')).toBeInTheDocument()
  })
})

describe('MainPage calendar feed', () => {
  it('shows the calendar URL and copy button', async () => {
    renderMainPage()

    const urlInput = await screen.findByTestId('calendar-url')
    expect(urlInput).toBeInTheDocument()
    expect(urlInput).toHaveValue('http://localhost:8000/api/calendar/mock-ics-token')

    expect(screen.getByTestId('copy-calendar-url')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Paste this link into your calendar app. Accepted events will appear there.',
      ),
    ).toBeInTheDocument()
  })

  it('shows inline confirmation when Reset link is clicked', async () => {
    renderMainPage()

    const rotateBtn = await screen.findByTestId('rotate-calendar-url')
    fireEvent.click(rotateBtn)

    expect(screen.getByTestId('rotate-confirm')).toBeInTheDocument()
    expect(
      screen.getByText(
        'This will break any existing subscription. Reset?',
      ),
    ).toBeInTheDocument()
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

  it('updates the URL on confirm', async () => {
    renderMainPage()

    const rotateBtn = await screen.findByTestId('rotate-calendar-url')
    fireEvent.click(rotateBtn)
    fireEvent.click(screen.getByTestId('rotate-confirm-yes'))

    const urlInput = await screen.findByTestId('calendar-url')
    await screen.findByTestId('rotate-calendar-url')
    expect((urlInput as HTMLInputElement).value).not.toBe(
      'http://localhost:8000/api/calendar/mock-ics-token',
    )
    expect(screen.queryByTestId('rotate-confirm')).not.toBeInTheDocument()
  })
})

describe('MainPage criteria card', () => {
  it('shows Saved. after save', async () => {
    renderMainPage()
    await screen.findByLabelText("What I'm looking for")
    fireEvent.click(screen.getByRole('button', { name: 'Save criteria' }))
    await waitFor(() => {
      expect(screen.getByText('Saved.')).toBeInTheDocument()
    })
  })
})

describe('MainPage scoring card', () => {
  it('shows validation error live when lower >= upper', async () => {
    renderMainPage()
    const lower = await screen.findByRole('spinbutton', { name: 'Auto-reject below' })
    const upper = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    fireEvent.change(lower, { target: { value: '80' } })
    fireEvent.change(upper, { target: { value: '50' } })
    expect(
      screen.getByText(
        'The auto-accept line must be higher than the auto-reject line.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save scoring' })).toBeDisabled()
  })
})

describe('MainPage search card', () => {
  it('shows hint and disabled button when criteria is empty', async () => {
    renderMainPage()
    const textarea = await screen.findByLabelText("What I'm looking for")
    fireEvent.change(textarea, { target: { value: '' } })
    expect(screen.getByRole('button', { name: 'Search now' })).toBeDisabled()
    expect(
      screen.getByText(
        "Write what you're looking for, then press Search now.",
      ),
    ).toBeInTheDocument()
  })

  it('calls onSearchComplete and shows queue count', async () => {
    const onSearchComplete = vi.fn().mockResolvedValue(5)
    renderMainPage(onSearchComplete)
    await screen.findByLabelText("What I'm looking for")

    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    expect(result).toHaveTextContent('Found 12 events, 4 new.')
    expect(result).toHaveTextContent('5 waiting for you in the Queue.')
    expect(onSearchComplete).toHaveBeenCalled()
  })
})
