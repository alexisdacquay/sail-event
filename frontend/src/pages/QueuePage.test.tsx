import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { QueuePage } from './QueuePage'
import * as mock from '@/services/mock'
import type { Event } from '@/services/api'

describe('QueuePage', () => {
  beforeEach(() => {
    mock._resetMockEvents()
  })

  it('shows only queued events', async () => {
    render(<QueuePage />)

    await screen.findByText('Jazz in the Park')
    expect(screen.getByText('AWS re:Invent Watch Party')).toBeInTheDocument()

    expect(screen.queryByText('React London Meetup')).not.toBeInTheDocument()
    expect(
      screen.queryByText('Pottery Workshop for Beginners'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText('TypeScript Conference 2026'),
    ).not.toBeInTheDocument()
  })

  it('Accept moves event to accepted and shows undo', async () => {
    render(<QueuePage />)

    await screen.findByText('Jazz in the Park')

    const jazzCard = screen.getByTestId('event-card-evt-2')
    const acceptButton = jazzCard.querySelector('button')!
    await act(async () => { fireEvent.click(acceptButton) })

    // Undo bar should appear
    await waitFor(() => {
      expect(screen.getByText('Accepted.')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Undo' })).toBeInTheDocument()
    })

    // Mock state should reflect the accept
    const events = await mock.listEvents()
    const jazz = events.find((e: Event) => e.id === 'evt-2')
    expect(jazz?.status).toBe('accepted')
  })

  it('Reject moves event to rejected and shows undo', async () => {
    render(<QueuePage />)

    await screen.findByText('AWS re:Invent Watch Party')

    const awsCard = screen.getByTestId('event-card-evt-3')
    const buttons = awsCard.querySelectorAll('button')
    const rejectButton = buttons[1]
    await act(async () => { fireEvent.click(rejectButton) })

    // Undo bar should appear
    await waitFor(() => {
      expect(screen.getByText('Rejected.')).toBeInTheDocument()
    })

    const events = await mock.listEvents()
    const aws = events.find((e: Event) => e.id === 'evt-3')
    expect(aws?.status).toBe('rejected')
  })

  it('rejected event stays rejected in mock state', async () => {
    render(<QueuePage />)

    await screen.findByText('Jazz in the Park')

    const card = screen.getByTestId('event-card-evt-2')
    const buttons = card.querySelectorAll('button')
    await act(async () => { fireEvent.click(buttons[1]) }) // Reject

    // Verify mock state
    const queued = await mock.listEvents('queued')
    expect(queued.find((e: Event) => e.id === 'evt-2')).toBeUndefined()

    const all = await mock.listEvents()
    const jazz = all.find((e: Event) => e.id === 'evt-2')
    expect(jazz?.status).toBe('rejected')
  })

  it('disables both buttons while a decision is in flight', async () => {
    vi.spyOn(mock, 'decideEvent').mockImplementation(
      () => new Promise(() => {}),
    )

    render(<QueuePage />)
    await screen.findByText('Jazz in the Park')

    const card = screen.getByTestId('event-card-evt-2')
    fireEvent.click(card.querySelectorAll('button')[0]!) // Accept

    await waitFor(() => {
      const btns = card.querySelectorAll('button')
      expect(btns[0]).toBeDisabled()
      expect(btns[1]).toBeDisabled()
    })

    vi.restoreAllMocks()
  })

  it('renders To review heading', async () => {
    render(<QueuePage />)
    await screen.findByText('Jazz in the Park')
    expect(screen.getByRole('heading', { name: 'To review' })).toBeInTheDocument()
  })

  it('shows empty state when no queued events', async () => {
    // Decide both queued events so the queue is empty
    await mock.decideEvent('evt-2', 'accepted')
    await mock.decideEvent('evt-3', 'rejected')

    render(<QueuePage />)

    await screen.findByText('Nothing to decide right now.')
    expect(
      screen.getByText(/Events that clearly match go straight to your calendar/),
    ).toBeInTheDocument()
  })
})
