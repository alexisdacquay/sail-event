import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EventRow, formatDay, formatTime, formatWhere } from './EventCard'
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

const tokyoEvent: Event = {
  ...event,
  id: 'evt-tokyo',
  title: 'Tokyo Jazz Night',
  dateTime: '2026-10-20T20:00:00+09:00',
  startTz: 'Asia/Tokyo',
  city: 'Tokyo',
  country: 'JP',
}

describe('formatWhere', () => {
  it('renders venue, city, country', () => {
    expect(formatWhere(event)).toBe('QEII Centre, London, GB')
  })

  it('does not repeat the country when place already ends with it', () => {
    expect(formatWhere({ ...event, place: 'YSY Bar, Berlin, DE', city: 'Berlin', country: 'DE' })).toBe('YSY Bar, Berlin, DE')
  })

  it('renders place unknown for ZZ country', () => {
    expect(formatWhere({ ...event, country: 'ZZ', city: '', place: '' })).toBe('place unknown')
  })
})

describe('formatTime / formatDay', () => {
  it('no time for a date-only event', () => {
    expect(formatTime({ ...event, dateTime: '2026-10-20', startTz: null })).toBe('no time')
  })

  it('day is weekday day month', () => {
    expect(formatDay({ ...event, dateTime: '2026-10-20', startTz: null })).toBe('Tue 20 Oct')
    expect(formatDay(tokyoEvent)).toBe('Tue 20 Oct')
  })

  it('time carries a short zone name only when the zone differs from the viewer', () => {
    expect(formatTime(tokyoEvent, 'Europe/Berlin')).toBe('20:00 GMT+9')
    expect(formatTime(tokyoEvent, 'Asia/Tokyo')).toBe('20:00')
    // an abbreviation where one exists
    expect(formatTime(event, 'Europe/Berlin')).toBe('10:00 BST')
    expect(formatTime(event, 'Europe/London')).toBe('10:00')
  })

  it('no zone when startTz is null', () => {
    expect(formatTime({ ...event, startTz: null }, 'Europe/Berlin')).toMatch(/^\d\d:\d\d$/)
  })
})

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

  it('shows no time for a date-only event', () => {
    render(<EventRow event={{ ...event, dateTime: '2026-10-20', startTz: null }} selected={false} onSelect={() => {}} />)
    expect(screen.getByTestId('row-time')).toHaveTextContent('no time')
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
    ['queued', 'Review'],
    ['rejected', 'Out'],
    ['new', 'New'],
  ] as const)('status pill for %s reads %s', (status, text) => {
    render(<EventRow event={{ ...event, status }} selected={false} onSelect={() => {}} />)
    expect(screen.getByTestId('row-status')).toHaveTextContent(text)
  })
})
