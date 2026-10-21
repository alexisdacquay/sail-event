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

  it('shows events except new, with action buttons per status', async () => {
    render(<EventsPage />)

    await screen.findByText('React London Meetup')

    // accepted — has Remove from calendar
    expect(screen.getByText('React London Meetup')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Remove from calendar' })).toBeInTheDocument()
    // queued — has Add to calendar + Reject
    expect(screen.getByText('Jazz in the Park')).toBeInTheDocument()
    expect(screen.getByText('AWS re:Invent Watch Party')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Add to calendar' }).length).toBeGreaterThanOrEqual(1)
    // rejected — has Add to calendar
    expect(screen.getByText('Pottery Workshop for Beginners')).toBeInTheDocument()

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

  it('Remove from calendar changes card to show Add to calendar', async () => {
    render(<EventsPage />)

    await screen.findByText('React London Meetup')

    fireEvent.click(
      screen.getByRole('button', { name: 'Remove from calendar' }),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))

    // After removal the card becomes rejected — shows Add to calendar
    await waitFor(() => {
      expect(
        screen.queryByRole('button', { name: 'Remove from calendar' }),
      ).not.toBeInTheDocument()
    })
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
