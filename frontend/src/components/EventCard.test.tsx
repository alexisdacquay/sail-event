import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
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
  it('renders all listed fields', () => {
    render(<EventCard event={event} />)

    expect(screen.getByText('Test Conference 2026')).toBeInTheDocument()
    expect(screen.getByText('QEII Centre, London')).toBeInTheDocument()
    expect(screen.getByText('https://example.com/conf')).toBeInTheDocument()
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('Strong match: test event.')).toBeInTheDocument()
    expect(screen.getByText('queued')).toBeInTheDocument()
    // date/time is formatted by Intl.DateTimeFormat — check the element exists
    expect(screen.getByTestId('event-datetime')).toBeInTheDocument()
  })

  it('link is clickable', () => {
    render(<EventCard event={event} />)
    const link = screen.getByRole('link', { name: 'https://example.com/conf' })
    expect(link).toHaveAttribute('href', 'https://example.com/conf')
  })
})
