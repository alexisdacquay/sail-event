import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { MainPage, stageText } from './MainPage'
import type { Event, SearchResult } from '@/services/api'

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

beforeEach(() => {
  vi.restoreAllMocks()
})

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
    expect(result).toHaveTextContent(/6 queries → 31 results/)
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
      currentStage: null,
      stoppedAtStage: 'search',
      error: 'budget: search',
      startedAt: '2026-10-18T10:00:00+00:00',
      finishedAt: '2026-10-18T10:00:05+00:00',
    })

    const onSearchComplete = vi.fn().mockResolvedValue(0)
    renderMainPage(onSearchComplete)
    await screen.findByLabelText("What I'm looking for")

    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    expect(result).toHaveTextContent('Stopped at search: budget: search.')
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

// --- #104: live progress ---

describe('stageText', () => {
  it('shows stage-appropriate text for search stage', () => {
    const run: SearchResult = {
      runId: 'r1', eventsFound: 0, eventsNew: 0,
      stageCounts: { results_fetched: 10 },
      currentStage: 'search',
      stoppedAtStage: null, error: null,
      startedAt: '2026-10-18T10:00:00+00:00', finishedAt: null,
    }
    expect(stageText(run)).toBe('Searching the web…')
  })

  it('shows reading pages with counts for extract stage', () => {
    const run: SearchResult = {
      runId: 'r1', eventsFound: 0, eventsNew: 0,
      stageCounts: { results_fetched: 20, pages_content_pass: 7 },
      currentStage: 'extract',
      stoppedAtStage: null, error: null,
      startedAt: '2026-10-18T10:00:00+00:00', finishedAt: null,
    }
    expect(stageText(run)).toBe('Reading pages 7 of 20…')
  })

  it('shows judging with counts for judge stage', () => {
    const run: SearchResult = {
      runId: 'r1', eventsFound: 5, eventsNew: 5,
      stageCounts: { events_judged: 3 },
      currentStage: 'judge',
      stoppedAtStage: null, error: null,
      startedAt: '2026-10-18T10:00:00+00:00', finishedAt: null,
    }
    expect(stageText(run)).toBe('Judging 3 of 5 events…')
  })

  it('shows done summary when finished', () => {
    const run: SearchResult = {
      runId: 'r1', eventsFound: 30, eventsNew: 10,
      stageCounts: { accepted: 3, queued: 5, rejected: 22 },
      currentStage: null,
      stoppedAtStage: null, error: null,
      startedAt: '2026-10-18T10:00:00+00:00', finishedAt: '2026-10-18T10:01:30+00:00',
    }
    expect(stageText(run)).toBe('Done: 3 added to your calendar, 5 to review, 22 rejected')
  })
})

// --- #104: results section ---

describe('MainPage results section', () => {
  it('shows accepted and queued groups from fetched events', async () => {
    const api = await import('@/services/api')
    const accepted: Event[] = [{
      id: 'a1', title: 'Accepted Gig', dateTime: '2026-10-20T20:00:00+02:00',
      place: 'Berlin', link: 'https://example.com/a1', description: 'desc',
      startTz: 'Europe/Berlin', endTime: null, city: 'Berlin', country: 'DE',
      sourceUrl: null, band: 'fits', score: 95, scoreReason: 'Great match',
      status: 'accepted', decidedBy: 'auto',
    }]
    const queued: Event[] = [{
      id: 'q1', title: 'Maybe Gig', dateTime: '2026-10-21T18:00:00+02:00',
      place: 'Berlin', link: 'https://example.com/q1', description: 'desc',
      startTz: 'Europe/Berlin', endTime: null, city: 'Berlin', country: 'DE',
      sourceUrl: null, band: 'open question', score: 55, scoreReason: 'Moderate',
      status: 'queued', decidedBy: null,
    }]
    const rejected: Event[] = [{
      id: 'r1', title: 'Bad Gig', dateTime: '2026-10-22T20:00:00+02:00',
      place: 'Berlin', link: 'https://example.com/r1', description: 'desc',
      startTz: 'Europe/Berlin', endTime: null, city: 'Berlin', country: 'DE',
      sourceUrl: null, band: 'off topic', score: 10, scoreReason: 'No match',
      status: 'rejected', decidedBy: 'auto',
    }]

    vi.spyOn(api, 'listEvents').mockImplementation(async (status) => {
      if (status === 'accepted') return accepted
      if (status === 'queued') return queued
      if (status === 'rejected') return rejected
      return [...accepted, ...queued, ...rejected]
    })

    renderMainPage()
    await screen.findByTestId('results-section')
    expect(screen.getByTestId('results-accepted')).toBeInTheDocument()
    expect(screen.getByText('In your calendar (1)')).toBeInTheDocument()
    expect(screen.getByText('Accepted Gig')).toBeInTheDocument()
    expect(screen.getByTestId('results-queued')).toBeInTheDocument()
    expect(screen.getByText('To review (1)')).toBeInTheDocument()
    expect(screen.getByText('Maybe Gig')).toBeInTheDocument()
    expect(screen.getByTestId('results-rejected')).toBeInTheDocument()
    expect(screen.getByText(/Rejected \(1\)/)).toBeInTheDocument()
    // Summary line
    expect(screen.getByTestId('results-summary')).toHaveTextContent('1 in your calendar · 1 to review · 1 rejected')
  })

  it('shows Clear all button that empties events after confirm', async () => {
    const api = await import('@/services/api')
    const accepted: Event[] = [{
      id: 'a1', title: 'Accepted Gig', dateTime: '2026-10-20T20:00:00+02:00',
      place: 'Berlin', link: 'https://example.com/a1', description: 'desc',
      startTz: 'Europe/Berlin', endTime: null, city: 'Berlin', country: 'DE',
      sourceUrl: null, band: 'fits', score: 95, scoreReason: 'Great match',
      status: 'accepted', decidedBy: 'auto',
    }]

    vi.spyOn(api, 'listEvents').mockImplementation(async (status) => {
      if (status === 'accepted') return accepted
      if (status === 'queued') return []
      if (status === 'rejected') return []
      return accepted
    })
    vi.spyOn(api, 'deleteAllEvents').mockResolvedValue({ deleted: 1 })

    const onSearchComplete = vi.fn().mockResolvedValue(0)
    renderMainPage(onSearchComplete)

    await screen.findByTestId('results-section')
    // Click Clear all -> shows confirmation
    fireEvent.click(screen.getByTestId('clear-all'))
    expect(screen.getByTestId('clear-all-confirm')).toBeInTheDocument()
    expect(screen.getByText('Delete all your events? This cannot be undone.')).toBeInTheDocument()

    // Confirm
    fireEvent.click(screen.getByTestId('clear-all-confirm-yes'))
    await waitFor(() => {
      expect(api.deleteAllEvents).toHaveBeenCalled()
    })
    // Results section should be gone after clear
    await waitFor(() => {
      expect(screen.queryByTestId('results-section')).not.toBeInTheDocument()
    })
  })
})
