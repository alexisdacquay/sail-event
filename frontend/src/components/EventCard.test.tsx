import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EventCard, EventRow, formatDay, formatTime, formatWhen } from './EventCard'
import type { Event } from '@/services/api'

const event: Event = {
  id: 'evt-test',
  title: 'Test Conference 2026',
  dateTime: '2026-09-18T09:00:00Z',
  place: 'QEII Centre',
  link: 'https://example.com/conf',
  description: 'A test event description.',
  startTz: 'Europe/London',
  endTime: null,
  city: 'London',
  country: 'GB',
  sourceUrl: 'https://example.com/conf',
  band: 'mostly fits',
  score: 85,
  scoreReason: 'Strong match: test event.',
  status: 'queued',
  decidedBy: null,
}

describe('EventCard', () => {
  it('renders title, info line, and Details toggle', () => {
    render(<EventCard event={event} variant="queue" />)

    expect(screen.getByText('Test Conference 2026')).toBeInTheDocument()
    expect(screen.getByTestId('event-info-line')).toBeInTheDocument()
    expect(screen.getByText(/Score: 85%/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Details/ })).toBeInTheDocument()
  })

  it('does not render band word', () => {
    render(<EventCard event={event} variant="queue" />)
    expect(screen.queryByText(/mostly fits/)).not.toBeInTheDocument()
  })

  it('does not render status badges', () => {
    const accepted = { ...event, status: 'accepted' as const, decidedBy: 'user' as const }
    render(<EventCard event={accepted} variant="all" />)
    expect(screen.queryByText('Accepted by you')).not.toBeInTheDocument()
    expect(screen.queryByText('Auto-accepted')).not.toBeInTheDocument()
  })

  it('info line shows when, where, and score', () => {
    render(<EventCard event={event} variant="queue" />)
    const line = screen.getByTestId('event-info-line').textContent!
    expect(line).toContain('QEII Centre')
    expect(line).toContain('Score: 85%')
    // date part present
    expect(line).toMatch(/\w{3} \d{1,2} \w{3}/)
  })

  it('renders where as venue, city, country', () => {
    render(<EventCard event={event} variant="queue" />)
    const line = screen.getByTestId('event-info-line').textContent!
    expect(line).toContain('QEII Centre, London, GB')
  })

  it('does not repeat the country when place already ends with it', () => {
    const full = { ...event, place: 'YSY Bar, Berlin, DE', city: 'Berlin', country: 'DE' }
    render(<EventCard event={full} variant="queue" />)
    const line = screen.getByTestId('event-info-line').textContent!
    expect(line).toContain('YSY Bar, Berlin, DE')
    // country not duplicated
    expect(line).not.toMatch(/DE.*DE/)
  })

  it('renders place unknown for ZZ country', () => {
    const zz = { ...event, country: 'ZZ', city: '', place: '' }
    render(<EventCard event={zz} variant="queue" />)
    const line = screen.getByTestId('event-info-line').textContent!
    expect(line).toContain('place unknown')
  })

  it('renders date only when no T in dateTime', () => {
    const dateOnly = { ...event, dateTime: '2026-10-20', startTz: null }
    render(<EventCard event={dateOnly} variant="queue" />)
    const line = screen.getByTestId('event-info-line').textContent!
    expect(line).toMatch(/Tue 20 Oct/)
    expect(line).not.toMatch(/\d{2}:\d{2}/)
  })

  it('shows no tz suffix when startTz is null', () => {
    const noTz = { ...event, startTz: null }
    render(<EventCard event={noTz} variant="queue" />)
    const line = screen.getByTestId('event-info-line').textContent!
    // no parenthesised timezone
    expect(line).not.toMatch(/\(.*\/.*\)/)
    expect(line).not.toContain('(local time)')
  })

  it('title links to event page', () => {
    render(<EventCard event={event} variant="queue" />)
    const link = screen.getByRole('link', { name: 'Test Conference 2026' })
    expect(link).toHaveAttribute('href', 'https://example.com/conf')
  })

  // --- Action buttons ---

  it('queued shows Add to calendar and Reject buttons', () => {
    const onDecide = vi.fn()
    render(<EventCard event={event} variant="queue" onDecide={onDecide} />)
    expect(screen.getByRole('button', { name: 'Add to calendar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('accepted shows Remove from calendar', () => {
    const accepted = { ...event, status: 'accepted' as const, decidedBy: 'auto' as const }
    const onDecide = vi.fn()
    render(<EventCard event={accepted} variant="all" onDecide={onDecide} />)
    expect(screen.getByRole('button', { name: 'Remove from calendar' })).toBeInTheDocument()
  })

  it('rejected shows Add to calendar', () => {
    const rejected = { ...event, status: 'rejected' as const, decidedBy: 'auto' as const }
    const onDecide = vi.fn()
    render(<EventCard event={rejected} variant="all" onDecide={onDecide} />)
    expect(screen.getByRole('button', { name: 'Add to calendar' })).toBeInTheDocument()
  })

  it('hides Remove from calendar for non-accepted events', () => {
    const onDecide = vi.fn()
    render(<EventCard event={event} variant="all" onDecide={onDecide} />)
    expect(
      screen.queryByRole('button', { name: 'Remove from calendar' }),
    ).not.toBeInTheDocument()
  })

  it('Remove from calendar shows confirm prompt', () => {
    const accepted = { ...event, status: 'accepted' as const, decidedBy: 'auto' as const }
    const onDecide = vi.fn()
    render(<EventCard event={accepted} variant="all" onDecide={onDecide} />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Remove from calendar' }),
    )
    expect(
      screen.getByText('Remove this event from your calendar?'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Remove' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Cancel' }),
    ).toBeInTheDocument()
  })

  it('Add to calendar and Reject disable both buttons while deciding', async () => {
    const onDecide = vi.fn(
      () => new Promise<void>(() => {}), // never resolves
    )
    render(<EventCard event={event} variant="queue" onDecide={onDecide} />)

    fireEvent.click(screen.getByRole('button', { name: 'Add to calendar' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Adding…' })).toBeDisabled()
      expect(screen.getByRole('button', { name: 'Reject' })).toBeDisabled()
    })
  })

  // --- Details toggle ---

  it('Details closed by default for accepted event', () => {
    const accepted = { ...event, status: 'accepted' as const, decidedBy: 'auto' as const }
    render(<EventCard event={accepted} variant="all" />)
    expect(screen.queryByText('Strong match: test event.')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Details/ })).toHaveAttribute('aria-expanded', 'false')
  })

  it('Details closed by default for queued event', () => {
    render(<EventCard event={event} variant="queue" />)
    expect(screen.queryByText('Strong match: test event.')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Details/ })).toHaveAttribute('aria-expanded', 'false')
  })

  it('Details open by default for rejected event', () => {
    const rejected = { ...event, status: 'rejected' as const, decidedBy: 'auto' as const }
    render(<EventCard event={rejected} variant="all" />)
    expect(screen.getByText('Strong match: test event.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Details/ })).toHaveAttribute('aria-expanded', 'true')
  })

  it('Details toggles on click', () => {
    render(<EventCard event={event} variant="queue" />)
    const toggle = screen.getByRole('button', { name: /Details/ })

    // Initially closed
    expect(screen.queryByText('Strong match: test event.')).not.toBeInTheDocument()

    // Open
    fireEvent.click(toggle)
    expect(screen.getByText('Strong match: test event.')).toBeInTheDocument()

    // Close
    fireEvent.click(toggle)
    expect(screen.queryByText('Strong match: test event.')).not.toBeInTheDocument()
  })

  it('Details toggle is a button element', () => {
    render(<EventCard event={event} variant="queue" />)
    const toggle = screen.getByRole('button', { name: /Details/ })
    expect(toggle.tagName).toBe('BUTTON')
  })
})

