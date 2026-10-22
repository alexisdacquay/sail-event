import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { HINT_SEEN_KEY, MainPage, groupByDay, mostlyReason, runHeader, stageLines, stageText } from './MainPage'
import type { Event, SearchResult } from '@/services/api'

function renderMainPage() {
  localStorage.clear()
  localStorage.setItem('sail-event-token', 'test-token')
  localStorage.setItem('sail-event-username', 'demo')
  return render(
    <AuthProvider>
      <MainPage />
    </AuthProvider>,
  )
}

const base: Event = {
  id: 'a1', title: 'Accepted Gig', dateTime: '2026-10-20T20:00:00+02:00',
  place: 'A-Trane', link: 'https://example.com/a1', description: 'desc',
  startTz: 'Europe/Berlin', endTime: null, city: 'Berlin', country: 'DE',
  sourceUrl: null, band: 'fits', score: 95, scoreReason: 'Great match',
  status: 'accepted', decidedBy: 'auto',
}
const accepted = base
const sameDay: Event = { ...base, id: 'q1', title: 'Maybe Gig', dateTime: '2026-10-20T22:00:00+02:00', score: 55, scoreReason: 'Moderate', status: 'queued', decidedBy: null }
const nextDay: Event = { ...base, id: 'q2', title: 'Other Gig', dateTime: '2026-10-21', startTz: null, score: 58, status: 'queued', decidedBy: null }
const rejected: Event = { ...base, id: 'r1', title: 'Bad Gig', dateTime: '2026-10-22T20:00:00+02:00', score: 10, scoreReason: 'No match', status: 'rejected' }

const tiePath = () => screen.getByTestId('tie').querySelector('path')!.getAttribute('d')

