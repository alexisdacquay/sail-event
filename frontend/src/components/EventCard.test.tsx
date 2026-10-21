import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EventCard, formatWhen, getBrowserTz } from './EventCard'
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
  it('renders fields in queue variant', () => {
    render(<EventCard event={event} variant="queue" />)

    expect(screen.getByText('Test Conference 2026')).toBeInTheDocument()
    expect(screen.getByText(/QEII Centre/)).toBeInTheDocument()
    expect(screen.getByText('https://example.com/conf')).toBeInTheDocument()
    expect(screen.getByText(/Score 85%/)).toBeInTheDocument()
    expect(screen.getByText(/mostly fits/)).toBeInTheDocument()
    expect(screen.getByText(/Strong match: test event\./)).toBeInTheDocument()
    expect(screen.getByTestId('event-datetime')).toBeInTheDocument()
  })

  it('renders score with band word', () => {
    render(<EventCard event={event} variant="queue" />)
    const scoreEl = screen.getByText(/Score 85%/)
    // The band word appears as a sibling span in the same <p>
    expect(scoreEl.closest('p')!.textContent).toContain('· mostly fits')
  })

  it('renders where as venue, city, country', () => {
    render(<EventCard event={event} variant="queue" />)
    expect(screen.getByText('QEII Centre, London, GB')).toBeInTheDocument()
  })

  it('does not repeat the country when place already ends with it', () => {
    const full = { ...event, place: 'YSY Bar, Berlin, DE', city: 'Berlin', country: 'DE' }
    render(<EventCard event={full} variant="queue" />)
    expect(screen.getByText('YSY Bar, Berlin, DE')).toBeInTheDocument()
  })

  it('renders place unknown for ZZ country', () => {
    const zz = { ...event, country: 'ZZ', city: '', place: '' }
    render(<EventCard event={zz} variant="queue" />)
    expect(screen.getByText('place unknown')).toBeInTheDocument()
  })

  it('renders date only with all day label', () => {
    const dateOnly = { ...event, dateTime: '2026-10-20', startTz: null }
    render(<EventCard event={dateOnly} variant="queue" />)
    const dt = screen.getByTestId('event-datetime')
    expect(dt.textContent).toMatch(/Oct 2026/)
    expect(dt.textContent).toContain('all day')
    expect(dt.textContent).not.toMatch(/\d{2}:\d{2}/)
  })

  it('shows local time label when startTz is null', () => {
    const noTz = { ...event, startTz: null }
    render(<EventCard event={noTz} variant="queue" />)
    const dt = screen.getByTestId('event-datetime')
    expect(dt.textContent).toContain('(local time)')
  })

  it('queue variant renders reason before the title in DOM order', () => {
    const { container } = render(
      <EventCard event={event} variant="queue" />,
    )
    const header = container.querySelector('[data-slot="card-header"]')!
    const texts = header.textContent!
    const reasonPos = texts.indexOf('Strong match')
    const titlePos = texts.indexOf('Test Conference 2026')
    expect(reasonPos).toBeLessThan(titlePos)
  })

  it('all variant shows To review badge for queued', () => {
    render(<EventCard event={event} variant="all" />)
    expect(screen.getByText('To review')).toBeInTheDocument()
  })

  it('all variant shows Auto-accepted badge for auto-accepted', () => {
    const accepted = { ...event, status: 'accepted' as const, decidedBy: 'auto' as const }
    render(<EventCard event={accepted} variant="all" />)
    expect(screen.getByText('Auto-accepted')).toBeInTheDocument()
  })

  it('all variant shows Accepted by you badge for user-accepted', () => {
    const accepted = { ...event, status: 'accepted' as const, decidedBy: 'user' as const }
    render(<EventCard event={accepted} variant="all" />)
    expect(screen.getByText('Accepted by you')).toBeInTheDocument()
  })

  it('all variant shows Auto-rejected badge for auto-rejected', () => {
    const rejected = { ...event, status: 'rejected' as const, decidedBy: 'auto' as const }
    render(<EventCard event={rejected} variant="all" />)
    expect(screen.getByText('Auto-rejected')).toBeInTheDocument()
  })

  it('all variant shows Rejected by you badge for user-rejected', () => {
    const rejected = { ...event, status: 'rejected' as const, decidedBy: 'user' as const }
    render(<EventCard event={rejected} variant="all" />)
    expect(screen.getByText('Rejected by you')).toBeInTheDocument()
  })

  it('all variant shows Remove from calendar for accepted events', () => {
    const accepted = { ...event, status: 'accepted' as const, decidedBy: 'auto' as const }
    const onDecide = vi.fn()
    render(<EventCard event={accepted} variant="all" onDecide={onDecide} />)
    expect(
      screen.getByRole('button', { name: 'Remove from calendar' }),
    ).toBeInTheDocument()
  })

  it('all variant hides Remove from calendar for non-accepted events', () => {
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

  it('link is clickable', () => {
    render(<EventCard event={event} variant="queue" />)
    const link = screen.getByRole('link', { name: 'https://example.com/conf' })
    expect(link).toHaveAttribute('href', 'https://example.com/conf')
  })

  it('card title is a clickable link to the event', () => {
    render(<EventCard event={event} variant="queue" />)
    const titleLink = screen.getByRole('link', { name: 'Test Conference 2026' })
    expect(titleLink).toHaveAttribute('href', 'https://example.com/conf')
  })

  it('Accept and Reject disable both buttons while deciding', async () => {
    const onDecide = vi.fn(
      () => new Promise<void>(() => {}), // never resolves
    )
    render(<EventCard event={event} variant="queue" onDecide={onDecide} />)

    fireEvent.click(screen.getByRole('button', { name: 'Accept' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Accepting…' })).toBeDisabled()
      expect(screen.getByRole('button', { name: 'Reject' })).toBeDisabled()
    })
  })

  it('queue variant shows 5-second undo bar after accept', async () => {
    const onDecide = vi.fn().mockResolvedValue(undefined)
    render(<EventCard event={event} variant="queue" onDecide={onDecide} />)

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Accept' }))
    })

    await waitFor(() => {
      expect(screen.getByTestId('undo-bar')).toBeInTheDocument()
      expect(screen.getByText('Accepted.')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Undo' })).toBeInTheDocument()
    })
  })

  it('all variant shows Put back to review for rejected events', () => {
    const rejected = { ...event, status: 'rejected' as const, decidedBy: 'auto' as const }
    const onDecide = vi.fn()
    render(<EventCard event={rejected} variant="all" onDecide={onDecide} />)
    expect(
      screen.getByRole('button', { name: 'Put back to review' }),
    ).toBeInTheDocument()
  })

  it('queue variant does not show Why: label', () => {
    render(<EventCard event={event} variant="queue" />)
    expect(screen.queryByText('Why:')).not.toBeInTheDocument()
  })

  it('datetime includes timezone', () => {
    render(<EventCard event={event} variant="queue" />)
    const dt = screen.getByTestId('event-datetime')
    // Should contain the event tz in parentheses
    expect(dt.textContent).toMatch(/\(Europe\/London\)/)
  })
})

