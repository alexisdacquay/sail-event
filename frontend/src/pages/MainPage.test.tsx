import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { MainPage, groupByDay, mostlyReason, runHeader, stageFraction, stageLines, stageText } from './MainPage'
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

afterEach(() => {
  vi.useRealTimers()
})

describe('Stream page from mock data', () => {
  it('renders the search box, chronology, funnel, earlier runs and the rail', async () => {
    renderMainPage()
    await waitFor(() => expect(screen.getByTestId('criteria-text')).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument()
    const tl = await screen.findByTestId('run-chronology')
    expect(tl).toHaveTextContent('18 Oct')
    expect(tl).toHaveTextContent('your run · 1 min 30 s')
    expect(tl).toHaveTextContent('Searched the web, 31 pages')
    expect(tl).toHaveTextContent('Read 31 pages, found 12 events')
    expect(tl).toHaveTextContent('Skipped 2 pages that were not events')
    expect(tl).toHaveTextContent('Screened out: 5')
    expect(tl).toHaveTextContent('Judged 7 · 2 in calendar, 3 to review, 2 rejected')
    expect(screen.getByRole('button', { name: 'Search again' })).toBeInTheDocument()
    const funnel = screen.getByTestId('funnel')
    expect(funnel).toHaveTextContent('12 found')
    expect(funnel).toHaveTextContent('from 8 of 31 pages read')
    expect(document.body.textContent).not.toMatch(/set aside|not judged/i)
    // the mock has three runs; the current one (run-001) is not an earlier run
    expect(screen.getAllByTestId('earlier-run')).toHaveLength(2)
    expect(screen.getByTestId('month-calendar')).toBeInTheDocument()
    expect(screen.getByTestId('calendar-url')).toHaveValue('http://localhost:8000/api/calendar/mock-ics-token')
    expect(screen.getByTestId('searches')).toHaveTextContent('sailing regattas')
    expect(screen.getByRole('button', { name: '+ new search' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '+ new search' })).toHaveAttribute('title', 'coming later')
  })

  /** saveCriteria and runSearch spies that record their call order. */
  async function spyPutThenPost() {
    const api = await import('@/services/api')
    const calls: string[] = []
    const save = vi.spyOn(api, 'saveCriteria').mockImplementation(async (text) => { calls.push(`PUT ${text}`); return { text, updatedAt: 'now', timeZone: 'Europe/Berlin' } })
    const real = api.runSearch
    vi.spyOn(api, 'runSearch').mockImplementation(async () => { calls.push('POST'); return real() })
    return { calls, save }
  }

  it('typing then clicking Search once saves and runs: PUT then POST with the typed text', async () => {
    const { calls } = await spyPutThenPost()
    renderMainPage()
    const box = screen.getByLabelText('What are you looking for?')
    await waitFor(() => expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    fireEvent.change(box, { target: { value: 'jazz tonight in Berlin' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search again' }))
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
    await waitFor(() => expect(calls).toEqual(['PUT jazz tonight in Berlin', 'POST']))
    expect(await screen.findByRole('button', { name: 'Search again' })).toBeEnabled()
    expect(screen.getByTestId('searches')).toHaveTextContent('jazz tonight in Berlin')
  })

  it('Enter saves and runs, Shift+Enter is left to insert a newline, Esc restores the saved text', async () => {
    const { calls } = await spyPutThenPost()
    renderMainPage()
    const box = screen.getByLabelText('What are you looking for?')
    await waitFor(() => expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    fireEvent.change(box, { target: { value: 'jazz tonight in Berlin' } })
    // Shift+Enter: default not prevented (the browser inserts the newline), nothing sent
    expect(fireEvent.keyDown(box, { key: 'Enter', shiftKey: true })).toBe(true)
    expect(calls).toEqual([])
    fireEvent.keyDown(box, { key: 'Escape' })
    expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026')

    fireEvent.change(box, { target: { value: 'folk in Paris' } })
    expect(fireEvent.keyDown(box, { key: 'Enter' })).toBe(false)
    await waitFor(() => expect(calls).toEqual(['PUT folk in Paris', 'POST']))
    await screen.findByRole('button', { name: 'Search again' })
    fireEvent.change(box, { target: { value: 'something else' } })
    fireEvent.keyDown(box, { key: 'Escape' })
    expect(box).toHaveValue('folk in Paris')
  })

  it('keeps what the user typed when the saved criteria load late', async () => {
    const api = await import('@/services/api')
    let loaded!: (c: { text: string; updatedAt: string; timeZone: string }) => void
    vi.spyOn(api, 'getCriteria').mockReturnValue(new Promise((resolve) => { loaded = resolve }))
    const { calls } = await spyPutThenPost()
    renderMainPage()
    const box = screen.getByLabelText('What are you looking for?')
    fireEvent.change(box, { target: { value: 'jazz tonight in Berlin' } })
    await act(async () => loaded({ text: '', updatedAt: 'now', timeZone: 'UTC' }))
    expect(box).toHaveValue('jazz tonight in Berlin')
    fireEvent.keyDown(box, { key: 'Enter' })
    await waitFor(() => expect(calls).toEqual(['PUT jazz tonight in Berlin', 'POST']))
    expect(api.saveCriteria).toHaveBeenCalledWith('jazz tonight in Berlin', expect.any(String))
  })

  it('no hint, no Saved., no UTC line; the placeholder shows when empty and differs in style from the typed text', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getCriteria').mockResolvedValue({ text: '', updatedAt: 'now', timeZone: 'UTC' })
    renderMainPage()
    const box = screen.getByLabelText('What are you looking for?')
    expect(box).toHaveValue('')
    expect(box).toHaveAttribute('placeholder', 'e.g. jazz or folk concerts near Paris on weekends')
    expect(box).toHaveClass('placeholder:italic', 'placeholder:text-muted-foreground', 'font-medium', 'text-foreground', 'border')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Search again' })).toBeDisabled())
    expect(screen.queryByTestId('criteria-hint')).not.toBeInTheDocument()
    expect(screen.queryByTestId('utc-notice')).not.toBeInTheDocument()
    expect(screen.getByTestId('search-box')).not.toHaveTextContent(/Saved\.|UTC|click the text/)
    expect(localStorage.getItem('sail-event-criteria-hint-seen')).toBeNull()
  })

  it('Search is enabled as soon as the box has text, without saving first', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getCriteria').mockResolvedValue({ text: '', updatedAt: 'now', timeZone: 'UTC' })
    renderMainPage()
    const button = screen.getByRole('button', { name: /Search (now|again)/ })
    await waitFor(() => expect(button).toBeDisabled())
    fireEvent.change(screen.getByLabelText('What are you looking for?'), { target: { value: '   ' } })
    expect(button).toBeDisabled()
    fireEvent.change(screen.getByLabelText('What are you looking for?'), { target: { value: 'jazz' } })
    expect(button).toBeEnabled()
    expect(screen.getByTestId('search-box').tagName).toBe('FORM')
    expect(button).toHaveAttribute('type', 'submit')
  })

  it('shows Couldn\'t save and no run when the PUT fails', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'saveCriteria').mockRejectedValue(new Error('500'))
    const run = vi.spyOn(api, 'runSearch')
    renderMainPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Search again' }))
    expect(await screen.findByText("Couldn't save. Try again.")).toBeInTheDocument()
    expect(run).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Search again' })).toBeEnabled()
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
    expect(live).toHaveTextContent('Reading pages 7 / 20…')
    const tl = screen.getByTestId('run-chronology')
    expect(tl).toHaveTextContent('automatic run · running…')
    expect(tl).toHaveTextContent('Searched the web, 20 pages')
    expect(tl).not.toHaveTextContent('Judged')
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
  })

  it('while a run goes, the box stays editable and Enter saves for the next search without a POST', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getLastRun').mockResolvedValue({ run: running })
    const save = vi.spyOn(api, 'saveCriteria').mockImplementation(async (text) => ({ text, updatedAt: 'now', timeZone: 'Europe/Berlin' }))
    const run = vi.spyOn(api, 'runSearch')
    renderMainPage()
    await screen.findByTestId('search-progress')
    const box = screen.getByLabelText('What are you looking for?')
    expect(box).toBeEnabled()
    fireEvent.change(box, { target: { value: 'folk in Paris' } })
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(await screen.findByText('Saved for the next search')).toBeInTheDocument()
    expect(save).toHaveBeenCalledWith('folk in Paris', expect.any(String))
    expect(run).not.toHaveBeenCalled()
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


})


describe('Scoring auto-save (#157)', () => {
  async function setupScoring() {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getThresholds').mockResolvedValue({ lowerThreshold: 30, upperThreshold: 70 })
    const save = vi.spyOn(api, 'saveThresholds').mockImplementation(async (pair) => pair)
    const view = renderMainPage()
    const lower = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upper = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    await waitFor(() => expect(lower).toHaveValue(30))
    vi.useFakeTimers()
    return { ...view, lower, upper, save }
  }

  it('starts open with visible thresholds and no Save button', async () => {
    await setupScoring()
    expect(screen.getByTestId('scoring-card')).toHaveAttribute('open')
    expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument()
  })

  it('does not save the initial values', async () => {
    const { save } = await setupScoring()
    await act(() => vi.advanceTimersByTimeAsync(1000))
    expect(save).not.toHaveBeenCalled()
  })

  it('debounces number and slider edits for 600 ms, then briefly confirms Saved', async () => {
    const { lower, save } = await setupScoring()
    fireEvent.change(lower, { target: { value: '24' } })
    await act(() => vi.advanceTimersByTimeAsync(300))
    fireEvent.change(screen.getByRole('slider', { name: 'Auto-accept above' }), { target: { value: '72' } })
    await act(() => vi.advanceTimersByTimeAsync(599))
    expect(save).not.toHaveBeenCalled()
    await act(() => vi.advanceTimersByTimeAsync(1))
    expect(save).toHaveBeenCalledExactlyOnceWith({ lowerThreshold: 24, upperThreshold: 72 })
    expect(screen.getByText('Saved.')).toHaveAttribute('role', 'status')
    await act(() => vi.advanceTimersByTimeAsync(2000))
    expect(screen.queryByText('Saved.')).not.toBeInTheDocument()
  })

  it.each([[50, 50], [80, 50], [-1, 70], [30, 101]])('does not save invalid thresholds %s/%s', async (l, u) => {
    const { lower, upper, save } = await setupScoring()
    fireEvent.change(lower, { target: { value: String(l) } })
    fireEvent.change(upper, { target: { value: String(u) } })
    await act(() => vi.advanceTimersByTimeAsync(1000))
    expect(save).not.toHaveBeenCalled()
    expect(screen.getByText('The auto-accept line must be higher than the auto-reject line.')).toBeInTheDocument()
    expect(screen.queryByText('Saved.')).not.toBeInTheDocument()
  })

  it('cancels a pending save when an edit becomes invalid, then saves a corrected pair', async () => {
    const { lower, upper, save } = await setupScoring()
    fireEvent.change(lower, { target: { value: '24' } })
    await act(() => vi.advanceTimersByTimeAsync(300))
    fireEvent.change(upper, { target: { value: '24' } })
    await act(() => vi.advanceTimersByTimeAsync(1000))
    expect(save).not.toHaveBeenCalled()
    fireEvent.change(upper, { target: { value: '72' } })
    await act(() => vi.advanceTimersByTimeAsync(600))
    expect(save).toHaveBeenCalledExactlyOnceWith({ lowerThreshold: 24, upperThreshold: 72 })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('keeps later edits while a save is in flight and saves them in order', async () => {
    const { lower, upper, save } = await setupScoring()
    let finishSave!: (pair: { lowerThreshold: number; upperThreshold: number }) => void
    save.mockImplementationOnce(() => new Promise((resolve) => { finishSave = resolve }))
    fireEvent.change(lower, { target: { value: '24' } })
    await act(() => vi.advanceTimersByTimeAsync(600))
    expect(save).toHaveBeenCalledTimes(1)
    fireEvent.change(upper, { target: { value: '72' } })
    await act(() => vi.advanceTimersByTimeAsync(700))
    expect(save).toHaveBeenCalledTimes(1)
    await act(async () => finishSave({ lowerThreshold: 24, upperThreshold: 70 }))
    expect(upper).toHaveValue(72)
    expect(screen.queryByText('Saved.')).not.toBeInTheDocument()
    await act(() => vi.advanceTimersByTimeAsync(600))
    expect(save).toHaveBeenLastCalledWith({ lowerThreshold: 24, upperThreshold: 72 })
    expect(save).toHaveBeenCalledTimes(2)
    expect(screen.getByText('Saved.')).toBeInTheDocument()
  })

  it('shows save failures without retrying in a loop, and retries after a new edit', async () => {
    const { lower, save } = await setupScoring()
    save.mockRejectedValueOnce(new Error('offline'))
    fireEvent.change(lower, { target: { value: '24' } })
    await act(() => vi.advanceTimersByTimeAsync(600))
    expect(screen.getByText("Couldn't save. Try again.")).toBeInTheDocument()
    expect(screen.queryByText('Saved.')).not.toBeInTheDocument()
    await act(() => vi.advanceTimersByTimeAsync(3000))
    expect(save).toHaveBeenCalledTimes(1)
    fireEvent.change(lower, { target: { value: '25' } })
    await act(() => vi.advanceTimersByTimeAsync(600))
    expect(save).toHaveBeenLastCalledWith({ lowerThreshold: 25, upperThreshold: 70 })
    expect(screen.getByText('Saved.')).toBeInTheDocument()
    expect(screen.queryByText("Couldn't save. Try again.")).not.toBeInTheDocument()
  })

  it('cancels a pending save on unmount', async () => {
    const { lower, save, unmount } = await setupScoring()
    fireEvent.change(lower, { target: { value: '24' } })
    unmount()
    await act(() => vi.advanceTimersByTimeAsync(1000))
    expect(save).not.toHaveBeenCalled()
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
      'Screened out: 9',
      'Judged 22 · 2 in calendar, 1 to review, 19 rejected',
    ])
  })

  it('found = screened out + judged, and non-events are a separate line', () => {
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
      'Screened out: 1',
      'Judged 9 · 3 in calendar, 1 to review, 4 rejected, 1 not scored yet',
    ])
    const num = (re: RegExp) => Number(lines.join('\n').match(re)![1])
    expect(num(/found (\d+) events/)).toBe(num(/Screened out: (\d+)/) + num(/Judged (\d+)/))
    expect(num(/Judged (\d+)/)).toBe(num(/(\d+) in calendar/) + num(/(\d+) to review/) + num(/(\d+) rejected/) + num(/(\d+) not scored yet/))
  })

  // dev 2026-10-25 "Screened out: 307 (44 detail fetch errors)": a failed event-page fetch keeps the listing's
  // record and goes on to the screen; it is a page count of the event-page stage, not a screening reason
  it('reports failed event-page fetches on the event-page line only, out of every page it opened', () => {
    const counts = { ...finished.stageCounts, events_extracted: 329, filtered_no_time: 298, pages_detail_fetched: 229, detail_fetch_errors: 44 }
    const lines = stageLines({ ...finished, stageCounts: counts })
    expect(lines[2]).toBe('Opened 273 event pages, 44 failed')
    expect(lines[3]).toBe('Screened out: 307') // 4 already over + 2 wrong place + 3 duplicates + 298 no start time
    expect(lines.join('\n')).not.toMatch(/fetch error|detail/)
    // every page failed: the line still says so
    const allFailed = stageLines({ ...finished, stageCounts: { ...finished.stageCounts, detail_fetch_errors: 5 } })
    expect(allFailed[2]).toBe('Opened 5 event pages, 5 failed')
    expect(stageLines({ ...finished, stageCounts: { ...counts, detail_fetch_errors: 0 } })[2]).toBe('Opened 229 event pages')
  })

  it('says how many pages were already known from earlier runs', () => {
    const withKnown = stageLines({ ...finished, stageCounts: { ...finished.stageCounts, results_known: 6 } })
    expect(withKnown[0]).toBe('Searched the web: 20 pages, 6 already known from earlier runs, 14 new')
    expect(withKnown[1]).toBe('Read 14 pages, found 31 events')
    expect(stageLines({ ...finished, stageCounts: { ...finished.stageCounts, results_known: 0 } })[0]).toBe('Searched the web, 20 pages')
  })

  it('the reading total is fetched minus known: 17 fetched, 1 known → of 16', () => {
    const counts = { ...finished.stageCounts, results_fetched: 17, results_known: 1, pages_content_pass: 9 }
    expect(stageText({ ...finished, currentStage: 'extract', finishedAt: null, stageCounts: counts })).toBe('Reading pages 9 / 16…')
    const lines = stageLines({ ...finished, stageCounts: counts })
    expect(lines[0]).toBe('Searched the web: 17 pages, 1 already known from earlier runs, 16 new')
    expect(lines[1]).toBe('Read 16 pages, found 31 events')
  })

  it('shows the finished stages then the live line while judging (from events_to_judge, not eventsNew)', () => {
    expect(stageLines({ ...finished, eventsNew: 0, currentStage: 'judge', finishedAt: null, stageCounts: { ...finished.stageCounts, events_to_judge: 10, events_judged: 3 } })).toEqual([
      'Searched the web, 20 pages',
      'Read 20 pages, found 31 events',
      'Screened out: 9',
      'Judging events 3 / 10…',
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
    expect(stageText({ ...finished, currentStage: 'extract', finishedAt: null, stageCounts: { results_fetched: 20, pages_content_pass: 7 } })).toBe('Reading pages 7 / 20…')
  })

  // dev 2026-10-25: the event-page stage showed "Working…" for minutes
  it('shows opening event pages done / total for the detail_hop stage', () => {
    const hop = { ...finished, currentStage: 'detail_hop', finishedAt: null }
    expect(stageText({ ...hop, stageCounts: { detail_pages_done: 87, detail_pages_to_open: 236 } })).toBe('Opening event pages 87 / 236…')
    expect(stageText({ ...hop, stageCounts: { results_fetched: 20 } })).toBe('Opening event pages…')
    expect(stageLines({ ...hop, stageCounts: { ...finished.stageCounts, detail_pages_done: 0, detail_pages_to_open: 5 } })).toEqual([
      'Searched the web, 20 pages',
      'Read 20 pages, found 31 events',
      'Opening event pages 0 / 5…',
    ])
  })

  it('shows done summary when finished', () => {
    expect(stageText(finished)).toBe('Done: 2 added to your calendar, 1 to review, 19 rejected')
  })
})

describe('stageFraction', () => {
  it('returns done/total for extract (uses fetched - known)', () => {
    expect(stageFraction({ ...finished, currentStage: 'extract', finishedAt: null, stageCounts: { results_fetched: 20, pages_content_pass: 7 } })).toBeCloseTo(7 / 20)
    expect(stageFraction({ ...finished, currentStage: 'extract', finishedAt: null, stageCounts: { results_fetched: 17, results_known: 1, pages_content_pass: 8 } })).toBeCloseTo(8 / 16)
  })

  it('returns done/total for judge from events_to_judge in stageCounts', () => {
    expect(stageFraction({ ...finished, currentStage: 'judge', finishedAt: null, stageCounts: { events_to_judge: 10, events_judged: 3 } })).toBeCloseTo(3 / 10)
    // falls back to eventsNew when the key is absent (finalised run)
    expect(stageFraction({ ...finished, currentStage: 'judge', finishedAt: null, eventsNew: 10, stageCounts: { events_judged: 3 } })).toBeCloseTo(3 / 10)
  })

  it('returns done/total for detail_hop, the same numbers as its text', () => {
    expect(stageFraction({ ...finished, currentStage: 'detail_hop', finishedAt: null, stageCounts: { detail_pages_done: 87, detail_pages_to_open: 236 } })).toBeCloseTo(87 / 236)
    expect(stageFraction({ ...finished, currentStage: 'detail_hop', finishedAt: null, stageCounts: {} })).toBeNull()
  })

  it('returns null when the total is unknown', () => {
    expect(stageFraction({ ...finished, currentStage: 'search', finishedAt: null })).toBeNull()
    expect(stageFraction({ ...finished, currentStage: 'filter', finishedAt: null })).toBeNull()
    expect(stageFraction({ ...finished, currentStage: 'adapters', finishedAt: null, stageCounts: null })).toBeNull()
  })
})

describe('progress hairline', () => {
  const extractRun: SearchResult = {
    runId: 'run-live', eventsFound: 0, eventsNew: 0,
    stageCounts: { results_fetched: 20, pages_content_pass: 7 },
    currentStage: 'extract', stoppedAtStage: null, error: null,
    startedAt: '2026-10-18T10:00:00+00:00', finishedAt: null, trigger: 'manual',
  }

  it('shows the hairline with fill width matching the fraction during extract', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getLastRun').mockResolvedValue({ run: extractRun })
    renderMainPage()
    const hairline = await screen.findByTestId('progress-hairline')
    expect(hairline).toBeInTheDocument()
    expect(hairline.classList.contains('progress-hairline')).toBe(true)
    const fill = hairline.querySelector('.progress-hairline-fill')!
    expect(fill).toBeTruthy()
    expect(fill.getAttribute('style')).toContain('width: 35%')
  })

  it('shows the dot alone when the total is unknown (search stage)', async () => {
    const api = await import('@/services/api')
    vi.spyOn(api, 'getLastRun').mockResolvedValue({
      run: { ...extractRun, currentStage: 'search', stageCounts: { queries_planned: 2 } },
    })
    renderMainPage()
    const hairline = await screen.findByTestId('progress-hairline')
    expect(hairline.classList.contains('progress-hairline-dot')).toBe(true)
    expect(hairline.querySelector('.progress-hairline-fill')).toBeNull()
  })

  it('is removed when the stage is done', async () => {
    renderMainPage()
    await waitFor(() => expect(screen.getByTestId('run-chronology')).toBeInTheDocument())
    expect(screen.queryByTestId('progress-hairline')).not.toBeInTheDocument()
  })

  it('adds progress-no-motion when prefers-reduced-motion matches', async () => {
    const listeners: ((e: MediaQueryListEvent) => void)[] = []
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: true,
      media: '(prefers-reduced-motion: reduce)',
      addEventListener: (_: string, cb: (e: MediaQueryListEvent) => void) => listeners.push(cb),
      removeEventListener: () => {},
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })
    const api = await import('@/services/api')
    vi.spyOn(api, 'getLastRun').mockResolvedValue({ run: extractRun })
    renderMainPage()
    const hairline = await screen.findByTestId('progress-hairline')
    expect(hairline.classList.contains('progress-no-motion')).toBe(true)
  })
})
