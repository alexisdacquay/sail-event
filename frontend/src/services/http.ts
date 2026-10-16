import type {
  AuthResponse,
  Criteria,
  Thresholds,
  SearchResult,
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

  if (res.status === 401) {
    localStorage.removeItem('sail-event-token')
    localStorage.removeItem('sail-event-username')
    window.location.reload()
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? res.statusText)
  }

  return res.json() as Promise<T>
}

export async function register(
  username: string,
  password: string,
): Promise<AuthResponse> {
  return request<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
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

export async function saveCriteria(text: string): Promise<Criteria> {
  return request<Criteria>('/api/criteria', {
    method: 'PUT',
    body: JSON.stringify({ text }),
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