async function mockEvents(events: Event[]) {
  const api = await import('@/services/api')
  vi.spyOn(api, 'listEvents').mockImplementation(async (status) => events.filter((e) => !status || e.status === status))
  return api
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('Stream page from mock data', () => {
  it('renders the search box, chronology, funnel, earlier runs and the rail', async () => {
    renderMainPage()
    await waitFor(() => expect(screen.getByTestId('criteria-text')).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument()
    expect(screen.getByTestId('criteria-hint')).toHaveTextContent('click the text to change it · Enter saves')
    const tl = await screen.findByTestId('run-chronology')
    expect(tl).toHaveTextContent('18 Oct')
    expect(tl).toHaveTextContent('your run · 1 min 30 s')
    expect(tl).toHaveTextContent('Searched the web, 31 pages')
    expect(tl).toHaveTextContent('Read 31 pages, found 12 events')
    expect(tl).toHaveTextContent('Skipped 2 pages that were not events')
    expect(tl).toHaveTextContent('Not judged: 5')
    expect(tl).toHaveTextContent('Judged 7 · 2 in calendar, 3 to review, 2 out')
    expect(screen.getByRole('button', { name: 'Search again' })).toBeInTheDocument()
    const funnel = screen.getByTestId('funnel')
    expect(funnel).toHaveTextContent('12 found')
    expect(funnel).toHaveTextContent('12 events from 8 pages')
    expect(funnel).toHaveTextContent('23 pages: no events')
    expect(document.body.textContent).not.toMatch(/set aside|rejected/i)
    // the mock has three runs; the current one (run-001) is not an earlier run
    expect(screen.getAllByTestId('earlier-run')).toHaveLength(2)
    expect(screen.getByTestId('month-calendar')).toBeInTheDocument()
    expect(screen.getByTestId('calendar-url')).toHaveValue('http://localhost:8000/api/calendar/mock-ics-token')
    expect(screen.getByTestId('searches')).toHaveTextContent('sailing regattas')
    expect(screen.getByRole('button', { name: '+ new search' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '+ new search' })).toHaveAttribute('title', 'coming later')
  })

  it('the text is edited in place: Esc cancels, Enter saves, blur saves, the hint goes after the first edit', async () => {
    const api = await import('@/services/api')
    const save = vi.spyOn(api, 'saveCriteria').mockImplementation(async (text) => ({ text, updatedAt: 'now', timeZone: 'Europe/Berlin' }))
    renderMainPage()
    const box = screen.getByLabelText("What I'm looking for")
    await waitFor(() => expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    fireEvent.change(box, { target: { value: 'jazz tonight in Berlin' } })
    expect(screen.queryByTestId('criteria-hint')).not.toBeInTheDocument()
    fireEvent.keyDown(box, { key: 'Escape' })
    expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026')
    fireEvent.blur(box)
    expect(save).not.toHaveBeenCalled()

    fireEvent.change(box, { target: { value: 'jazz tonight in Berlin' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(await screen.findByText('Saved.')).toBeInTheDocument()
    expect(save).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem(HINT_SEEN_KEY)).toBe('1')
    expect(screen.getByTestId('criteria-text')).toHaveValue('jazz tonight in Berlin')
    expect(screen.getByTestId('searches')).toHaveTextContent('jazz tonight in Berlin')
    expect(screen.queryByTestId('utc-notice')).not.toBeInTheDocument()

    fireEvent.change(box, { target: { value: 'folk in Paris' } })
    fireEvent.blur(box)
    await waitFor(() => expect(save).toHaveBeenCalledTimes(2))
    expect(save).toHaveBeenLastCalledWith('folk in Paris', expect.any(String))
  })

  it('shows the empty box with the hint when there is no saved search yet', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getCriteria').mockResolvedValue({ text: '', updatedAt: 'now', timeZone: 'UTC' })
    renderMainPage()
    expect(screen.getByLabelText("What I'm looking for")).toHaveValue('')
    expect(screen.getByTestId('criteria-hint')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Search again' })).toBeDisabled())
    expect(screen.getByTestId('utc-notice')).toHaveTextContent('Times shown in UTC until you save your criteria.')
  })

  it('does not show the hint again once a text was saved in this browser', async () => {
    renderMainPage()
    localStorage.setItem(HINT_SEEN_KEY, '1')
    render(<AuthProvider><MainPage /></AuthProvider>)
    await waitFor(() => expect(screen.getAllByTestId('criteria-text')).toHaveLength(2))
    expect(screen.getAllByTestId('criteria-hint')).toHaveLength(1)
  })
})

describe('Stream page results', () => {
  it('groups rows by day with aligned columns and collapses the rejected', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-10-21T12:00:00+02:00'))
    await mockEvents([accepted, sameDay, nextDay, rejected])
    renderMainPage()
    await screen.findByTestId('results-section')
    const days = screen.getAllByTestId('day-heading').map((d) => d.textContent)
    vi.useRealTimers()
    expect(days).toEqual(['Tue 20 Oct', 'Tonight · Wed 21 Oct'])
    expect(screen.getAllByTestId(/^event-row-/)).toHaveLength(3)
    // one column-header row above the list, aligned with the rows (same grid)
    const header = screen.getByTestId('row-header')
    expect(header).toHaveTextContent('EventStartWhereScoreStatus')
    expect(header.compareDocumentPosition(screen.getAllByTestId('day-heading')[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    const row = screen.getByTestId('event-row-a1')
    expect(within(row).getByRole('link', { name: 'Accepted Gig' })).toHaveAttribute('href', 'https://example.com/a1')
    expect(within(row).getByTestId('row-time')).toHaveTextContent('20:00')
    expect(within(row).getByTestId('row-place')).toHaveTextContent('A-Trane, Berlin, DE')
    expect(within(row).getByTestId('row-score')).toHaveTextContent('95%')
    expect(within(row).getByTestId('row-status')).toHaveTextContent('In calendar')
    expect(within(screen.getByTestId('event-row-q2')).getByTestId('row-time')).toHaveTextContent('no time')

    expect(screen.queryByTestId('event-row-r1')).not.toBeInTheDocument()
    expect(screen.getByText(/1 out, mostly wrong date or place/)).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('rejected-toggle'))
    expect(screen.getByTestId('event-row-r1')).toBeInTheDocument()
    expect(within(screen.getByTestId('event-row-r1')).getByTestId('row-status')).toHaveTextContent('Out')
  })

  it('selects one row at a time, shows the detail tied to it, and decides from the detail', async () => {
    const api = await mockEvents([accepted, sameDay])
    const decide = vi.spyOn(api, 'decideEvent').mockResolvedValue({ ...sameDay, status: 'accepted' })
    renderMainPage()
    await screen.findByTestId('results-section')
    expect(screen.queryByTestId('event-detail')).not.toBeInTheDocument()

    fireEvent.click(screen.getByTestId('event-row-q1'))
    const detail = screen.getByTestId('event-detail')
    expect(detail).toHaveTextContent('Maybe Gig')
    expect(detail).toHaveTextContent('Score 55%')
    expect(detail).toHaveTextContent('Moderate')
    expect(screen.getByTestId('event-row-q1')).toHaveAttribute('aria-pressed', 'true')
    expect(tiePath()).toMatch(/^M/)

    // keyboard: Enter on another row moves the selection
    fireEvent.keyDown(screen.getByTestId('event-row-a1'), { key: 'Enter' })
    expect(screen.getByTestId('event-detail')).toHaveTextContent('Accepted Gig')
    expect(screen.getByTestId('event-row-q1')).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getAllByTestId(/^event-row-/).filter((r) => r.getAttribute('aria-pressed') === 'true')).toHaveLength(1)

    fireEvent.click(screen.getByTestId('event-row-q1'))
    fireEvent.click(within(screen.getByTestId('event-detail')).getByRole('button', { name: 'Add to calendar' }))
    await waitFor(() => expect(decide).toHaveBeenCalledWith('q1', 'accepted'))

    fireEvent.click(within(screen.getByTestId('event-detail')).getByRole('button', { name: 'Close' }))
    expect(screen.queryByTestId('event-detail')).not.toBeInTheDocument()
    expect(tiePath()).toBe('')
  })

  it('clears the selection, the detail and the tie when the selected row leaves the list', async () => {
    const list = [accepted, sameDay]
    const api = await mockEvents(list)
    // deciding from the detail flips the row to rejected, which is folded away: the row disappears
    vi.spyOn(api, 'decideEvent').mockImplementation(async (id, decision) => {
      const e = list.find((x) => x.id === id)!
      e.status = decision
      return e
    })
    renderMainPage()
    await screen.findByTestId('results-section')
    fireEvent.click(screen.getByTestId('event-row-q1'))
    expect(screen.getByTestId('event-detail')).toHaveTextContent('Maybe Gig')
    expect(tiePath()).toMatch(/^M/)

    fireEvent.click(within(screen.getByTestId('event-detail')).getByRole('button', { name: 'Reject' }))
    await waitFor(() => expect(screen.queryByTestId('event-row-q1')).not.toBeInTheDocument())
    expect(screen.queryByTestId('event-detail')).not.toBeInTheDocument()
    expect(screen.queryAllByTestId(/^event-row-/).filter((r) => r.getAttribute('aria-pressed') === 'true')).toHaveLength(0)
    expect(tiePath()).toBe('')
    expect(screen.getByText(/1 out/)).toBeInTheDocument()
  })

  it('Clear all empties the events after confirm', async () => {
    const api = await mockEvents([accepted])
    vi.spyOn(api, 'deleteAllEvents').mockResolvedValue({ deleted: 1 })
    renderMainPage()
    await screen.findByTestId('results-section')
    fireEvent.click(screen.getByTestId('clear-all'))
    expect(screen.getByText('Delete all your events? This cannot be undone.')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('clear-all-confirm-yes'))
    await waitFor(() => expect(api.deleteAllEvents).toHaveBeenCalled())
    await waitFor(() => expect(screen.queryByTestId('results-section')).not.toBeInTheDocument())
  })
})

describe('Stream page live run', () => {
  const running: SearchResult = {
    runId: 'run-live', eventsFound: 0, eventsNew: 0,
    stageCounts: { results_fetched: 20, pages_content_pass: 7 },
    currentStage: 'extract', stoppedAtStage: null, error: null,
    startedAt: '2026-10-18T10:00:00+00:00', finishedAt: null, trigger: 'scheduled',
  }

  it('resumes the live line from last-run on reload', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getLastRun').mockResolvedValue({ run: running })
    renderMainPage()
    const live = await screen.findByTestId('search-progress')
    expect(live).toHaveTextContent('Reading pages 7 of 20…')
    const tl = screen.getByTestId('run-chronology')
    expect(tl).toHaveTextContent('automatic run · running…')
    expect(tl).toHaveTextContent('Searched the web, 20 pages')
    expect(tl).not.toHaveTextContent('Judged')
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
  })

  it('Search again runs a search and refreshes the page', async () => {
    const api = await import('@/services/api')
    const run = vi.spyOn(api, 'runSearch')
    renderMainPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Search again' }))
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
    await waitFor(() => expect(run).toHaveBeenCalled())
    expect(await screen.findByRole('button', { name: 'Search again' })).toBeEnabled()
    expect(screen.getByTestId('run-chronology')).toHaveTextContent('Judged 7 ·')
  })

  it('shows the 429 message with minutes from Retry-After', async () => {
    const api = await import('@/services/api')
    const err = new Error('Too many requests') as Error & { status: number; retryAfter: number }
    err.status = 429
    err.retryAfter = 300
    vi.spyOn(api, 'runSearch').mockRejectedValueOnce(err)
    renderMainPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Search again' }))
    expect(await screen.findByTestId('search-error')).toHaveTextContent('Search limit reached, try again in 5 minutes')
  })
})

describe('Stream page rail', () => {
  it('copy button and Reset link keep working', async () => {
    renderMainPage()
    fireEvent.click(await screen.findByTestId('rotate-calendar-url'))
    expect(screen.getByText('This will break any existing subscription. Reset?')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('rotate-confirm-cancel'))
    expect(screen.getByTestId('calendar-url')).toHaveValue('http://localhost:8000/api/calendar/mock-ics-token')
    fireEvent.click(screen.getByTestId('rotate-calendar-url'))
    fireEvent.click(screen.getByTestId('rotate-confirm-yes'))
    await waitFor(() => expect(screen.getByTestId('calendar-url')).not.toHaveValue('http://localhost:8000/api/calendar/mock-ics-token'))
    expect(screen.getByTestId('copy-calendar-url')).toHaveTextContent('Copy')
  })

  it('scoring stays reachable: validation and save', async () => {
    renderMainPage()
    const lower = await screen.findByRole('spinbutton', { name: 'Auto-reject below' })
    const upper = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    await waitFor(() => expect(lower).toHaveValue(30))
    fireEvent.change(lower, { target: { value: '80' } })
    fireEvent.change(upper, { target: { value: '50' } })
    expect(screen.getByText('The auto-accept line must be higher than the auto-reject line.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save scoring' })).toBeDisabled()
    fireEvent.change(lower, { target: { value: '20' } })
    fireEvent.change(upper, { target: { value: '90' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save scoring' }))
    await waitFor(() => expect(screen.getByText('Saved.')).toBeInTheDocument())
  })
})

// --- pure helpers ---

const finished: SearchResult = {
  runId: 'r1', eventsFound: 30, eventsNew: 10,
  stageCounts: { results_fetched: 20, pages_content_pass: 20, events_extracted: 31, filtered_past: 4, filtered_place: 2, filtered_duplicate: 3, events_judged: 22, accepted: 2, queued: 1, rejected: 19, rejected_date_place: 16, rejected_off_topic: 3 },
  currentStage: null, stoppedAtStage: null, error: null,
  startedAt: '2026-10-18T10:00:00+00:00', finishedAt: '2026-10-18T10:01:40+00:00',
}

describe('stageLines', () => {
  it('lists the four stage lines for a finished run', () => {
    expect(stageLines(finished)).toEqual([
      'Searched the web, 20 pages',
      'Read 20 pages, found 31 events',
      'Not judged: 9',
      'Judged 22 · 2 in calendar, 1 to review, 19 out',
    ])
  })

  it('found = not judged + judged, and non-events are a separate line', () => {
    const real = {
      results_fetched: 22, pages_content_pass: 0, events_extracted: 10, filtered_non_event: 12,
      filtered_incomplete: 1, judge_errors: 1, events_judged: 8,
      accepted: 3, queued: 1, rejected: 4,
    }
    const lines = stageLines({ ...finished, stageCounts: real })
    expect(lines).toEqual([
      'Searched the web, 22 pages',
      'Read 22 pages, found 10 events',
      'Skipped 12 pages that were not events',
      'Not judged: 2',
      'Judged 8 · 3 in calendar, 1 to review, 4 out',
    ])
    const num = (re: RegExp) => Number(lines.join('\n').match(re)![1])
    expect(num(/found (\d+) events/)).toBe(num(/Not judged: (\d+)/) + num(/Judged (\d+)/))
    expect(num(/Judged (\d+)/)).toBe(num(/(\d+) in calendar/) + num(/(\d+) to review/) + num(/(\d+) out/))
  })

  it('shows the finished stages then the live line while judging', () => {
    expect(stageLines({ ...finished, currentStage: 'judge', finishedAt: null, stageCounts: { ...finished.stageCounts, events_judged: 3 } })).toEqual([
      'Searched the web, 20 pages',
      'Read 20 pages, found 31 events',
      'Not judged: 9',
      'Judging 3 of 10 events…',
    ])
  })

  it('shows only the stop line for a run stopped at search', () => {
    expect(stageLines({ ...finished, stageCounts: { queries_planned: 2 }, stoppedAtStage: 'search', error: 'budget: search' }))
      .toEqual(['Stopped at search: budget: search.'])
  })

  it('shows Starting up… before the first stage', () => {
    expect(stageLines({ ...finished, stageCounts: null, currentStage: 'adapters', finishedAt: null })).toEqual(['Starting up…'])
  })
})

describe('runHeader', () => {
  it('falls back to the started/finished stamps for the duration', () => {
    expect(runHeader(finished)).toMatch(/^18 Oct \d\d:\d\d · 1 min 40 s$/)
    expect(runHeader({ ...finished, trigger: 'scheduled', durationSeconds: 45 })).toMatch(/automatic run · 45 s$/)
    // whole seconds: the backend sends a float
    expect(runHeader({ ...finished, durationSeconds: 100.3 })).toMatch(/1 min 40 s$/)
    expect(runHeader({ ...finished, durationSeconds: 119.6 })).toMatch(/2 min 0 s$/)
    expect(runHeader({ ...finished, trigger: 'manual', finishedAt: null, currentStage: 'search' })).toMatch(/your run · running…$/)
  })
})

describe('mostlyReason and groupByDay', () => {
  it('names the most common rejected reason', () => {
    expect(mostlyReason(finished.stageCounts!)).toBe('wrong date or place')
    expect(mostlyReason({ rejected_off_topic: 5, rejected_other: 1 })).toBe('off topic')
    expect(mostlyReason({ rejected_other: 1 })).toBe('below your threshold')
    expect(mostlyReason({ rejected: 3 })).toBe('')
  })

  it('groups in date order by day', () => {
    const groups = groupByDay([nextDay, sameDay, accepted])
    expect(groups.map(([d, es]) => [d, es.map((e) => e.id)])).toEqual([['Tue 20 Oct', ['a1', 'q1']], ['Wed 21 Oct', ['q2']]])
  })
})

describe('stageText', () => {
  it('shows stage-appropriate text for search stage', () => {
    expect(stageText({ ...finished, currentStage: 'search', finishedAt: null })).toBe('Searching the web…')
  })

  it('shows reading pages with counts for extract stage', () => {
    expect(stageText({ ...finished, currentStage: 'extract', finishedAt: null, stageCounts: { results_fetched: 20, pages_content_pass: 7 } })).toBe('Reading pages 7 of 20…')
  })

  it('shows done summary when finished', () => {
    expect(stageText(finished)).toBe('Done: 2 added to your calendar, 1 to review, 19 out')
  })
})
