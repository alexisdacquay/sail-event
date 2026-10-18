import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { login } from '@/services/api'
import { useAuth } from '@/contexts/AuthContext'
import { SailMark } from '@/components/SailMark'

export function LoginPage({
  onNavigateRegister,
}: {
  onNavigateRegister: () => void
}) {
  const { setAuth } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const res = await login(username, password)
      setAuth(res)
    } catch (err: unknown) {
      const status = (err as { status?: number }).status
      if (status === 401) {
        setError('Wrong username or password.')
      } else if (status === 429) {
        setError('Too many attempts. Try again later.')
      } else {
        setError("Couldn't sign in. Try again.")
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center">
      <SailMark className="size-10 mb-3" aria-hidden="true" />
      <p className="font-heading text-[28px] font-bold tracking-tight text-center mb-6">Sail Event</p>
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle as="h2">Sign in</CardTitle>
        </CardHeader>
        <CardContent>
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
                autoComplete="current-password"
              />
            </div>
            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Signing in…' : 'Sign in'}
            </Button>
            <p className="text-sm text-center">
              No account?{' '}
              <button
                type="button"
                className="underline rounded-sm focus-visible:outline-2 focus-visible:outline-ring focus-visible:outline-offset-2"
                onClick={onNavigateRegister}
              >
                Create one
              </button>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
