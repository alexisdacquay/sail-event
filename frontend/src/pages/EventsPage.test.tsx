import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { EventsPage } from './EventsPage'

describe('EventsPage', () => {
  it('shows events of all statuses', async () => {
    render(<EventsPage />)

    // Wait for the mock data to load — check for at least one event title
    await screen.findByText('React London Meetup')

    // accepted
    expect(screen.getByText('React London Meetup')).toBeInTheDocument()
    // queued
    expect(screen.getByText('Jazz in the Park')).toBeInTheDocument()
    expect(screen.getByText('AWS re:Invent Watch Party')).toBeInTheDocument()
    // rejected
    expect(screen.getByText('Pottery Workshop for Beginners')).toBeInTheDocument()
    // new
    expect(screen.getByText('TypeScript Conference 2026')).toBeInTheDocument()

    // Verify all four status badges are present
    expect(screen.getByText('accepted')).toBeInTheDocument()
    expect(screen.getByText('rejected')).toBeInTheDocument()
    expect(screen.getByText('new')).toBeInTheDocument()
    // "queued" appears on multiple cards
    expect(screen.getAllByText('queued').length).toBeGreaterThanOrEqual(1)
  })
})
