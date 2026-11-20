import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { ApiError, errorMessage } from '../api/client'
import { login, register } from '../auth/actions'
import { useSession } from '../auth/session'
import { Page } from '../components/ui'
import { useOnline } from '../hooks/useOnline'

function useReturnTo() {
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from
  return from && from !== '/login' && from !== '/register' ? from : '/'
}

function OfflineNote() {
  return <p className="form-note">Signing in needs a connection. You're offline right now.</p>
}

export function LoginPage() {
  const session = useSession()
  const online = useOnline()
  const navigate = useNavigate()
  const returnTo = useReturnTo()
  const [username, setUsername] = useState(session?.user.username ?? '')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(username.trim(), password)
      navigate(returnTo, { replace: true })
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Page title="Sign in">
      <form className="card form" onSubmit={submit}>
        {session?.expired && (
          <p className="form-note">Your session expired. Sign in again to keep syncing.</p>
        )}
        {!online && <OfflineNote />}
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary btn-block" disabled={busy || !online}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="muted center">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </form>
    </Page>
  )
}

export function RegisterPage() {
  const online = useOnline()
  const navigate = useNavigate()
  const returnTo = useReturnTo()
  const [form, setForm] = useState({ username: '', password1: '', password2: '' })
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setErrors({})
    setError(null)
    try {
      await register(form.username.trim(), form.password1, form.password2)
      navigate(returnTo, { replace: true })
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) setErrors(e.fieldErrors)
      else setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const field = (name: keyof typeof form, label: string, type = 'text', autoComplete?: string) => (
    <label>
      {label}
      <input
        type={type}
        value={form[name]}
        onChange={(e) => setForm({ ...form, [name]: e.target.value })}
        autoComplete={autoComplete}
        autoCapitalize="none"
        aria-invalid={!!errors[name]}
        required
      />
      {errors[name]?.map((message) => (
        <span key={message} className="field-error">
          {message}
        </span>
      ))}
    </label>
  )

  return (
    <Page title="Create account">
      <form className="card form" onSubmit={submit}>
        {!online && <OfflineNote />}
        {field('username', 'Username', 'text', 'username')}
        {field('password1', 'Password', 'password', 'new-password')}
        {field('password2', 'Confirm password', 'password', 'new-password')}
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary btn-block" disabled={busy || !online}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
        <p className="muted center">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </Page>
  )
}