// --- formatWhen: tz suffix only when event zone ≠ viewer zone ---

const tokyoEvent: Event = {
  ...event,
  id: 'evt-tokyo',
  title: 'Tokyo Jazz Night',
  dateTime: '2026-10-20T20:00:00+09:00',
  startTz: 'Asia/Tokyo',
  city: 'Tokyo',
  country: 'JP',
}

describe('formatWhen — tz suffix', () => {
  it('shows tz suffix when event zone differs from viewer zone', () => {
    const text = formatWhen(tokyoEvent, 'Europe/Berlin')
    expect(text).toContain('20:00')
    expect(text).toContain('(Asia/Tokyo)')
    expect(text).toMatch(/Tue 20 Oct/)
  })

  it('no tz suffix when event zone matches viewer zone', () => {
    const text = formatWhen(tokyoEvent, 'Asia/Tokyo')
    expect(text).toContain('20:00')
    expect(text).not.toContain('(')
    expect(text).toMatch(/Tue 20 Oct/)
  })

  it('no viewer-zone time annotation (only event-zone time shown)', () => {
    const text = formatWhen(tokyoEvent, 'Europe/Berlin')
    // Only event tz, no Berlin time
    expect(text).not.toContain('13:00')
    expect(text).not.toContain('Europe/Berlin')
  })

  it('date-only event shows correct date from any timezone', () => {
    const dateOnly: Event = { ...event, dateTime: '2026-10-20', startTz: null }
    const text = formatWhen(dateOnly, 'America/New_York')
    expect(text).toMatch(/Tue 20 Oct/)
    expect(text).not.toMatch(/\d{2}:\d{2}/)
  })

  it('no tz suffix when startTz is null', () => {
    const noTz: Event = { ...event, startTz: null }
    const text = formatWhen(noTz, 'Europe/Berlin')
    expect(text).not.toContain('(')
  })
})

