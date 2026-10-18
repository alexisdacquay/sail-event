import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EventCard } from './EventCard'
import type { Event } from '@/services/api'

const event: Event = {
  id: 'evt-test',
  title: 'Test Conference 2026',
  dateTime: '2026-09-18T09:00:00Z',
  place: 'QEII Centre, London',
  link: 'https://example.com/conf',
  description: 'A test event description.',
  score: 85,
  scoreReason: 'Strong match: test event.',
  status: 'queued',
}

describe('EventCard', () => {
  it('renders fields in queue variant', () => {
    render(<EventCard event={event} variant="queue" />)

    expect(screen.getByText('Test Conference 2026')).toBeInTheDocument()
    expect(screen.getByText('QEII Centre, London')).toBeInTheDocument()
    expect(screen.getByText('https://example.com/conf')).toBeInTheDocument()
    expect(screen.getByText(/85 \/ 100/)).toBeInTheDocument()
    expect(screen.getByText(/Strong match: test event\./)).toBeInTheDocument()
    expect(screen.getByTestId('event-datetime')).toBeInTheDocument()
  })

  it('queue variant renders Why before the title in DOM order', () => {
    const { container } = render(
      <EventCard event={event} variant="queue" />,
    )
    const header = container.querySelector('[data-slot="card-header"]')!
    const texts = header.textContent!
    const whyPos = texts.indexOf('Why:')
    const titlePos = texts.indexOf('Test Conference 2026')
    expect(whyPos).toBeLessThan(titlePos)
  })

  it('all variant shows Waiting for you badge for queued', () => {
    render(<EventCard event={event} variant="all" />)
    expect(screen.getByText('Waiting for you')).toBeInTheDocument()
  })

  it('all variant shows On your calendar badge for accepted', () => {
    const accepted = { ...event, status: 'accepted' as const }
    render(<EventCard event={accepted} variant="all" />)
    expect(screen.getByText('On your calendar')).toBeInTheDocument()
  })

  it('all variant shows Rejected badge', () => {
    const rejected = { ...event, status: 'rejected' as const }
    render(<EventCard event={rejected} variant="all" />)
    expect(screen.getByText('Rejected')).toBeInTheDocument()
  })

  it('all variant shows Remove from calendar for accepted events', () => {
    const accepted = { ...event, status: 'accepted' as const }
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
    const accepted = { ...event, status: 'accepted' as const }
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
})
