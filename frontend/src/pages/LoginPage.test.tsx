import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { LoginPage, PITCH } from './LoginPage'

describe('LoginPage', () => {
  it('renders the pitch and the Sign in button', () => {
    render(
      <AuthProvider>
        <LoginPage onNavigateRegister={() => {}} />
      </AuthProvider>,
    )
    expect(screen.getByTestId('pitch')).toHaveTextContent(PITCH)
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })
})