// --- EventRow ---

describe('EventRow', () => {
  it('renders the five columns and the title link', () => {
    render(<EventRow event={event} selected={false} onSelect={() => {}} />)
    for (const id of ['row-time', 'row-place', 'row-score', 'row-status']) {
      expect(screen.getByTestId(id)).toBeInTheDocument()
    }
    expect(screen.getByRole('link', { name: 'Test Conference 2026' })).toHaveAttribute(
      'href',
      'https://example.com/conf',
    )
    expect(screen.getByTestId('row-score')).toHaveTextContent('85%')
  })

  it('shows time unknown for a date-only event', () => {
    render(<EventRow event={{ ...event, dateTime: '2026-10-20', startTz: null }} selected={false} onSelect={() => {}} />)
    expect(screen.getByTestId('row-time')).toHaveTextContent('time unknown')
  })

  it('Enter calls onSelect with the id', () => {
    const onSelect = vi.fn()
    render(<EventRow event={event} selected={false} onSelect={onSelect} />)
    fireEvent.keyDown(screen.getByTestId('event-row-evt-test'), { key: 'Enter' })
    expect(onSelect).toHaveBeenCalledWith('evt-test')
  })

  it('aria-pressed reflects selection', () => {
    render(<EventRow event={event} selected onSelect={() => {}} />)
    expect(screen.getByTestId('event-row-evt-test')).toHaveAttribute('aria-pressed', 'true')
  })

  it.each([
    ['accepted', 'In calendar'],
    ['queued', 'To review'],
    ['rejected', 'Rejected'],
    ['new', 'New'],
  ] as const)('status pill for %s reads %s', (status, text) => {
    render(<EventRow event={{ ...event, status }} selected={false} onSelect={() => {}} />)
    expect(screen.getByTestId('row-status')).toHaveTextContent(text)
  })
})

describe('formatTime / formatDay', () => {
  it('time unknown for a date-only event', () => {
    expect(formatTime({ ...event, dateTime: '2026-10-20', startTz: null })).toBe('time unknown')
  })

  it('day is weekday day month', () => {
    expect(formatDay({ ...event, dateTime: '2026-10-20', startTz: null })).toBe('Tue 20 Oct')
    expect(formatDay(tokyoEvent)).toBe('Tue 20 Oct')
  })

  it('time carries the zone only when it differs from the viewer', () => {
    expect(formatTime(tokyoEvent, 'Europe/Berlin')).toBe('20:00 (Asia/Tokyo)')
    expect(formatTime(tokyoEvent, 'Asia/Tokyo')).toBe('20:00')
  })
})
