import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { register, getConfig } from '@/services/api'
import { useAuth } from '@/contexts/AuthContext'
import { SailMark } from '@/components/SailMark'
import { PITCH } from './LoginPage'

export function RegisterPage({
  onNavigateLogin,
}: {
  onNavigateLogin: () => void
}) {
  const { setAuth } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [registrationCode, setRegistrationCode] = useState('')
  const [codeRequired, setCodeRequired] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    getConfig()
      .then((cfg) => setCodeRequired(cfg.registrationCodeRequired))
      .catch(() => {})  // on failure, treat as not required
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const res = await register(
        username,
        password,
        codeRequired ? registrationCode : undefined,
      )
      setAuth(res)
    } catch (err: unknown) {
      const status = (err as { status?: number }).status
      if (status === 409) {
        setError(
          "Couldn't create your account. That username may already be taken.",
        )
      } else if (status === 403) {
        setError("That invitation code isn't valid.")
      } else if (status === 429) {
        setError('Too many attempts. Try again later.')
      } else {
        setError("Couldn't create your account. Try again.")
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm flex flex-col items-center">
        <SailMark className="size-10 mb-3" aria-hidden="true" />
        <p className="font-heading text-[28px] font-bold tracking-tight text-center">Sail Event</p>
        <p className="text-sm text-muted-foreground text-center mt-2 mb-6" data-testid="pitch">
          {PITCH}
        </p>
        <div className="w-full rounded-xl border-2 border-ring/50 bg-card p-4 shadow-sm text-sm">
          <h2 className="font-heading text-lg font-bold mb-4">Create account</h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>
            {codeRequired && (
              <div className="flex flex-col gap-2">
                <Label htmlFor="invitationCode">Invitation code</Label>
                <Input
                  id="invitationCode"
                  value={registrationCode}
                  onChange={(e) => setRegistrationCode(e.target.value)}
                  required
                />
              </div>
            )}
            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Creating…' : 'Create account'}
            </Button>
            <p className="text-sm text-center">
              Already have an account?{' '}
              <button
                type="button"
                className="underline rounded-sm focus-visible:outline-2 focus-visible:outline-ring focus-visible:outline-offset-2"
                onClick={onNavigateLogin}
              >
                Sign in
              </button>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
