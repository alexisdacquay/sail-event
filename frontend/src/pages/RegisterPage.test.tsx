import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'

vi.mock('@/services/api', async (importOriginal) => {
  const mod = await importOriginal<typeof import('@/services/api')>()
  return {
    ...mod,
    getConfig: () =>
      Promise.resolve({ registrationCodeRequired: true }),
  }
})

import { RegisterPage } from './RegisterPage'

describe('RegisterPage', () => {
  it('shows registration code input when getConfig says required', async () => {
    render(
      <AuthProvider>
        <RegisterPage onNavigateLogin={() => {}} />
      </AuthProvider>,
    )
    await waitFor(() => {
      expect(
        screen.getByLabelText('Invitation code'),
      ).toBeInTheDocument()
    })
  })
})
