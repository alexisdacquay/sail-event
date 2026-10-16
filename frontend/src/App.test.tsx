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
  fireEvent.click(screen.getByRole('button', { name: 'Login' }))
  await screen.findByText('Search Criteria')
}

describe('Auth', () => {
  it('shows login screen for unauthenticated visitor', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
  })

  it('navigates from login to register', () => {
    render(<App />)
    fireEvent.click(screen.getByText('Register'))
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Register' }),
    ).toBeInTheDocument()
  })

  it('register flow shows main page on success', async () => {
    render(<App />)
    fireEvent.click(screen.getByText('Register'))
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'newuser' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'pass' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))
    await screen.findByText('Search Criteria')
  })

  it('login flow shows main page on success', async () => {
    await loginAsTestUser()
    expect(screen.getByText('Search Criteria')).toBeInTheDocument()
  })

  it('logout returns to login screen', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }))
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument()
  })

  it('unauthenticated render shows no criteria editor', () => {
    render(<App />)
    expect(screen.queryByLabelText('Criteria')).not.toBeInTheDocument()
  })
})

describe('Criteria', () => {
  it('initial value equals mock canned criteria text', async () => {
    await loginAsTestUser()
    const textarea = screen.getByLabelText('Criteria')
    await waitFor(() => {
      expect(textarea).toHaveValue(
        'sailing regattas in the Mediterranean, July 2026',
      )
    })
  })

  it('save round-trips criteria text', async () => {
    await loginAsTestUser()
    const textarea = screen.getByLabelText('Criteria')
    fireEvent.change(textarea, {
      target: { value: 'Atlantic tall ship races' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save Criteria' }))
    await waitFor(() => {
      expect(textarea).toHaveValue('Atlantic tall ship races')
    })
  })
})

describe('Thresholds', () => {
  it('initial values equal mock canned thresholds', async () => {
    await loginAsTestUser()
    const lowerInput = screen.getByLabelText('Lower Threshold')
    const upperInput = screen.getByLabelText('Upper Threshold')
    await waitFor(() => {
      expect(lowerInput).toHaveValue(30)
      expect(upperInput).toHaveValue(70)
    })
  })

  it('equal thresholds shows error and saveThresholds is not called', async () => {
    const spy = vi.spyOn(mock, 'saveThresholds')
    await loginAsTestUser()
    const lowerInput = screen.getByLabelText('Lower Threshold')
    const upperInput = screen.getByLabelText('Upper Threshold')
    fireEvent.change(lowerInput, { target: { value: '50' } })
    fireEvent.change(upperInput, { target: { value: '50' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Thresholds' }))
    expect(
      screen.getByText('Lower threshold must be less than upper threshold'),
    ).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
    spy.mockRestore()
  })

  it('rejects lower >= upper with inline error', async () => {
    await loginAsTestUser()
    const lowerInput = screen.getByLabelText('Lower Threshold')
    const upperInput = screen.getByLabelText('Upper Threshold')
    fireEvent.change(lowerInput, { target: { value: '80' } })
    fireEvent.change(upperInput, { target: { value: '50' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Thresholds' }))
    expect(
      screen.getByText('Lower threshold must be less than upper threshold'),
    ).toBeInTheDocument()
  })

  it('save round-trips threshold values', async () => {
    await loginAsTestUser()
    const lowerInput = screen.getByLabelText('Lower Threshold')
    const upperInput = screen.getByLabelText('Upper Threshold')
    fireEvent.change(lowerInput, { target: { value: '20' } })
    fireEvent.change(upperInput, { target: { value: '90' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Thresholds' }))
    await waitFor(() => {
      expect(lowerInput).toHaveValue(20)
      expect(upperInput).toHaveValue(90)
    })
  })
})

describe('Search', () => {
  it('displays confirmation with event counts', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Search now' }))
    const result = await screen.findByTestId('search-result')
    expect(result).toHaveTextContent('12 events found')
    expect(result).toHaveTextContent('4 new')
  })
})

describe('Tab bar and queue count', () => {
  it('shows tabs with queue count and decrements on accept', async () => {
    await loginAsTestUser()

    // Tab bar shows all three tabs
    const nav = screen.getByRole('navigation', { name: 'Main navigation' })
    expect(nav).toHaveTextContent('Dashboard')
    expect(nav).toHaveTextContent('Events')
    expect(nav).toHaveTextContent('Queue')

    // Queue count equals mock's queued events (2)
    await waitFor(() => {
      expect(nav).toHaveTextContent('(2)')
    })

    // Navigate to Queue tab
    fireEvent.click(screen.getByRole('button', { name: /Queue/ }))

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
