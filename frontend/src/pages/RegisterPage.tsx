import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { register, getConfig } from '@/services/api'
import { useAuth } from '@/contexts/AuthContext'

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

  useEffect(() => {
    getConfig()
      .then((cfg) => setCodeRequired(cfg.registrationCodeRequired))
      .catch(() => {})  // on failure, treat as not required
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      const res = await register(
        username,
        password,
        codeRequired ? registrationCode : undefined,
      )
      setAuth(res)
    } catch {
      setError('Registration failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Register</CardTitle>
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
              />
            </div>
            {codeRequired && (
              <div className="flex flex-col gap-2">
                <Label htmlFor="registrationCode">Registration code</Label>
                <Input
                  id="registrationCode"
                  value={registrationCode}
                  onChange={(e) => setRegistrationCode(e.target.value)}
                  required
                />
              </div>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit">Register</Button>
            <p className="text-sm text-center">
              Already have an account?{' '}
              <button
                type="button"
                className="underline"
                onClick={onNavigateLogin}
              >
                Login
              </button>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