// --- #71: event times carry their offset end to end ---

const tokyoEvent: Event = {
  ...event,
  id: 'evt-tokyo',
  title: 'Tokyo Jazz Night',
  dateTime: '2026-10-20T20:00:00+09:00',
  startTz: 'Asia/Tokyo',
  city: 'Tokyo',
  country: 'JP',
}

describe('formatWhen — offset-aware (#71)', () => {
  it('Tokyo event shows 20:00 (Asia/Tokyo) regardless of browser zone', () => {
    const text = formatWhen(tokyoEvent, 'Europe/Berlin')
    expect(text).toContain('20:00')
    expect(text).toContain('(Asia/Tokyo)')
    expect(text).toMatch(/Tue 20 Oct 2026/)
  })

  it('Tokyo event viewed from Europe/Berlin shows viewer annotation', () => {
    const text = formatWhen(tokyoEvent, 'Europe/Berlin')
    expect(text).toContain('(Asia/Tokyo)')
    expect(text).toContain('13:00')  // 20:00 JST = 13:00 CEST
    expect(text).toContain('your time:')
    expect(text).toContain('(Europe/Berlin)')
  })

  it('Tokyo event viewed from America/New_York shows NY annotation', () => {
    const text = formatWhen(tokyoEvent, 'America/New_York')
    expect(text).toContain('(Asia/Tokyo)')
    expect(text).toContain('07:00')  // 20:00 JST = 07:00 EDT
    expect(text).toContain('your time:')
    expect(text).toContain('(America/New_York)')
  })

  it('date-only event shows all day', () => {
    const dateOnly: Event = { ...event, dateTime: '2026-10-20', startTz: null }
    const text = formatWhen(dateOnly, 'America/New_York')
    expect(text).toMatch(/Tue 20 Oct 2026/)
    expect(text).toContain('all day')
    expect(text).not.toMatch(/\d{2}:\d{2}/)
  })

  it('viewer timezone hidden when same as event timezone', () => {
    const berlinEvent: Event = { ...event, dateTime: '2026-10-20T20:00:00+02:00', startTz: 'Europe/Berlin' }
    const text = formatWhen(berlinEvent, 'Europe/Berlin')
    expect(text).toContain('(Europe/Berlin)')
    // Should not contain "your time:" since zones match
    expect(text).not.toContain('your time:')
    // Only one occurrence of Europe/Berlin
    const matches = text.match(/Europe\/Berlin/g)
    expect(matches).toHaveLength(1)
  })

  it('shows time unknown for empty dateTime', () => {
    const noDate: Event = { ...event, dateTime: '' }
    const text = formatWhen(noDate)
    expect(text).toBe('time unknown')
  })
})
