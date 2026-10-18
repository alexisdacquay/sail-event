import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { EventsPage } from './EventsPage'
import * as mock from '@/services/mock'
import * as api from '@/services/api'

describe('EventsPage', () => {
  beforeEach(() => {
    mock._resetMockEvents()
    vi.restoreAllMocks()
  })

  it('shows events except new, with correct badges', async () => {
    render(<EventsPage />)

    await screen.findByText('React London Meetup')

    // accepted (auto)
    expect(screen.getByText('React London Meetup')).toBeInTheDocument()
    expect(screen.getByText('Auto-accepted')).toBeInTheDocument()
    // queued
    expect(screen.getByText('Jazz in the Park')).toBeInTheDocument()
    expect(screen.getByText('AWS re:Invent Watch Party')).toBeInTheDocument()
    expect(
      screen.getAllByText('To review').length,
    ).toBeGreaterThanOrEqual(1)
    // rejected (auto)
    expect(
      screen.getByText('Pottery Workshop for Beginners'),
    ).toBeInTheDocument()
    expect(screen.getByText('Auto-rejected')).toBeInTheDocument()

    // new events must be filtered out
    expect(
      screen.queryByText('TypeScript Conference 2026'),
    ).not.toBeInTheDocument()
  })

  it('shows Remove from calendar on accepted events', async () => {
    render(<EventsPage />)

    await screen.findByText('React London Meetup')

    expect(
      screen.getByRole('button', { name: 'Remove from calendar' }),
    ).toBeInTheDocument()
  })

  it('Remove from calendar flips badge to Rejected by you', async () => {
    render(<EventsPage />)

    await screen.findByText('React London Meetup')

    fireEvent.click(
      screen.getByRole('button', { name: 'Remove from calendar' }),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))

    const acceptedCard = screen.getByTestId('event-card-evt-1')
    await waitFor(() => {
      expect(acceptedCard).toHaveTextContent('Rejected by you')
    })
    expect(
      screen.queryByRole('button', { name: 'Remove from calendar' }),
    ).not.toBeInTheDocument()
  })

  it('shows empty state when no events', async () => {
    vi.spyOn(api, 'listEvents').mockResolvedValue([])

    render(<EventsPage />)

    await screen.findByText('No events yet.')
    expect(
      screen.getByText(
        /Write what you're looking for on the Home tab/,
      ),
    ).toBeInTheDocument()
  })
})
