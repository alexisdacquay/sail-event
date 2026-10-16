import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import { describe, expect, it, beforeEach } from 'vitest'
import { QueuePage } from './QueuePage'
import * as mock from '@/services/mock'
import type { Event } from '@/services/api'

describe('QueuePage', () => {
  beforeEach(() => {
    mock._resetMockEvents()
  })

  it('shows only queued events', async () => {
    render(<QueuePage />)

    // Queued events should appear
    await screen.findByText('Jazz in the Park')
    expect(screen.getByText('AWS re:Invent Watch Party')).toBeInTheDocument()

    // Non-queued events should not appear
    expect(screen.queryByText('React London Meetup')).not.toBeInTheDocument()
    expect(
      screen.queryByText('Pottery Workshop for Beginners'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('TypeScript Conference 2026'),
    ).not.toBeInTheDocument()
  })

  it('Accept moves event to accepted and out of queue', async () => {
    render(<QueuePage />)

    await screen.findByText('Jazz in the Park')

    // Find the Accept button in the Jazz event card
    const jazzCard = screen.getByTestId('event-card-evt-2')
    const acceptButton = jazzCard.querySelector('button')!
    fireEvent.click(acceptButton)

    // The event should leave the queue
    await waitFor(() => {
      expect(screen.queryByText('Jazz in the Park')).not.toBeInTheDocument()
    })

    // Verify the mock was mutated
    const events = await mock.listEvents()
    const jazz = events.find((e: Event) => e.id === 'evt-2')
    expect(jazz?.status).toBe('accepted')
  })

  it('Reject moves event to rejected and out of queue', async () => {
    render(<QueuePage />)

    await screen.findByText('AWS re:Invent Watch Party')

    // Find the Reject button in the AWS event card
    const awsCard = screen.getByTestId('event-card-evt-3')
    const buttons = awsCard.querySelectorAll('button')
    // Reject is the second button
    const rejectButton = buttons[1]
    fireEvent.click(rejectButton)

    // The event should leave the queue
    await waitFor(() => {
      expect(
        screen.queryByText('AWS re:Invent Watch Party'),
      ).not.toBeInTheDocument()
    })

    // Verify the mock was mutated
    const events = await mock.listEvents()
    const aws = events.find((e: Event) => e.id === 'evt-3')
    expect(aws?.status).toBe('rejected')
  })

  it('rejected event stays out of queue across remounts', async () => {
    const { unmount } = render(<QueuePage />)

    await screen.findByText('Jazz in the Park')

    // Reject evt-2
    const card = screen.getByTestId('event-card-evt-2')
    const buttons = card.querySelectorAll('button')
    fireEvent.click(buttons[1]) // Reject

    await waitFor(() => {
      expect(screen.queryByText('Jazz in the Park')).not.toBeInTheDocument()
    })

    unmount()

    // Re-render a fresh QueuePage
    render(<QueuePage />)

    // evt-3 should still be queued
    await screen.findByText('AWS re:Invent Watch Party')

    // evt-2 must not reappear
    expect(screen.queryByText('Jazz in the Park')).not.toBeInTheDocument()

    // Verify at the data layer
    const queued = await mock.listEvents('queued')
    expect(queued.find((e: Event) => e.id === 'evt-2')).toBeUndefined()
  })
})
