import { act, render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import App from './App'
import * as mock from './services/mock'
import * as api from './services/api'

beforeEach(async () => {
  await mock.saveThresholds({ lowerThreshold: 30, upperThreshold: 70 })
  localStorage.clear()
  document.documentElement.classList.remove('dark')
  mock._resetMockEvents()
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
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

  it('typing then Enter saves the text and runs the search in one action', async () => {
    await loginAsTestUser()
    const box = screen.getByLabelText('What are you looking for?')
    // wait for the saved text to load, or the edit is overwritten by it
    await waitFor(() => expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    fireEvent.change(box, { target: { value: 'Atlantic tall ship races' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(screen.getByRole('button', { name: 'Searching…' })).toBeDisabled()
    await screen.findByRole('button', { name: 'Search again' })
    expect(screen.getByTestId('criteria-text')).toHaveValue('Atlantic tall ship races')
    expect((await mock.getCriteria()).text).toBe('Atlantic tall ship races')
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
    const spy = vi.spyOn(api, 'saveThresholds')
    await loginAsTestUser()
    const lowerInput = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upperInput = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    await waitFor(() => expect(lowerInput).toHaveValue(30))
    vi.useFakeTimers()
    fireEvent.change(lowerInput, { target: { value: '50' } })
    fireEvent.change(upperInput, { target: { value: '50' } })
    expect(
      screen.getByText(
        'The auto-accept line must be higher than the auto-reject line.',
      ),
    ).toBeInTheDocument()
    await act(() => vi.advanceTimersByTimeAsync(1000))
    expect(spy).not.toHaveBeenCalled()
    spy.mockRestore()
  })

  it('auto-save round-trips threshold values after signing in again', async () => {
    await loginAsTestUser()
    const lowerInput = screen.getByRole('spinbutton', { name: 'Auto-reject below' })
    const upperInput = screen.getByRole('spinbutton', { name: 'Auto-accept above' })
    await waitFor(() => expect(lowerInput).toHaveValue(30))
    fireEvent.change(lowerInput, { target: { value: '20' } })
    fireEvent.change(upperInput, { target: { value: '90' } })
    await screen.findByText('Saved.')
    expect(await mock.getThresholds()).toEqual({ lowerThreshold: 20, upperThreshold: 90 })
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => {
      expect(screen.getByRole('spinbutton', { name: 'Auto-reject below' })).toHaveValue(20)
      expect(screen.getByRole('spinbutton', { name: 'Auto-accept above' })).toHaveValue(90)
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

  it('disables Search again while the box is empty', async () => {
    await loginAsTestUser()
    const box = screen.getByLabelText('What are you looking for?')
    await waitFor(() => expect(box).toHaveValue('sailing regattas in the Mediterranean, July 2026'))
    fireEvent.change(box, { target: { value: '' } })
    expect(screen.getByRole('button', { name: 'Search again' })).toBeDisabled()
  })
})
