import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import App from './App'
import * as mock from './services/mock'

beforeEach(() => {
  localStorage.clear()
  mock._resetMockEvents()
})

async function loginAsTestUser() {
  render(<App />)
  fireEvent.change(screen.getByLabelText('Username'), {
    target: { value: 'testuser' },
  })
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'pass123' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
  await screen.findByTestId('criteria-text')
}

describe('Auth', () => {
  it('shows login screen for unauthenticated visitor', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
  })

  it('navigates from login to register', () => {
    render(<App />)
    fireEvent.click(screen.getByText('Create one'))
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Create account' }),
    ).toBeInTheDocument()
  })

  it('register flow shows the Stream page on success', async () => {
    render(<App />)
    fireEvent.click(screen.getByText('Create one'))
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'newuser' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'pass' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await screen.findByTestId('search-box')
  })

  it('login flow shows the Stream page on success', async () => {
    await loginAsTestUser()
    expect(screen.getByTestId('search-box')).toBeInTheDocument()
  })

  it('logout returns to login screen', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('unauthenticated render shows no search box', () => {
    render(<App />)
    expect(screen.queryByTestId('search-box')).not.toBeInTheDocument()
  })
})

describe('Criteria', () => {
  it('initial value equals mock canned criteria text', async () => {
    await loginAsTestUser()
    expect(screen.getByTestId('criteria-text')).toHaveTextContent(
      'sailing regattas in the Mediterranean, July 2026',
    )
  })

  it('edit and save round-trips criteria text', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.change(screen.getByLabelText("What I'm looking for"), {
      target: { value: 'Atlantic tall ship races' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save criteria' }))
    await waitFor(() => {
      expect(screen.getByText('Saved.')).toBeInTheDocument()
    })
    expect(screen.getByTestId('criteria-text')).toHaveTextContent('Atlantic tall ship races')
    await mock.saveCriteria('sailing regattas in the Mediterranean, July 2026', 'UTC')
  })
})

describe('Thresholds', () => {
  it('initial values equal mock canned thresholds', async () => {
    await loginAsTestUser()
    const lowerInput = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upperInput = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    await waitFor(() => {
      expect(lowerInput).toHaveValue(30)
      expect(upperInput).toHaveValue(70)
    })
  })

  it('equal thresholds shows error and saveThresholds is not called', async () => {
    const spy = vi.spyOn(mock, 'saveThresholds')
    await loginAsTestUser()
    const lowerInput = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upperInput = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    fireEvent.change(lowerInput, { target: { value: '50' } })
    fireEvent.change(upperInput, { target: { value: '50' } })
    expect(
      screen.getByText(
        'The auto-accept line must be higher than the auto-reject line.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save scoring' })).toBeDisabled()
    expect(spy).not.toHaveBeenCalled()
    spy.mockRestore()
  })

  it('save round-trips threshold values', async () => {
    await loginAsTestUser()
    const lowerInput = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upperInput = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    fireEvent.change(lowerInput, { target: { value: '20' } })
    fireEvent.change(upperInput, { target: { value: '90' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save scoring' }))
    await waitFor(() => {
      expect(lowerInput).toHaveValue(20)
      expect(upperInput).toHaveValue(90)
    })
  })
})

describe('Search', () => {
  it('Search again runs and the queue count is fresh afterwards', async () => {
    await loginAsTestUser()
    const nav = screen.getByRole('navigation', { name: 'Main navigation' })
    const button = await screen.findByRole('button', { name: 'Search again' })
    fireEvent.click(button)
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
    await screen.findByRole('button', { name: 'Search again' })
    // Mock has 2 queued events
    await waitFor(() => {
      expect(nav).toHaveTextContent('(2)')
    })
  })

  it('disables Search again when the saved criteria are empty', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.change(screen.getByLabelText("What I'm looking for"), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save criteria' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Search again' })).toBeDisabled())
    await mock.saveCriteria('sailing regattas in the Mediterranean, July 2026', 'UTC')
  })
})

describe('Tab bar and queue count', () => {
  it('shows tabs with queue count and decrements on accept', async () => {
    await loginAsTestUser()

    const nav = screen.getByRole('navigation', { name: 'Main navigation' })
    expect(nav).toHaveTextContent('Stream')
    expect(nav).toHaveTextContent('All events')
    expect(nav).toHaveTextContent('To review')

    // Queue count equals mock's queued events (2)
    await waitFor(() => {
      expect(nav).toHaveTextContent('(2)')
    })

    // Navigate to To review tab
    fireEvent.click(within(nav).getByRole('button', { name: /To review/ }))

    // Wait for queued events to render
    await screen.findByText('Jazz in the Park')

    // Accept evt-2
    const card = screen.getByTestId('event-card-evt-2')
    const acceptButton = card.querySelector('button')!
    fireEvent.click(acceptButton)

    // Event leaves the queue
    await waitFor(() => {
      expect(screen.queryByText('Jazz in the Park')).not.toBeInTheDocument()
    })

    // Queue count decrements to 1
    await waitFor(() => {
      expect(nav).toHaveTextContent('(1)')
    })
  })
})
