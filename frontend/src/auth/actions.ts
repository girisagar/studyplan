import { api } from '../api/client'
import type { SessionResponse } from '../api/types'
import { clearCache } from '../offline/cache'
import { clearFiles } from '../offline/files'
import { clearOutbox } from '../offline/progress'
import { requestSync, resetSyncState } from '../offline/sync'
import { getSession, setSession } from './session'

/** Whose data the local database holds (user id), so another account's sign-in
 * on this device starts clean. */
const OWNER_KEY = 'studyplan.owner'

/** Remove everything stored for offline use: data, pending changes, files. */
export async function wipeLocalData() {
  await Promise.all([clearCache(), clearOutbox(), clearFiles()])
  resetSyncState()
  localStorage.removeItem(OWNER_KEY)
}

async function startSession(response: SessionResponse) {
  const owner = localStorage.getItem(OWNER_KEY)
  if (owner && owner !== String(response.user.id)) await wipeLocalData()
  localStorage.setItem(OWNER_KEY, String(response.user.id))
  resetSyncState() // "synced" should mean synced with this account's data
  setSession(response)
  void requestSync(true)
}

export async function login(username: string, password: string) {
  const response = await api<SessionResponse>('/auth/login', {
    method: 'POST',
    body: { username, password },
    auth: false,
  })
  await startSession(response)
}

export async function register(username: string, password1: string, password2: string) {
  const response = await api<SessionResponse>('/auth/register', {
    method: 'POST',
    body: { username, password1, password2 },
    auth: false,
  })
  await startSession(response)
}

/** Sign out: revoke the refresh token (best effort) and wipe local data. */
export async function logout() {
  const session = getSession()
  if (session && navigator.onLine) {
    try {
      await api('/auth/logout', {
        method: 'POST',
        body: { refresh: session.refresh },
        auth: false,
      })
    } catch {
      // Offline or already invalid: the token expires on its own.
    }
  }
  setSession(null)
  await wipeLocalData()
  void requestSync(true)
}
