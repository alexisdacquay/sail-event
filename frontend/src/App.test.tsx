import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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
  await screen.findByText("What I'm looking for")
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

  it('register flow shows main page on success', async () => {
    render(<App />)
    fireEvent.click(screen.getByText('Create one'))
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'newuser' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'pass' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await screen.findByText("What I'm looking for")
  })

  it('login flow shows main page on success', async () => {
    await loginAsTestUser()
    expect(screen.getByText("What I'm looking for")).toBeInTheDocument()
  })

  it('logout returns to login screen', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('unauthenticated render shows no criteria editor', () => {
    render(<App />)
    expect(
      screen.queryByLabelText("What I'm looking for"),
    ).not.toBeInTheDocument()
  })
})

describe('Criteria', () => {
  it('initial value equals mock canned criteria text', async () => {
    await loginAsTestUser()
    const textarea = screen.getByLabelText("What I'm looking for")
    await waitFor(() => {
      expect(textarea).toHaveValue(
        'sailing regattas in the Mediterranean, July 2026',
      )
    })
  })

  it('save round-trips criteria text', async () => {
    await loginAsTestUser()
    const textarea = screen.getByLabelText("What I'm looking for")
    fireEvent.change(textarea, {
      target: { value: 'Atlantic tall ship races' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save criteria' }))
    await waitFor(() => {
      expect(textarea).toHaveValue('Atlantic tall ship races')
    })
  })

  it('shows Saved. after successful save', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Save criteria' }))
    await waitFor(() => {
      expect(screen.getByText('Saved.')).toBeInTheDocument()
    })
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

  it('rejects lower >= upper with inline error', async () => {
    await loginAsTestUser()
    const lowerInput = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upperInput = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    fireEvent.change(lowerInput, { target: { value: '80' } })
    fireEvent.change(upperInput, { target: { value: '50' } })
    expect(
      screen.getByText(
        'The auto-accept line must be higher than the auto-reject line.',
      ),
    ).toBeInTheDocument()
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
  it('displays result with event counts and review button', async () => {
    await loginAsTestUser()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Search now' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    // Mock returns stageCounts, so we see the pipeline report line
    expect(result).toHaveTextContent(/6 queries → 31 results/)
    // Mock has 2 queued events — review button should appear
    expect(screen.getByRole('button', { name: /Review 2 events/ })).toBeInTheDocument()
  })

  it('saves criteria before searching (criteria Saved. appears)', async () => {
    await loginAsTestUser()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Search now' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    await waitFor(() => {
      expect(screen.getByText('Saved.')).toBeInTheDocument()
    })
  })

  it('disables Search now when criteria is empty', async () => {
    await loginAsTestUser()
    const textarea = screen.getByLabelText("What I'm looking for")
    fireEvent.change(textarea, { target: { value: '' } })
    expect(screen.getByRole('button', { name: 'Search now' })).toBeDisabled()
    expect(
      screen.getByText(
        "Write what you're looking for, then press Search now.",
      ),
    ).toBeInTheDocument()
  })
})

describe('Tab bar and queue count', () => {
  it('shows tabs with queue count and decrements on accept', async () => {
    await loginAsTestUser()

    const nav = screen.getByRole('navigation', { name: 'Main navigation' })
    expect(nav).toHaveTextContent('Home')
    expect(nav).toHaveTextContent('All events')
    expect(nav).toHaveTextContent('To review')

    // Queue count equals mock's queued events (2)
    await waitFor(() => {
      expect(nav).toHaveTextContent('(2)')
    })

    // Navigate to To review tab
    fireEvent.click(screen.getByRole('button', { name: /To review/ }))

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

  it('refreshes queue count after search without tab click', async () => {
    await loginAsTestUser()
    const nav = screen.getByRole('navigation', { name: 'Main navigation' })

    // Run a search - this calls refreshQueueCount via onSearchComplete.
    // The button stays disabled until the saved criteria have loaded, so wait for it.
    const searchButton = screen.getByRole('button', { name: 'Search now' })
    await waitFor(() => expect(searchButton).toBeEnabled())
    fireEvent.click(searchButton)
    await screen.findByTestId('search-result', {}, { timeout: 5000 })

    // Queue count should be fresh (2 queued in mock)
    await waitFor(() => {
      expect(nav).toHaveTextContent('(2)')
    })
  })
})
