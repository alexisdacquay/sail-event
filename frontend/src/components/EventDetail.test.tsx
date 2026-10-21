import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EventDetail } from './EventDetail'
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
  sourceUrl: 'https://www.example.com/events/conf',
  band: 'mostly fits',
  score: 85,
  scoreReason: 'Strong match: test event.',
  status: 'queued',
  decidedBy: null,
}

const onDecide = vi.fn(async () => {})

describe('EventDetail', () => {
  it('renders title, score, bar, reason and source link', () => {
    render(<EventDetail event={event} onDecide={onDecide} onClose={() => {}} />)
    expect(screen.getByText('Test Conference 2026')).toBeInTheDocument()
    expect(screen.getByText('Score 85%')).toBeInTheDocument()
    expect(screen.getByText('Strong match: test event.')).toBeInTheDocument()
    const bar = screen.getByTestId('event-detail').querySelector('.bg-zone-calendar') as HTMLElement
    expect(bar.style.width).toBe('85%')
    const source = screen.getByRole('link', { name: /Source · example.com\/events\/conf/ })
    expect(source).toHaveAttribute('href', 'https://www.example.com/events/conf')
  })

  it('queued shows Add to calendar and Reject', () => {
    render(<EventDetail event={event} onDecide={onDecide} onClose={() => {}} />)
    expect(screen.getByRole('button', { name: 'Add to calendar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('accepted shows Remove from calendar', () => {
    render(<EventDetail event={{ ...event, status: 'accepted' }} onDecide={onDecide} onClose={() => {}} />)
    expect(screen.getByRole('button', { name: 'Remove from calendar' })).toBeInTheDocument()
  })

  it('rejected shows Add to calendar only', () => {
    render(<EventDetail event={{ ...event, status: 'rejected' }} onDecide={onDecide} onClose={() => {}} />)
    expect(screen.getByRole('button', { name: 'Add to calendar' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Reject' })).not.toBeInTheDocument()
  })

  it('Close calls onClose', () => {
    const onClose = vi.fn()
    render(<EventDetail event={event} onDecide={onDecide} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(onClose).toHaveBeenCalled()
  })

  it('shows an alert when deciding fails', async () => {
    const failing = vi.fn(async () => { throw new Error('x') })
    render(<EventDetail event={event} onDecide={failing} onClose={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: 'Reject' }))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
