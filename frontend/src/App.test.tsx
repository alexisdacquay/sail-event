import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

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
})

describe('Criteria', () => {
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
