// Fetch wrapper for the Django API: JSON in/out, bearer auth, and one transparent
// token refresh on 401. Network failures throw NetworkError (the request never
// reached the server), so callers can tell "offline" from "rejected".
import { getSession, markExpired, updateTokens } from '../auth/session'
import type { TokenPair, ValidationErrorBody } from './types'

export const API_BASE = `${import.meta.env.VITE_API_URL ?? ''}/api`

export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(status: number, body: unknown) {
    super(describe(body) ?? `Request failed (${status})`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }

  /** Field -> messages, from a 422 validation response. */
  get fieldErrors(): Record<string, string[]> {
    const out: Record<string, string[]> = {}
    const detail = (this.body as ValidationErrorBody | null)?.detail
    if (Array.isArray(detail)) {
      for (const error of detail) {
        const field = String(error.loc[error.loc.length - 1] ?? '')
        ;(out[field] ??= []).push(error.msg.replace(/^Value error, /, ''))
      }
    }
    return out
  }
}

export class NetworkError extends Error {
  constructor() {
    super('You appear to be offline.')
    this.name = 'NetworkError'
  }
}

function describe(body: unknown): string | null {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e: { msg?: string }) => e.msg?.replace(/^Value error, /, '')).join(' ')
  }
  return null
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return 'Something went wrong.'
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  /** Send the access token (default true when signed in). */
  auth?: boolean
  signal?: AbortSignal
}

let refreshing: Promise<boolean> | null = null

/** Renew the token pair once, shared by concurrent callers. */
export function refreshTokens(): Promise<boolean> {
  refreshing ??= (async () => {
    const session = getSession()
    if (!session) return false
    try {
      const tokens = await send<TokenPair>('/auth/refresh', {
        method: 'POST',
        body: { refresh: session.refresh },
        auth: false,
      })
      updateTokens(tokens)
      return true
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) markExpired()
      if (error instanceof NetworkError) throw error
      return false
    } finally {
      refreshing = null
    }
  })()
  return refreshing
}

async function send<T>(path: string, options: RequestOptions): Promise<T> {
  const { method = 'GET', body, signal } = options
  const session = getSession()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  // An expired session's token would only earn a 401, even on public endpoints.
  if (options.auth !== false && session && !session.expired) {
    headers.Authorization = `Bearer ${session.access}`
  }
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if ((error as Error).name === 'AbortError') throw error
    throw new NetworkError()
  }
  if (response.status === 204) return undefined as T
  const data: unknown = response.headers.get('content-type')?.includes('json')
    ? await response.json().catch(() => null)
    : null
  if (!response.ok) throw new ApiError(response.status, data)
  return data as T
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  try {
    return await send<T>(path, options)
  } catch (error) {
    const canRetry =
      error instanceof ApiError &&
      error.status === 401 &&
      options.auth !== false &&
      getSession() !== null &&
      !getSession()?.expired
    if (canRetry && (await refreshTokens())) return send<T>(path, options)
    throw error
  }
}
