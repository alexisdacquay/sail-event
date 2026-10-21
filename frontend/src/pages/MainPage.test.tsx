import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { MainPage } from './MainPage'
import type { Event } from '@/services/api'

const emptyQueue: Event[] = []

function renderMainPage(
  onSearchComplete = async () => 0,
  queuedEvents: Event[] = emptyQueue,
  onNavigateQueue = () => {},
) {
  localStorage.setItem('sail-event-token', 'test-token')
  localStorage.setItem('sail-event-username', 'demo')
  return render(
    <AuthProvider>
      <MainPage
        onSearchComplete={onSearchComplete}
        queuedEvents={queuedEvents}
        onNavigateQueue={onNavigateQueue}
      />
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

  it('shows UTC notice when user timeZone is UTC', async () => {
    renderMainPage()
    const notice = await screen.findByTestId('utc-notice')
    expect(notice).toHaveTextContent(
      'Times shown in UTC until you save your criteria.',
    )
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

  it('explainer shows live threshold numbers', async () => {
    renderMainPage()
    await screen.findByRole('spinbutton', { name: 'Auto-reject below' })
    expect(screen.getByText('Below 30: rejected.')).toBeInTheDocument()
    expect(screen.getByText('Above 70: accepted.')).toBeInTheDocument()
  })

  it('shows band meaning explanation', async () => {
    renderMainPage()
    await screen.findByRole('spinbutton', { name: 'Auto-reject below' })
    expect(
      screen.getByText(/Recommended thresholds: 90 \/ 40/),
    ).toBeInTheDocument()
    expect(screen.getByText(/90\+ fits/)).toBeInTheDocument()
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

  it('calls onSearchComplete and shows run report', async () => {
    const onSearchComplete = vi.fn().mockResolvedValue(5)
    renderMainPage(onSearchComplete)
    await screen.findByLabelText("What I'm looking for")

    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    // Run report includes the pipeline line
    expect(result).toHaveTextContent(/6 queries → 31 results → 12 events → 9 passed filters → 7 judged/)
    expect(result).toHaveTextContent(/2 accepted, 3 queued, 2 rejected/)
    expect(screen.getByRole('button', { name: /Review 5 events/ })).toBeInTheDocument()
    expect(onSearchComplete).toHaveBeenCalled()
  })

  it('shows filter details in run report', async () => {
    const onSearchComplete = vi.fn().mockResolvedValue(0)
    renderMainPage(onSearchComplete)
    await screen.findByLabelText("What I'm looking for")

    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    expect(result).toHaveTextContent(/Filtered:/)
    expect(result).toHaveTextContent(/2 past/)
  })

  it('shows 429 rate-limit message with minutes from Retry-After', async () => {
    const { runSearch: _orig } = await import('@/services/api')
    const api = await import('@/services/api')
    const err = new Error('Too many requests') as Error & { status: number; retryAfter: number }
    err.status = 429
    err.retryAfter = 300 // 5 minutes
    vi.spyOn(api, 'runSearch').mockRejectedValueOnce(err)

    renderMainPage()
    await screen.findByLabelText("What I'm looking for")

    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    expect(result).toHaveTextContent('Search limit reached, try again in 5 minutes')
    vi.restoreAllMocks()
  })

  it('shows stopped-at stage and error in run report', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'runSearch').mockResolvedValueOnce({
      runId: 'run-stop',
      eventsFound: 0,
      eventsNew: 0,
      stageCounts: {
        queries_planned: 2,
        results_fetched: 0,
      },
      stoppedAtStage: 'search',
      error: 'budget: search',
    })

    const onSearchComplete = vi.fn().mockResolvedValue(0)
    renderMainPage(onSearchComplete)
    await screen.findByLabelText("What I'm looking for")

    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    expect(result).toHaveTextContent('Stopped at search: budget: search.')
    vi.restoreAllMocks()
  })
})

describe('MainPage right column', () => {
  it('shows To review sidebar when queued events exist', async () => {
    const queued: Event[] = [
      {
        id: 'q1',
        title: 'Queued Event 1',
        dateTime: '2026-07-15T20:00:00Z',
        place: 'Venue',
        link: 'https://example.com/q1',
        description: '',
        startTz: 'Europe/London',
        endTime: null,
        city: 'London',
        country: 'GB',
        sourceUrl: null,
        band: 'open question',
        score: 55,
        scoreReason: 'moderate',
        status: 'queued',
        decidedBy: null,
      },
    ]
    renderMainPage(async () => 1, queued)
    await screen.findByTestId('criteria-card')
    expect(screen.getByTestId('review-sidebar')).toBeInTheDocument()
    expect(screen.getByText('Queued Event 1')).toBeInTheDocument()
    expect(screen.getByText('Score 55%')).toBeInTheDocument()
  })

  it('hides sidebar when no queued events', async () => {
    renderMainPage()
    await screen.findByTestId('criteria-card')
    expect(screen.queryByTestId('review-sidebar')).not.toBeInTheDocument()
  })
})
