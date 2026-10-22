import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import App from './App'
import * as mock from './services/mock'

beforeEach(() => {
  localStorage.clear()
  document.documentElement.classList.remove('dark')
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
    expect(screen.getByTestId('pitch')).toBeInTheDocument()
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

describe('Shell', () => {
  it('the Stream is the only page: no navigation, no To review or All events', async () => {
    await loginAsTestUser()
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
    expect(screen.queryByText('To review')).not.toBeInTheDocument()
    expect(screen.queryByText('All events')).not.toBeInTheDocument()
    expect(screen.getByTestId('calendar-url')).toBeInTheDocument()
    expect(screen.getByText('Scoring')).toBeInTheDocument()
  })

  it('theme switch in the header toggles the dark class and remembers it', async () => {
    await loginAsTestUser()
    fireEvent.click(screen.getByRole('button', { name: 'Switch to dark theme' }))
    expect(document.documentElement).toHaveClass('dark')
    expect(localStorage.getItem('sail-event-theme')).toBe('dark')
    fireEvent.click(screen.getByRole('button', { name: 'Switch to light theme' }))
    expect(document.documentElement).not.toHaveClass('dark')
  })
})

describe('Criteria', () => {
  it('initial value equals mock canned criteria text', async () => {
    await loginAsTestUser()
    await waitFor(() => expect(screen.getByTestId('criteria-text')).toHaveValue(
      'sailing regattas in the Mediterranean, July 2026',
    ))
  })

  it('typing in place and pressing Enter round-trips criteria text', async () => {
    await loginAsTestUser()
    const box = screen.getByLabelText("What I'm looking for")
    // wait for the saved text to load, or the edit is overwritten by it
    await waitFor(() => expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    fireEvent.change(box, { target: { value: 'Atlantic tall ship races' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    await waitFor(() => {
      expect(screen.getByText('Saved.')).toBeInTheDocument()
    })
    expect(screen.getByTestId('criteria-text')).toHaveValue('Atlantic tall ship races')
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
  it('Search again runs and the results show the pills', async () => {
    await loginAsTestUser()
    const button = await screen.findByRole('button', { name: 'Search again' })
    fireEvent.click(button)
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
    await screen.findByRole('button', { name: 'Search again' })
    // Mock has 2 queued events
    await waitFor(() => {
      expect(screen.getAllByText('Review')).toHaveLength(2)
    })
  })

  it('disables Search again when the saved criteria are empty', async () => {
    await loginAsTestUser()
    const box = screen.getByLabelText("What I'm looking for")
    await waitFor(() => expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    fireEvent.change(box, { target: { value: '' } })
    fireEvent.blur(box)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Search again' })).toBeDisabled())
    await mock.saveCriteria('sailing regattas in the Mediterranean, July 2026', 'UTC')
  })
})
