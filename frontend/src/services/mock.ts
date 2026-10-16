import type { AuthResponse, Criteria, Thresholds, SearchResult } from './api'

let mockCriteria: Criteria = {
  text: 'sailing regattas in the Mediterranean, July 2026',
  updatedAt: '2026-01-15T10:00:00Z',
}

let mockThresholds: Thresholds = {
  lowerThreshold: 30,
  upperThreshold: 70,
}

export async function register(
  username: string,
  _password: string,
): Promise<AuthResponse> {
  return { token: 'mock-token-' + username, username }
}

export async function login(
  username: string,
  _password: string,
): Promise<AuthResponse> {
  return { token: 'mock-token-' + username, username }
}

export async function getCriteria(): Promise<Criteria> {
  return { ...mockCriteria }
}

export async function saveCriteria(text: string): Promise<Criteria> {
  mockCriteria = { text, updatedAt: new Date().toISOString() }
  return { ...mockCriteria }
}

export async function getThresholds(): Promise<Thresholds> {
  return { ...mockThresholds }
}

export async function saveThresholds(
  thresholds: Thresholds,
): Promise<Thresholds> {
  mockThresholds = { ...thresholds }
  return { ...mockThresholds }
}

export async function runSearch(): Promise<SearchResult> {
  return { runId: 'run-001', eventsFound: 12, eventsNew: 4 }
}
