import type {
  AuthResponse,
  ConfigResponse,
  Criteria,
  Thresholds,
  SearchResult,
  LastRunResponse,
  Event,
  EventStatus,
} from './api'

const BASE = import.meta.env.VITE_API_URL as string

function token(): string | null {
  return localStorage.getItem('sail-event-token')
}

function authHeaders(): Record<string, string> {
  const t = token()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(init.headers as Record<string, string> | undefined),
    },
  })

  if (res.status === 401 && token()) {
    localStorage.removeItem('sail-event-token')
    localStorage.removeItem('sail-event-username')
    window.location.reload()
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    const err = new Error(body.detail ?? res.statusText) as Error & { status: number; retryAfter?: number }
    err.status = res.status
    if (res.status === 429) {
      const ra = res.headers.get('Retry-After')
      if (ra) err.retryAfter = parseInt(ra, 10)
    }
    throw err
  }

  return res.json() as Promise<T>
}

export async function getConfig(): Promise<ConfigResponse> {
  return request<ConfigResponse>('/api/config')
}

export async function register(
  username: string,
  password: string,
  registrationCode?: string,
): Promise<AuthResponse> {
  const payload: Record<string, string> = { username, password }
  if (registrationCode) payload.registrationCode = registrationCode
  return request<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function login(
  username: string,
  password: string,
): Promise<AuthResponse> {
  return request<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function getCriteria(): Promise<Criteria> {
  return request<Criteria>('/api/criteria')
}

export async function saveCriteria(text: string, timeZone?: string): Promise<Criteria> {
  return request<Criteria>('/api/criteria', {
    method: 'PUT',
    body: JSON.stringify({ text, timeZone }),
  })
}

export async function getThresholds(): Promise<Thresholds> {
  return request<Thresholds>('/api/thresholds')
}

export async function saveThresholds(
  thresholds: Thresholds,
): Promise<Thresholds> {
  return request<Thresholds>('/api/thresholds', {
    method: 'PUT',
    body: JSON.stringify(thresholds),
  })
}

export async function runSearch(): Promise<SearchResult> {
  return request<SearchResult>('/api/search', { method: 'POST' })
}

export async function listEvents(status?: EventStatus): Promise<Event[]> {
  const qs = status ? `?status=${status}` : ''
  return request<Event[]>(`/api/events${qs}`)
}

export async function decideEvent(
  id: string,
  decision: 'accepted' | 'rejected',
): Promise<Event> {
  return request<Event>(`/api/events/${id}/decision`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  })
}

export async function getLastRun(): Promise<LastRunResponse> {
  return request<LastRunResponse>('/api/search/last-run')
}

export async function deleteAllEvents(): Promise<{ deleted: number }> {
  return request<{ deleted: number }>('/api/events', { method: 'DELETE' })
}

export async function getCalendarUrl(): Promise<{ url: string }> {
  return request<{ url: string }>('/api/calendar-url')
}

export async function rotateCalendarUrl(): Promise<{ url: string }> {
  return request<{ url: string }>('/api/calendar/rotate', { method: 'POST' })
}
