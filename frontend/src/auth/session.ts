// The signed-in session (JWTs + user), kept in localStorage so the app opens
// signed in while offline. `expired` means the refresh token was rejected: local
// data stays readable, but syncing needs a new sign-in.
import { useSyncExternalStore } from 'react'
import type { TokenPair, User } from '../api/types'

export interface Session extends TokenPair {
  user: User
  expired?: boolean
}

const KEY = 'studyplan.session'
const listeners = new Set<() => void>()
let current: Session | null = read()

function read(): Session | null {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as Session) : null
  } catch {
    return null
  }
}

function write(next: Session | null) {
  current = next
  try {
    if (next) localStorage.setItem(KEY, JSON.stringify(next))
    else localStorage.removeItem(KEY)
  } catch {
    // Storage unavailable (private mode): the session lasts for this page only.
  }
  listeners.forEach((l) => l())
}

// Keep tabs in step (sign-in/out or token refresh in another tab).
window.addEventListener('storage', (event) => {
  if (event.key === KEY) {
    current = read()
    listeners.forEach((l) => l())
  }
})

export const getSession = () => current
export const setSession = (session: Session | null) => write(session)

export function updateTokens(tokens: TokenPair) {
  if (current) write({ ...current, ...tokens, expired: false })
}

export function updateUser(user: User) {
  if (current) write({ ...current, user })
}

export function markExpired() {
  if (current && !current.expired) write({ ...current, expired: true })
}

export function subscribeSession(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useSession() {
  return useSyncExternalStore(subscribeSession, getSession)
}
